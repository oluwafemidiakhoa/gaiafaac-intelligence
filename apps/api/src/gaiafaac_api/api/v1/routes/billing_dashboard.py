"""Billing dashboard projections from canonical subscription and API-key records."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select

from gaiafaac_api.customer_auth import CurrentCustomer, DatabaseSession
from gaiafaac_api.database.models import ApiKey, ApiRequest
from gaiafaac_api.database.subscription_models import Invoice
from gaiafaac_api.services.account import current_plan

router = APIRouter(prefix="/billing", tags=["billing dashboard"])


class UsageMetric(BaseModel):
    event_type: str
    count: int
    limit: int | None = None


class BillingDashboard(BaseModel):
    organization_id: str
    current_tier: str
    subscription_status: str | None
    expires_at: datetime | None = None
    monthly_usage: list[UsageMetric]
    total_api_calls: int
    total_exports: int | None = None
    overage_charges: int | None = None
    usage_statement: str


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


def _month_start(now: datetime) -> datetime:
    return datetime(now.year, now.month, 1, tzinfo=UTC)


def _canonical_api_calls(session: DatabaseSession, organization_id) -> int:
    now = datetime.now(UTC)
    return int(
        session.scalar(
            select(func.count(ApiRequest.id))
            .join(ApiKey, ApiKey.id == ApiRequest.api_key_id)
            .where(
                ApiKey.organization_id == organization_id,
                ApiRequest.created_at >= _month_start(now),
            )
        )
        or 0
    )


@router.get("/dashboard", response_model=BillingDashboard)
def get_billing_dashboard(
    session: DatabaseSession,
    user: CurrentCustomer,
) -> BillingDashboard:
    """Return canonical entitlement and auditable API-key usage only."""
    if not user.organization_id:
        raise HTTPException(status_code=401, detail="Organization not found.")

    plan_code, entitlements, subscription = current_plan(session, user.organization_id)
    api_calls = _canonical_api_calls(session, user.organization_id)
    api_limit = entitlements.api_rate_limit_per_day if entitlements.api_access else 0

    metrics = [
        UsageMetric(
            event_type="api_calls_this_month",
            count=api_calls,
            limit=None,
        )
    ]

    return BillingDashboard(
        organization_id=str(user.organization_id),
        current_tier=plan_code,
        subscription_status=subscription.status.value if subscription else None,
        expires_at=subscription.current_period_end if subscription else None,
        monthly_usage=metrics,
        total_api_calls=api_calls,
        total_exports=None,
        overage_charges=None,
        usage_statement=(
            "API usage is counted from canonical API-key request records. "
            f"The current API plan rate boundary is {api_limit} requests/day when API access is enabled. "
            "Legacy header-derived usage and modeled overage charges are not reported."
        ),
    )


@router.get("/invoices", response_model=list[InvoiceDetail])
def get_invoices(
    session: DatabaseSession,
    user: CurrentCustomer,
) -> list[InvoiceDetail]:
    """Return retained legacy invoice records for historical compatibility."""
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
    """Return canonical API request usage rather than legacy subscription logs."""
    if not user.organization_id:
        raise HTTPException(status_code=401, detail="Organization not found.")

    api_calls = _canonical_api_calls(session, user.organization_id)
    return {
        "organization_id": str(user.organization_id),
        "period": _month_start(datetime.now(UTC)).strftime("%Y-%m"),
        "total_events": api_calls,
        "by_type": {"api_call": api_calls},
        "statement": "Usage is sourced from canonical API request records only.",
    }
