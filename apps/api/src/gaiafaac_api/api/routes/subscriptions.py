"""Subscription and billing API routes"""

from __future__ import annotations

import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import requests
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.session import get_session
from gaiafaac_api.database.subscription_models import (
    OrganizationSubscription,
    PaymentRecord,
    SubscriptionTier,
)
from gaiafaac_api.subscription_schemas import (
    ApiKeyCreated,
    ApiKeyCreateRequest,
    ApiUsageMetrics,
    BillingDashboardResponse,
    DecisionPacketRequest,
    DecisionPacketResponse,
    PaymentHistoryItem,
    PaystackCheckoutResponse,
    PricingPageResponse,
    SubscriptionCheckoutRequest,
    SubscriptionStatus as SubscriptionStatusSchema,
    SubscriptionTierInfo,
)

router = APIRouter(prefix="/api/v1/billing", tags=["billing"])

# Paystack configuration (from environment)
PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY", "")
PAYSTACK_API_URL = "https://api.paystack.co"


def get_organization_id_from_request(request) -> str:
    """Extract organization ID from authenticated request"""
    # This would come from request context (e.g., from JWT token)
    # For now, stub it
    return request.state.organization_id if hasattr(request, "state") else None


@router.get("/pricing", response_model=PricingPageResponse)
async def get_pricing_tiers(session: Session = Depends(get_session)):
    """Get available subscription tiers and pricing"""
    tiers = (
        session.execute(select(SubscriptionTier).order_by(SubscriptionTier.price_naira))
        .scalars()
        .all()
    )

    tier_infos = [
        SubscriptionTierInfo(
            id=tier.id,
            name=tier.name,
            price_naira=tier.price_naira,
            requests_per_month=tier.requests_per_month,
            exports_per_month=tier.exports_per_month,
            features=tier.features.split(","),
            description=tier.description,
        )
        for tier in tiers
    ]

    return PricingPageResponse(tiers=tier_infos)


@router.post("/checkout", response_model=PaystackCheckoutResponse)
async def initiate_checkout(
    request: SubscriptionCheckoutRequest,
    session: Session = Depends(get_session),
):
    """Initiate subscription checkout with Paystack"""
    if not PAYSTACK_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Payment processing not configured",
        )

    # Get tier
    tier = session.execute(
        select(SubscriptionTier).where(SubscriptionTier.name == request.tier_name.title())
    ).scalar_one_or_none()

    if not tier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription tier '{request.tier_name}' not found",
        )

    # Skip payment for free tier
    if tier.price_naira == 0:
        # Auto-approve free tier
        return PaystackCheckoutResponse(
            checkout_url="https://gaiafaac.app/dashboard",
            transaction_id="free-tier",
            amount_naira=0,
            tier_name=tier.name,
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )

    # Create Paystack transaction
    transaction_id = str(uuid4())
    paystack_payload = {
        "email": request.email,
        "amount": tier.price_naira * 100,  # Paystack uses kobo (1 naira = 100 kobo)
        "metadata": {
            "transaction_id": transaction_id,
            "tier_name": tier.name,
            "organization_name": request.organization_name or "Individual",
            "full_name": request.full_name,
        },
    }

    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            f"{PAYSTACK_API_URL}/transaction/initialize",
            json=paystack_payload,
            headers=headers,
            timeout=10,
        )
        response.raise_for_status()
        paystack_response = response.json()

        if not paystack_response.get("status"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Paystack initialization failed",
            )

        return PaystackCheckoutResponse(
            checkout_url=paystack_response["data"]["authorization_url"],
            transaction_id=transaction_id,
            amount_naira=tier.price_naira,
            tier_name=tier.name,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )

    except requests.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Payment gateway error: {str(e)}",
        )


@router.get("/status", response_model=SubscriptionStatusSchema | None)
async def get_subscription_status(
    organization_id: str,
    session: Session = Depends(get_session),
):
    """Get current subscription status for organization"""
    subscription = session.execute(
        select(OrganizationSubscription).where(
            OrganizationSubscription.organization_id == organization_id
        )
    ).scalar_one_or_none()

    if not subscription:
        return None

    # Get tier details for limits
    tier = session.execute(
        select(SubscriptionTier).where(SubscriptionTier.id == subscription.tier_id)
    ).scalar_one()

    days_until_renewal = (subscription.expires_at - datetime.now(timezone.utc)).days

    return SubscriptionStatusSchema(
        organization_id=subscription.organization_id,
        tier_name=subscription.tier_name,
        price_naira=tier.price_naira,
        status=subscription.status,
        started_at=subscription.started_at,
        expires_at=subscription.expires_at,
        api_requests_used=subscription.api_requests_used,
        api_requests_limit=tier.requests_per_month,
        exports_used=subscription.exports_used,
        exports_limit=tier.exports_per_month,
        days_until_renewal=max(0, days_until_renewal),
    )


@router.get("/dashboard", response_model=BillingDashboardResponse)
async def get_billing_dashboard(
    organization_id: str,
    session: Session = Depends(get_session),
):
    """Get complete billing dashboard for organization"""
    subscription = session.execute(
        select(OrganizationSubscription).where(
            OrganizationSubscription.organization_id == organization_id
        )
    ).scalar_one_or_none()

    # Get payment history
    payments = (
        session.execute(
            select(PaymentRecord)
            .where(PaymentRecord.organization_id == organization_id)
            .order_by(PaymentRecord.created_at.desc())
            .limit(12)
        )
        .scalars()
        .all()
    )

    payment_items = [
        PaymentHistoryItem(
            id=p.id,
            amount_naira=p.amount_naira,
            status=p.status,
            invoice_number=p.invoice_number,
            created_at=p.created_at,
            completed_at=p.completed_at,
        )
        for p in payments
    ]

    # Calculate totals
    total_paid = sum(Decimal(str(p.amount_naira)) for p in payments if p.status == "success")

    next_payment = None
    if subscription and subscription.is_active():
        next_payment = subscription.expires_at

    return BillingDashboardResponse(
        subscription=(
            SubscriptionStatusSchema.model_validate(subscription) if subscription else None
        ),
        payment_history=payment_items,
        next_payment_date=next_payment,
        total_paid_naira=total_paid,
    )


@router.post("/api-keys", response_model=ApiKeyCreated)
async def create_api_key(
    request: ApiKeyCreateRequest,
    organization_id: str,
    session: Session = Depends(get_session),
):
    """Create new API key for programmatic access"""
    # Verify organization has active subscription
    subscription = session.execute(
        select(OrganizationSubscription).where(
            OrganizationSubscription.organization_id == organization_id
        )
    ).scalar_one_or_none()

    if not subscription or not subscription.is_active():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Active subscription required for API access",
        )

    # Generate API key
    raw_key = f"gaia_sk_{secrets.token_urlsafe(32)}"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    key_prefix = raw_key[:16]  # gaia_sk_XXXXXXXX

    # Store in database (simplified - would need actual API key table)
    # session.add(ApiKey(...))
    # session.commit()

    return ApiKeyCreated(
        id=uuid4(),
        name=request.name,
        key_prefix=key_prefix,
        api_key=raw_key,  # Shown only once!
        created_at=datetime.now(timezone.utc),
    )


@router.get("/usage", response_model=ApiUsageMetrics)
async def get_api_usage(
    organization_id: str,
    session: Session = Depends(get_session),
):
    """Get current API usage metrics"""
    subscription = session.execute(
        select(OrganizationSubscription).where(
            OrganizationSubscription.organization_id == organization_id
        )
    ).scalar_one_or_none()

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription",
        )

    tier = session.execute(
        select(SubscriptionTier).where(SubscriptionTier.id == subscription.tier_id)
    ).scalar_one()

    # Check if monthly reset needed
    now = datetime.now(timezone.utc)
    if (now - subscription.last_reset_at).days >= 30:
        subscription.reset_monthly_usage()
        session.commit()

    reset_date = subscription.last_reset_at + timedelta(days=30)

    return ApiUsageMetrics(
        current_month_requests=subscription.api_requests_used,
        current_month_limit=tier.requests_per_month,
        requests_remaining=max(0, tier.requests_per_month - subscription.api_requests_used),
        reset_date=reset_date,
        current_month_exports=subscription.exports_used,
        current_month_export_limit=tier.exports_per_month,
        exports_remaining=max(0, tier.exports_per_month - subscription.exports_used),
    )


@router.post("/decision-packets", response_model=DecisionPacketResponse)
async def generate_decision_packet(
    request: DecisionPacketRequest,
    organization_id: str,
    session: Session = Depends(get_session),
):
    """Generate a Decision Packet PDF export"""
    subscription = session.execute(
        select(OrganizationSubscription).where(
            OrganizationSubscription.organization_id == organization_id
        )
    ).scalar_one_or_none()

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Subscription required for Decision Packets",
        )

    # Check export limit
    if subscription.exports_used >= subscription.tier.exports_per_month:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Monthly export limit reached",
        )

    # TODO: Generate actual PDF with Fiscal State/Proof
    # For now, return mock response
    packet_id = uuid4()

    return DecisionPacketResponse(
        packet_id=packet_id,
        download_url=f"https://gaiafaac.app/api/v1/decision-packets/{packet_id}/download",
        size_bytes=2_500_000,  # ~2.5MB typical
        generated_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )
