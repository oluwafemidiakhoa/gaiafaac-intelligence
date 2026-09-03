"""Billing dashboard endpoints for customer self-service"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from gaiafaac_api.customer_auth import CurrentCustomer, DatabaseSession
from gaiafaac_api.database.subscription_models import (
    Invoice,
    OrganizationSubscription,
    SubscriptionTier,
    UsageLog,
)
from gaiafaac_api.services.billing import BillingService

router = APIRouter(prefix="/billing", tags=["billing dashboard"])


class UsageMetric(BaseModel):
    event_type: str
    count: int
    limit: int | None = None


class BillingDashboard(BaseModel):
    organization_id: str
    current_tier: str
    subscription_status: str
    expires_at: datetime | None = None
    monthly_usage: list[UsageMetric]
    total_api_calls: int
    total_exports: int
    overage_charges: int = 0


class InvoiceDetail(BaseModel):
    invoice_id: str
    invoice_number: str
    period_start: datetime
    period_end: datetime
    subtotal: str
    tax: str
    total: str
    status: str
    sent_at: datetime | None = None
    paid_date: datetime | None = None


@router.get("/dashboard", response_model=BillingDashboard)
def get_billing_dashboard(
    session: DatabaseSession,
    user: CurrentCustomer,
) -> BillingDashboard:
    """Get customer billing dashboard with usage metrics"""
    if not user.organization_id:
        raise HTTPException(status_code=401, detail="Organization not found.")

    subscription = session.scalar(
        select(OrganizationSubscription).where(
            OrganizationSubscription.organization_id == user.organization_id
        )
    )

    if not subscription:
        raise HTTPException(status_code=404, detail="No subscription found.")

    tier = session.scalar(
        select(SubscriptionTier).where(SubscriptionTier.id == subscription.tier_id)
    )
    if not tier:
        raise HTTPException(status_code=404, detail="Subscription tier not found.")

    billing_service = BillingService(session)
    limits = billing_service.check_usage_limits(user.organization_id, subscription, tier)

    metrics = [
        UsageMetric(
            event_type="api_calls",
            count=limits["api_calls"]["used"],
            limit=limits["api_calls"]["limit"],
        ),
        UsageMetric(
            event_type="exports",
            count=limits["exports"]["used"],
            limit=limits["exports"]["limit"],
        ),
    ]

    return BillingDashboard(
        organization_id=str(user.organization_id),
        current_tier=tier.name,
        subscription_status=subscription.status,
        expires_at=subscription.expires_at,
        monthly_usage=metrics,
        total_api_calls=limits["api_calls"]["used"],
        total_exports=limits["exports"]["used"],
        overage_charges=int(
            billing_service.calculate_overage_charges(
                limits["api_calls"]["overage"],
                limits["exports"]["overage"],
            )
        ),
    )


@router.get("/invoices", response_model=list[InvoiceDetail])
def get_invoices(
    session: DatabaseSession,
    user: CurrentCustomer,
) -> list[InvoiceDetail]:
    """Get customer invoices"""
    if not user.organization_id:
        raise HTTPException(status_code=401, detail="Organization not found.")

    invoices = session.scalars(
        select(Invoice)
        .where(Invoice.organization_id == user.organization_id)
        .order_by(Invoice.created_at.desc())
    ).all()

    return [
        InvoiceDetail(
            invoice_id=str(invoice.id),
            invoice_number=invoice.invoice_number,
            period_start=invoice.period_start,
            period_end=invoice.period_end,
            subtotal=f"₦{invoice.subtotal_naira:,.2f}",
            tax=f"₦{invoice.tax_naira:,.2f}",
            total=f"₦{invoice.total_naira:,.2f}",
            status=invoice.status,
            sent_at=invoice.sent_at,
            paid_date=invoice.paid_date,
        )
        for invoice in invoices
    ]


@router.get("/usage")
def get_usage_details(
    session: DatabaseSession,
    user: CurrentCustomer,
) -> dict:
    """Get detailed usage breakdown by event type"""
    if not user.organization_id:
        raise HTTPException(status_code=401, detail="Organization not found.")

    logs = session.scalars(
        select(UsageLog).where(UsageLog.organization_id == user.organization_id)
    ).all()

    usage_by_type = {}
    for log in logs:
        usage_by_type[log.event_type] = usage_by_type.get(log.event_type, 0) + 1

    return {
        "organization_id": str(user.organization_id),
        "total_events": len(logs),
        "by_type": usage_by_type,
    }
