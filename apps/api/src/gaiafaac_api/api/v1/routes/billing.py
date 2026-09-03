from __future__ import annotations

import hashlib
import hmac
import json
import uuid
from datetime import UTC, datetime, timedelta
from urllib.error import HTTPError, URLError
from urllib.request import Request as UrlRequest
from urllib.request import urlopen

import stripe
from fastapi import APIRouter, Header, HTTPException, Request, Response, status
from sqlalchemy import select

from gaiafaac_api.account_schemas import CheckoutRequest, RedirectResponse
from gaiafaac_api.config import get_settings
from gaiafaac_api.customer_auth import CurrentCustomer, DatabaseSession
from gaiafaac_api.database.enums import SubscriptionStatus
from gaiafaac_api.database.models import Subscription
from gaiafaac_api.services.account import active_subscription, membership_for

router = APIRouter(prefix="/billing", tags=["customer billing"])

_PAYSTACK_API_URL = "https://api.paystack.co"
_STATUS_MAP = {
    "trialing": SubscriptionStatus.TRIALING,
    "active": SubscriptionStatus.ACTIVE,
    "past_due": SubscriptionStatus.PAST_DUE,
    "canceled": SubscriptionStatus.CANCELED,
    "unpaid": SubscriptionStatus.PAST_DUE,
    "incomplete": SubscriptionStatus.PAST_DUE,
    "incomplete_expired": SubscriptionStatus.EXPIRED,
    "paused": SubscriptionStatus.PAST_DUE,
}


def _stripe_ready():
    settings = get_settings()
    if not settings.stripe_secret_key:
        raise HTTPException(status_code=503, detail="Self-service billing is not configured.")
    stripe.api_key = settings.stripe_secret_key
    return settings


def _stripe_price_id(settings, plan_code: str) -> str:
    prices = {
        "analyst": settings.stripe_price_analyst,
        "team": settings.stripe_price_team,
        "api": settings.stripe_price_api,
    }
    value = prices.get(plan_code, "")
    if not value:
        raise HTTPException(
            status_code=503, detail=f"Billing price for {plan_code} is not configured."
        )
    return value


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


def _as_id(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return getattr(value, "id", None)


def _timestamp(value) -> datetime | None:
    if value is None:
        return None
    try:
        return datetime.fromtimestamp(int(value), tz=UTC)
    except (TypeError, ValueError, OSError):
        return None


def _object_get(obj, name: str, default=None):
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _sync_stripe_subscription(
    session: DatabaseSession,
    stripe_subscription,
    *,
    organization_id: uuid.UUID | None = None,
    plan_code: str | None = None,
) -> Subscription | None:
    external_subscription_id = _as_id(stripe_subscription)
    if external_subscription_id is None:
        return None
    metadata = _object_get(stripe_subscription, "metadata", {}) or {}
    org_text = metadata.get("organization_id") if hasattr(metadata, "get") else None
    plan = plan_code or (metadata.get("plan_code") if hasattr(metadata, "get") else None)
    if organization_id is None and org_text:
        try:
            organization_id = uuid.UUID(str(org_text))
        except ValueError:
            organization_id = None
    row = session.scalar(
        select(Subscription).where(
            Subscription.external_subscription_id == external_subscription_id
        )
    )
    if row is None:
        if organization_id is None or not plan:
            return None
        row = Subscription(
            organization_id=organization_id,
            status=SubscriptionStatus.TRIALING,
            plan_code=str(plan),
            external_subscription_id=external_subscription_id,
        )
        session.add(row)
    stripe_status = str(_object_get(stripe_subscription, "status", "active"))
    row.status = _STATUS_MAP.get(stripe_status, SubscriptionStatus.PAST_DUE)
    if plan:
        row.plan_code = str(plan)
    customer_id = _as_id(_object_get(stripe_subscription, "customer"))
    if customer_id:
        row.external_customer_id = customer_id
    row.current_period_start = _timestamp(_object_get(stripe_subscription, "current_period_start"))
    row.current_period_end = _timestamp(_object_get(stripe_subscription, "current_period_end"))
    session.commit()
    return row


def _initialize_paystack_checkout(
    *,
    email: str,
    organization_id: uuid.UUID,
    plan_code: str,
) -> RedirectResponse:
    settings = get_settings()
    if not settings.paystack_secret_key:
        raise HTTPException(status_code=503, detail="Paystack billing is not configured.")

    reference = f"gfi-{organization_id.hex[:12]}-{uuid.uuid4().hex[:16]}"
    body = json.dumps(
        {
            "email": email,
            "amount": _paystack_price_naira(settings, plan_code) * 100,
            "reference": reference,
            "callback_url": f"{settings.customer_app_url.rstrip('/')}/account?checkout=return",
            "metadata": {
                "organization_id": str(organization_id),
                "plan_code": plan_code,
                "billing_period_days": 30,
                "gaia_reference": reference,
            },
        }
    ).encode("utf-8")
    request = UrlRequest(
        f"{_PAYSTACK_API_URL}/transaction/initialize",
        data=body,
        headers={
            "Authorization": f"Bearer {settings.paystack_secret_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=12) as response:  # noqa: S310 - fixed trusted host
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as error:
        raise HTTPException(
            status_code=502, detail="Payment gateway is temporarily unavailable."
        ) from error

    authorization_url = (payload.get("data") or {}).get("authorization_url")
    if not payload.get("status") or not authorization_url:
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
            detail="An active subscription already exists. Manage or renew it from your account.",
        )

    if settings.paystack_secret_key:
        return _initialize_paystack_checkout(
            email=user.email,
            organization_id=user.organization_id,
            plan_code=payload.plan_code,
        )

    settings = _stripe_ready()
    price_id = _stripe_price_id(settings, payload.plan_code)
    checkout = stripe.checkout.Session.create(
        mode="subscription",
        customer_email=user.email,
        client_reference_id=str(user.organization_id),
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=f"{settings.customer_app_url.rstrip('/')}/account?checkout=success",
        cancel_url=f"{settings.customer_app_url.rstrip('/')}/pricing?checkout=cancelled",
        metadata={
            "organization_id": str(user.organization_id),
            "plan_code": payload.plan_code,
        },
        subscription_data={
            "metadata": {
                "organization_id": str(user.organization_id),
                "plan_code": payload.plan_code,
            }
        },
        allow_promotion_codes=True,
    )
    if not checkout.url:
        raise HTTPException(
            status_code=502, detail="Billing provider did not return a checkout URL."
        )
    return RedirectResponse(url=checkout.url)


@router.post("/portal", response_model=RedirectResponse)
def create_billing_portal(
    session: DatabaseSession,
    user: CurrentCustomer,
) -> RedirectResponse:
    settings = get_settings()
    if user.organization_id is None:
        raise HTTPException(status_code=409, detail="Customer organization is not configured.")
    subscription = active_subscription(session, user.organization_id)
    if subscription is None:
        raise HTTPException(status_code=404, detail="No active subscription was found.")

    if subscription.external_subscription_id and subscription.external_subscription_id.startswith(
        "gfi-"
    ):
        return RedirectResponse(
            url=f"{settings.customer_app_url.rstrip('/')}/account?billing=paystack"
        )

    settings = _stripe_ready()
    if not subscription.external_customer_id:
        raise HTTPException(status_code=404, detail="No active billing customer was found.")
    portal = stripe.billing_portal.Session.create(
        customer=subscription.external_customer_id,
        return_url=f"{settings.customer_app_url.rstrip('/')}/account",
    )
    return RedirectResponse(url=portal.url)


@router.post("/stripe-webhook", status_code=status.HTTP_204_NO_CONTENT)
async def stripe_webhook(
    request: Request,
    session: DatabaseSession,
    stripe_signature: str | None = Header(default=None, alias="Stripe-Signature"),
) -> Response:
    settings = get_settings()
    if not settings.stripe_webhook_secret or not settings.stripe_secret_key:
        raise HTTPException(status_code=503, detail="Stripe webhook is not configured.")
    payload = await request.body()
    try:
        event = stripe.Webhook.construct_event(
            payload,
            stripe_signature or "",
            settings.stripe_webhook_secret,
        )
    except (ValueError, stripe.error.SignatureVerificationError) as error:
        raise HTTPException(status_code=400, detail="Invalid Stripe webhook.") from error

    event_type = event["type"]
    data_object = event["data"]["object"]
    if event_type == "checkout.session.completed":
        metadata = _object_get(data_object, "metadata", {}) or {}
        org_text = metadata.get("organization_id") if hasattr(metadata, "get") else None
        plan_code = metadata.get("plan_code") if hasattr(metadata, "get") else None
        subscription_id = _as_id(_object_get(data_object, "subscription"))
        if org_text and plan_code and subscription_id:
            try:
                organization_id = uuid.UUID(str(org_text))
            except ValueError:
                organization_id = None
            if organization_id is not None:
                stripe.api_key = settings.stripe_secret_key
                stripe_subscription = stripe.Subscription.retrieve(subscription_id)
                _sync_stripe_subscription(
                    session,
                    stripe_subscription,
                    organization_id=organization_id,
                    plan_code=str(plan_code),
                )
    elif event_type in {
        "customer.subscription.created",
        "customer.subscription.updated",
        "customer.subscription.deleted",
    }:
        _sync_stripe_subscription(session, data_object)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _verify_paystack_webhook(signature: str, body: bytes, secret: str) -> bool:
    """Verify Paystack's HMAC-SHA512 signature over the exact request body."""
    computed = hmac.new(secret.encode("utf-8"), body, hashlib.sha512).hexdigest()
    return hmac.compare_digest(computed, signature)


def _activate_paystack_subscription(session: DatabaseSession, data: dict) -> None:
    metadata = data.get("metadata") or {}
    organization_id_text = metadata.get("organization_id")
    plan_code = str(metadata.get("plan_code") or "").lower()
    reference = str(data.get("reference") or metadata.get("gaia_reference") or "")
    if plan_code not in {"analyst", "team", "api"} or not organization_id_text or not reference:
        return
    try:
        organization_id = uuid.UUID(str(organization_id_text))
    except ValueError:
        return

    now = datetime.now(UTC)
    row = session.scalar(
        select(Subscription).where(Subscription.external_subscription_id == reference)
    )
    if row is None:
        row = Subscription(
            organization_id=organization_id,
            status=SubscriptionStatus.ACTIVE,
            plan_code=plan_code,
            external_subscription_id=reference,
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
        )
        session.add(row)
    else:
        row.organization_id = organization_id
        row.status = SubscriptionStatus.ACTIVE
        row.plan_code = plan_code
        row.current_period_start = now
        row.current_period_end = now + timedelta(days=30)
    session.commit()


@router.post("/paystack-webhook", status_code=status.HTTP_204_NO_CONTENT)
async def paystack_webhook(
    request: Request,
    session: DatabaseSession,
    paystack_signature: str | None = Header(default=None, alias="x-paystack-signature"),
) -> Response:
    settings = get_settings()
    if not settings.paystack_secret_key:
        raise HTTPException(status_code=503, detail="Paystack webhook is not configured.")

    payload = await request.body()
    if not paystack_signature or not _verify_paystack_webhook(
        paystack_signature, payload, settings.paystack_secret_key
    ):
        raise HTTPException(status_code=400, detail="Invalid Paystack webhook signature.")

    try:
        event = json.loads(payload)
    except json.JSONDecodeError as error:
        raise HTTPException(status_code=400, detail="Invalid JSON in Paystack webhook.") from error

    if event.get("event") == "charge.success":
        _activate_paystack_subscription(session, event.get("data") or {})

    return Response(status_code=status.HTTP_204_NO_CONTENT)
