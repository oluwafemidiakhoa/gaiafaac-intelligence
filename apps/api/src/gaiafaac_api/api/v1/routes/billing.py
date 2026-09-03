from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime, timedelta

import stripe
from fastapi import APIRouter, Header, HTTPException, Request, Response, status
from pydantic import BaseModel
from sqlalchemy import select

from gaiafaac_api.account_schemas import CheckoutRequest, RedirectResponse
from gaiafaac_api.config import get_settings
from gaiafaac_api.customer_auth import CurrentCustomer, DatabaseSession
from gaiafaac_api.database.enums import SubscriptionStatus
from gaiafaac_api.database.models import Subscription
from gaiafaac_api.database.subscription_models import (
    OrganizationSubscription,
    SubscriptionTier,
    TierName,
)
from gaiafaac_api.services.account import active_subscription, membership_for
from gaiafaac_api.services.billing import BillingService

router = APIRouter(prefix="/billing", tags=["customer billing"])

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


def _price_id(settings, plan_code: str) -> str:
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


def _sync_subscription(
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


@router.post("/checkout", response_model=RedirectResponse)
def create_checkout(
    payload: CheckoutRequest,
    session: DatabaseSession,
    user: CurrentCustomer,
) -> RedirectResponse:
    settings = _stripe_ready()
    if user.organization_id is None or membership_for(session, user) is None:
        raise HTTPException(status_code=409, detail="Customer organization is not configured.")
    if active_subscription(session, user.organization_id) is not None:
        raise HTTPException(
            status_code=409,
            detail="An active subscription already exists. Use billing management to change it.",
        )
    price_id = _price_id(settings, payload.plan_code)
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
    settings = _stripe_ready()
    if user.organization_id is None:
        raise HTTPException(status_code=409, detail="Customer organization is not configured.")
    subscription = active_subscription(session, user.organization_id)
    if subscription is None or not subscription.external_customer_id:
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
                _sync_subscription(
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
        _sync_subscription(session, data_object)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


class PaystackWebhookData(BaseModel):
    reference: str
    customer: dict | None = None
    authorization: dict | None = None
    subscription: str | None = None


class PaystackWebhookEvent(BaseModel):
    event: str
    data: PaystackWebhookData


def _verify_paystack_webhook(signature: str, body: bytes, secret: str) -> bool:
    """Verify Paystack webhook signature"""
    hash_obj = hashlib.sha512(body + secret.encode())
    computed_signature = hash_obj.hexdigest()
    return computed_signature == signature


@router.post("/paystack-webhook", status_code=status.HTTP_204_NO_CONTENT)
async def paystack_webhook(
    request: Request,
    session: DatabaseSession,
    paystack_signature: str | None = Header(default=None, alias="x-paystack-signature"),
) -> Response:
    """Handle Paystack payment confirmations and subscription events"""
    settings = get_settings()
    if not settings.paystack_secret_key:
        raise HTTPException(status_code=503, detail="Paystack webhook is not configured.")

    payload = await request.body()
    if not paystack_signature or not _verify_paystack_webhook(
        paystack_signature, payload, settings.paystack_secret_key
    ):
        raise HTTPException(status_code=400, detail="Invalid Paystack webhook signature.")

    try:
        import json

        event = json.loads(payload)
    except (ValueError, json.JSONDecodeError) as error:
        raise HTTPException(status_code=400, detail="Invalid JSON in Paystack webhook.") from error

    event_type = event.get("event")
    data = event.get("data", {})

    if event_type == "charge.success":
        metadata = data.get("metadata", {})
        organization_id_str = metadata.get("organization_id")
        plan_code = metadata.get("plan_code")

        if organization_id_str and plan_code:
            try:
                organization_id = uuid.UUID(str(organization_id_str))
            except ValueError:
                return Response(status_code=status.HTTP_204_NO_CONTENT)

            billing_service = BillingService(session)

            tier_name_map = {
                "free": TierName.FREE,
                "professional": TierName.PROFESSIONAL,
                "enterprise": TierName.ENTERPRISE,
            }

            tier_name = tier_name_map.get(str(plan_code).lower())
            if not tier_name:
                return Response(status_code=status.HTTP_204_NO_CONTENT)

            tier = session.scalar(
                select(SubscriptionTier).where(SubscriptionTier.name == tier_name.value)
            )
            if not tier:
                return Response(status_code=status.HTTP_204_NO_CONTENT)

            existing_sub = session.scalar(
                select(OrganizationSubscription).where(
                    OrganizationSubscription.organization_id == organization_id
                )
            )

            if existing_sub:
                existing_sub.status = "active"
                existing_sub.expires_at = datetime.now(UTC) + timedelta(days=30)
                existing_sub.renewed_at = datetime.now(UTC)
                session.commit()
            else:
                auth_code = data.get("authorization", {}).get("authorization_code")
                subscription = OrganizationSubscription(
                    organization_id=organization_id,
                    tier_id=tier.id,
                    tier_name=tier.name,
                    status="active",
                    paystack_subscription_id=data.get("reference"),
                    paystack_authorization_code=auth_code,
                    expires_at=datetime.now(UTC) + timedelta(days=30),
                )
                session.add(subscription)
                session.commit()

                billing_service.create_billing_event(
                    organization_id=organization_id,
                    subscription_id=subscription.id,
                    event_type="subscription_start",
                    amount_naira=tier.price_naira,
                    description=f"{tier.name} subscription activated",
                )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
