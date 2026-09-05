from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request as UrlRequest
from urllib.request import urlopen

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from gaiafaac_api.commercial_schemas import (
    OneTimePurchaseCheckoutRequest,
    OneTimePurchaseCheckoutResponse,
    OneTimePurchaseResponse,
)
from gaiafaac_api.config import get_settings
from gaiafaac_api.customer_auth import CurrentCustomer, DatabaseSession
from gaiafaac_api.database.commercial_models import OneTimePurchase
from gaiafaac_api.services.account import membership_for
from gaiafaac_api.services.commercial_events import record_commercial_event_once
from gaiafaac_api.services.product_catalog import ProductBillingMode, product_by_code

router = APIRouter(prefix="/billing/one-time", tags=["customer billing"])
_PAYSTACK_API_URL = "https://api.paystack.co"


def _configured_product_price(product_code: str) -> tuple[str, int]:
    product = product_by_code(product_code)
    if product is None or product.billing_mode != ProductBillingMode.ONE_TIME:
        raise HTTPException(status_code=422, detail="Unsupported one-time product.")
    if not product.price_naira or product.price_naira <= 0:
        raise HTTPException(
            status_code=503,
            detail=(
                f"Checkout for {product.label} is not enabled because an approved "
                "production price has not been configured."
            ),
        )
    return product.label, int(product.price_naira)


def _initialize_paystack_transaction(
    *,
    email: str,
    reference: str,
    amount_naira: int,
    metadata: dict,
) -> str:
    settings = get_settings()
    if not settings.paystack_secret_key:
        raise HTTPException(status_code=503, detail="Paystack billing is not configured.")

    body = json.dumps(
        {
            "email": email,
            "amount": amount_naira * 100,
            "reference": reference,
            "callback_url": (
                f"{settings.customer_app_url.rstrip('/')}/account/billing"
                f"?purchase=return&reference={quote(reference, safe='')}"
            ),
            "metadata": metadata,
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
    return str(authorization_url)


def _verify_paystack_transaction(reference: str) -> dict:
    settings = get_settings()
    if not settings.paystack_secret_key:
        raise HTTPException(status_code=503, detail="Paystack billing is not configured.")
    request = UrlRequest(
        f"{_PAYSTACK_API_URL}/transaction/verify/{quote(reference, safe='')}",
        headers={"Authorization": f"Bearer {settings.paystack_secret_key}"},
        method="GET",
    )
    try:
        with urlopen(request, timeout=12) as response:  # noqa: S310 - fixed trusted host
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as error:
        raise HTTPException(
            status_code=502, detail="Payment verification is temporarily unavailable."
        ) from error

    data = payload.get("data") or {}
    if not payload.get("status") or data.get("status") != "success":
        raise HTTPException(status_code=409, detail="Payment has not been confirmed by Paystack.")
    return data


def _serialize_purchase(row: OneTimePurchase) -> OneTimePurchaseResponse:
    return OneTimePurchaseResponse(
        id=row.id,
        organization_id=row.organization_id,
        product_code=row.product_code,
        provider=row.provider,
        provider_reference=row.provider_reference,
        amount_naira=str(row.amount_naira),
        currency=row.currency,
        status=row.status,
        fulfillment_status=row.fulfillment_status,
        fulfillment_reference=row.fulfillment_reference,
        completed_at=row.completed_at,
        fulfilled_at=row.fulfilled_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.post("/checkout", response_model=OneTimePurchaseCheckoutResponse)
def create_one_time_checkout(
    payload: OneTimePurchaseCheckoutRequest,
    session: DatabaseSession,
    user: CurrentCustomer,
) -> OneTimePurchaseCheckoutResponse:
    if user.organization_id is None or membership_for(session, user) is None:
        raise HTTPException(status_code=409, detail="Customer organization is not configured.")

    product_label, amount_naira = _configured_product_price(payload.product_code)
    serialized_context = json.dumps(payload.context, sort_keys=True, default=str)
    if len(serialized_context.encode("utf-8")) > 8_000:
        raise HTTPException(status_code=422, detail="Purchase context is too large.")

    purchase_id = uuid.uuid4()
    reference = f"gfi-order-{purchase_id.hex}"
    purchase = OneTimePurchase(
        id=purchase_id,
        organization_id=user.organization_id,
        user_id=user.id,
        product_code=payload.product_code,
        provider="paystack",
        provider_reference=reference,
        amount_naira=Decimal(amount_naira),
        currency="NGN",
        status="pending",
        fulfillment_status="pending",
        purchase_metadata=dict(payload.context),
    )
    session.add(purchase)
    session.commit()
    session.refresh(purchase)

    metadata = {
        "purchase_mode": "one_time",
        "purchase_id": str(purchase.id),
        "organization_id": str(user.organization_id),
        "product_code": payload.product_code,
        "product_label": product_label,
        "gaia_reference": reference,
    }
    try:
        authorization_url = _initialize_paystack_transaction(
            email=user.email,
            reference=reference,
            amount_naira=amount_naira,
            metadata=metadata,
        )
    except HTTPException:
        purchase.status = "checkout_failed"
        session.commit()
        raise

    record_commercial_event_once(
        session,
        event_name="one_time_checkout_started",
        organization_id=user.organization_id,
        user_id=user.id,
        subject_type="one_time_purchase",
        subject_id=str(purchase.id),
        metadata={
            "product_code": payload.product_code,
            "amount_naira": str(purchase.amount_naira),
            "provider": "paystack",
        },
    )
    return OneTimePurchaseCheckoutResponse(
        purchase=_serialize_purchase(purchase),
        url=authorization_url,
    )


@router.post("/paystack-verify", response_model=OneTimePurchaseResponse)
def verify_one_time_purchase(
    reference: str,
    session: DatabaseSession,
    user: CurrentCustomer,
) -> OneTimePurchaseResponse:
    if user.organization_id is None:
        raise HTTPException(status_code=409, detail="Customer organization is not configured.")

    purchase = session.scalar(
        select(OneTimePurchase).where(
            OneTimePurchase.provider == "paystack",
            OneTimePurchase.provider_reference == reference,
            OneTimePurchase.organization_id == user.organization_id,
        )
    )
    if purchase is None:
        raise HTTPException(status_code=404, detail="One-time purchase was not found.")
    if purchase.status == "success":
        return _serialize_purchase(purchase)

    data = _verify_paystack_transaction(reference)
    metadata = data.get("metadata") or {}
    if str(data.get("reference") or "") != reference:
        raise HTTPException(status_code=409, detail="Payment reference mismatch.")
    if str(metadata.get("purchase_mode") or "") != "one_time":
        raise HTTPException(status_code=409, detail="Payment is not a Gaia one-time purchase.")
    if str(metadata.get("purchase_id") or "") != str(purchase.id):
        raise HTTPException(status_code=403, detail="Payment does not belong to this purchase.")
    if str(metadata.get("organization_id") or "") != str(user.organization_id):
        raise HTTPException(status_code=403, detail="Payment does not belong to this organization.")
    if str(metadata.get("product_code") or "") != purchase.product_code:
        raise HTTPException(
            status_code=409, detail="Purchased product does not match the order ledger."
        )

    _label, configured_amount = _configured_product_price(purchase.product_code)
    try:
        paid_amount_naira = Decimal(str(data.get("amount"))) / Decimal("100")
    except (TypeError, ValueError, ArithmeticError) as error:
        raise HTTPException(status_code=409, detail="Payment amount is invalid.") from error
    if paid_amount_naira != purchase.amount_naira or paid_amount_naira != Decimal(
        configured_amount
    ):
        raise HTTPException(
            status_code=409, detail="Payment amount does not match the configured product price."
        )

    purchase.status = "success"
    purchase.completed_at = purchase.completed_at or datetime.now(UTC)
    session.commit()
    session.refresh(purchase)

    record_commercial_event_once(
        session,
        event_name="one_time_purchase_completed",
        organization_id=user.organization_id,
        user_id=user.id,
        subject_type="one_time_purchase",
        subject_id=str(purchase.id),
        metadata={
            "product_code": purchase.product_code,
            "amount_naira": str(purchase.amount_naira),
            "provider": purchase.provider,
        },
    )
    return _serialize_purchase(purchase)


@router.get("/purchases", response_model=list[OneTimePurchaseResponse])
def list_one_time_purchases(
    session: DatabaseSession,
    user: CurrentCustomer,
) -> list[OneTimePurchaseResponse]:
    if user.organization_id is None or membership_for(session, user) is None:
        raise HTTPException(status_code=409, detail="Customer organization is not configured.")
    rows = session.scalars(
        select(OneTimePurchase)
        .where(OneTimePurchase.organization_id == user.organization_id)
        .order_by(OneTimePurchase.created_at.desc())
    ).all()
    return [_serialize_purchase(row) for row in rows]
