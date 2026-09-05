from __future__ import annotations

import json
import logging
import uuid
from urllib.error import HTTPError, URLError
from urllib.request import Request as UrlRequest
from urllib.request import urlopen

from fastapi import APIRouter, HTTPException

from gaiafaac_api.account_schemas import CheckoutRequest, RedirectResponse
from gaiafaac_api.config import get_settings
from gaiafaac_api.customer_auth import CurrentCustomer, DatabaseSession
from gaiafaac_api.services.account import active_subscription, membership_for
from gaiafaac_api.services.commercial_events import record_commercial_event

router = APIRouter(prefix="/billing", tags=["customer billing"])
logger = logging.getLogger(__name__)
_PAYSTACK_API_URL = "https://api.paystack.co"


def _paystack_price_naira(settings, plan_code: str) -> int:
    prices = {
        "analyst": settings.paystack_price_analyst,
        "team": settings.paystack_price_team,
        "api": settings.paystack_price_api,
    }
    value = prices.get(plan_code)
    if value is None:
        raise HTTPException(status_code=422, detail="Unsupported billing plan.")
    return value


def _provider_message(error: HTTPError) -> str:
    try:
        raw = error.read().decode("utf-8", errors="replace")
        payload = json.loads(raw)
        message = str(payload.get("message") or "provider rejected request")
    except (OSError, ValueError, TypeError, AttributeError):
        message = "provider rejected request"
    return message[:240]


def _initialize_paystack_checkout(
    *,
    email: str,
    organization_id: uuid.UUID,
    plan_code: str,
) -> RedirectResponse:
    settings = get_settings()
    secret = settings.paystack_secret_key.strip()
    if not secret:
        raise HTTPException(status_code=503, detail="Paystack billing is not configured.")

    reference = f"gfi-{organization_id.hex[:12]}-{uuid.uuid4().hex[:16]}"
    metadata = {
        "organization_id": str(organization_id),
        "plan_code": plan_code,
        "billing_period_days": 30,
        "gaia_reference": reference,
    }
    body = json.dumps(
        {
            "email": email,
            "amount": str(_paystack_price_naira(settings, plan_code) * 100),
            "reference": reference,
            "callback_url": f"{settings.customer_app_url.rstrip('/')}/account/billing?checkout=return",
            "metadata": json.dumps(metadata, separators=(",", ":")),
        }
    ).encode("utf-8")
    request = UrlRequest(
        f"{_PAYSTACK_API_URL}/transaction/initialize",
        data=body,
        headers={
            "Authorization": f"Bearer {secret}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "GaiaFiscalIntelligence/1.0",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=12) as response:  # noqa: S310 - fixed trusted host
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        logger.warning(
            "Paystack initialize rejected status=%s message=%s",
            error.code,
            _provider_message(error),
        )
        raise HTTPException(
            status_code=502, detail="Payment gateway is temporarily unavailable."
        ) from error
    except (URLError, TimeoutError, json.JSONDecodeError) as error:
        logger.warning("Paystack initialize transport failure type=%s", type(error).__name__)
        raise HTTPException(
            status_code=502, detail="Payment gateway is temporarily unavailable."
        ) from error

    authorization_url = (payload.get("data") or {}).get("authorization_url")
    if not payload.get("status") or not authorization_url:
        logger.warning("Paystack initialize returned no authorization URL")
        raise HTTPException(status_code=502, detail="Paystack did not return a checkout URL.")
    return RedirectResponse(url=str(authorization_url))


@router.post("/checkout", response_model=RedirectResponse)
def create_checkout(
    payload: CheckoutRequest,
    session: DatabaseSession,
    user: CurrentCustomer,
) -> RedirectResponse:
    settings = get_settings()
    if user.organization_id is None or membership_for(session, user) is None:
        raise HTTPException(status_code=409, detail="Customer organization is not configured.")
    if active_subscription(session, user.organization_id) is not None:
        raise HTTPException(
            status_code=409,
            detail="An active subscription already exists. Use renewal from your account.",
        )
    if not settings.paystack_secret_key.strip():
        raise HTTPException(status_code=503, detail="Paystack billing is not configured.")

    redirect = _initialize_paystack_checkout(
        email=user.email,
        organization_id=user.organization_id,
        plan_code=payload.plan_code,
    )
    record_commercial_event(
        session,
        event_name="checkout_started",
        organization_id=user.organization_id,
        user_id=user.id,
        subject_type="organization",
        subject_id=str(user.organization_id),
        metadata={"plan_code": payload.plan_code, "provider": "paystack"},
    )
    return redirect
