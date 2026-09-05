from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from gaiafaac_api.config import get_settings
from gaiafaac_api.database.commercial_models import CommercialEvent, OneTimePurchase, PilotLead
from gaiafaac_api.database.customer_models import CustomerWatchlist, OrganizationWatchlist
from gaiafaac_api.database.enums import SubscriptionStatus
from gaiafaac_api.database.evidence_room_models import EvidenceRoom, FiscalReceipt
from gaiafaac_api.database.models import ApiRequest, Subscription, User
from gaiafaac_api.database.subscription_models import PaymentRecord
from gaiafaac_api.database.watch_contract_models import FiscalWatchContract


def record_commercial_event(
    session: Session,
    *,
    event_name: str,
    organization_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
    subject_type: str | None = None,
    subject_id: str | None = None,
    metadata: dict | None = None,
    commit: bool = True,
) -> CommercialEvent:
    """Persist a server-side commercial event without IP, device, or fingerprint data."""

    row = CommercialEvent(
        organization_id=organization_id,
        user_id=user_id,
        event_name=event_name,
        subject_type=subject_type,
        subject_id=subject_id,
        source="server",
        event_metadata=dict(metadata or {}),
        occurred_at=datetime.now(UTC),
    )
    session.add(row)
    if commit:
        session.commit()
        session.refresh(row)
    return row


def record_commercial_event_once(
    session: Session,
    *,
    event_name: str,
    subject_type: str,
    subject_id: str,
    organization_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
    metadata: dict | None = None,
    commit: bool = True,
) -> CommercialEvent:
    """Record an idempotent server event for a stable commercial subject."""

    existing = session.scalar(
        select(CommercialEvent).where(
            CommercialEvent.event_name == event_name,
            CommercialEvent.subject_type == subject_type,
            CommercialEvent.subject_id == subject_id,
        )
    )
    if existing is not None:
        return existing
    return record_commercial_event(
        session,
        event_name=event_name,
        organization_id=organization_id,
        user_id=user_id,
        subject_type=subject_type,
        subject_id=subject_id,
        metadata=metadata,
        commit=commit,
    )


def _count(session: Session, model, *where) -> int:
    query = select(func.count()).select_from(model)
    if where:
        query = query.where(*where)
    return int(session.scalar(query) or 0)


def commercial_analytics(session: Session) -> dict:
    """Return database-backed commercial metrics only; no modeled/demo KPIs."""

    lead_rows = session.execute(
        select(PilotLead.status, func.count(PilotLead.id)).group_by(PilotLead.status)
    ).all()
    lead_plan_rows = session.execute(
        select(PilotLead.plan_interest, func.count(PilotLead.id)).group_by(PilotLead.plan_interest)
    ).all()

    successful_payment_count, successful_payment_revenue = session.execute(
        select(
            func.count(PaymentRecord.id),
            func.coalesce(func.sum(PaymentRecord.amount_naira), Decimal("0")),
        ).where(PaymentRecord.status == "success")
    ).one()
    failed_payment_count = _count(session, PaymentRecord, PaymentRecord.status == "failed")
    one_time_purchase_count, one_time_purchase_revenue = session.execute(
        select(
            func.count(OneTimePurchase.id),
            func.coalesce(func.sum(OneTimePurchase.amount_naira), Decimal("0")),
        ).where(OneTimePurchase.status == "success")
    ).one()

    now = datetime.now(UTC)
    active_subscription_rows = session.execute(
        select(Subscription.plan_code, func.count(func.distinct(Subscription.organization_id)))
        .where(
            Subscription.status == SubscriptionStatus.ACTIVE,
            or_(Subscription.current_period_end.is_(None), Subscription.current_period_end > now),
        )
        .group_by(Subscription.plan_code)
    ).all()

    since = now - timedelta(days=30)
    event_rows = session.execute(
        select(CommercialEvent.event_name, func.count(CommercialEvent.id))
        .where(CommercialEvent.occurred_at >= since)
        .group_by(CommercialEvent.event_name)
    ).all()

    leads_by_status = {str(name): int(count) for name, count in lead_rows}
    leads_by_plan = {str(name): int(count) for name, count in lead_plan_rows}
    active_subscriptions_by_plan = {
        str(name): int(count) for name, count in active_subscription_rows
    }
    events_last_30_days = {str(name): int(count) for name, count in event_rows}

    settings = get_settings()
    configured_prices = {
        "analyst": settings.paystack_price_analyst,
        "team": settings.paystack_price_team,
        "api": settings.paystack_price_api,
    }
    configured_mrr_naira = sum(
        configured_prices.get(plan, 0) * count
        for plan, count in active_subscriptions_by_plan.items()
    )

    leads_total = sum(leads_by_status.values())
    won_leads = leads_by_status.get("won", 0)
    won_lead_conversion_rate_pct = (
        round((won_leads / leads_total) * 100, 2) if leads_total else None
    )
    expired_or_canceled = _count(
        session,
        Subscription,
        or_(
            Subscription.status.in_([SubscriptionStatus.CANCELED, SubscriptionStatus.EXPIRED]),
            Subscription.current_period_end <= now,
        ),
    )

    return {
        "generated_at": now,
        "signups_total": _count(session, User),
        "active_users_total": _count(session, User, User.is_active.is_(True)),
        "leads_total": leads_total,
        "leads_by_status": leads_by_status,
        "leads_by_plan": leads_by_plan,
        "won_lead_conversion_rate_pct": won_lead_conversion_rate_pct,
        "active_subscriptions_total": sum(active_subscriptions_by_plan.values()),
        "active_subscriptions_by_plan": active_subscriptions_by_plan,
        "configured_mrr_naira": str(configured_mrr_naira),
        "successful_payment_count": int(successful_payment_count or 0),
        "successful_payment_revenue_naira": str(successful_payment_revenue or Decimal("0")),
        "failed_payment_count": failed_payment_count,
        "expired_or_canceled_subscriptions": expired_or_canceled,
        "one_time_purchases": int(one_time_purchase_count or 0),
        "one_time_purchase_revenue_naira": str(one_time_purchase_revenue or Decimal("0")),
        "one_time_purchase_note": (
            "Counts only persisted one_time_purchases with status=success; quote requests and pending checkouts are excluded."
        ),
        "decision_rooms_total": _count(session, EvidenceRoom),
        "fiscal_receipts_total": _count(session, FiscalReceipt),
        "watchlists_total": _count(session, CustomerWatchlist)
        + _count(session, OrganizationWatchlist),
        "watch_contracts_total": _count(session, FiscalWatchContract),
        "api_requests_total": _count(session, ApiRequest),
        "exports_total": events_last_30_days.get("export_generated", 0),
        "events_last_30_days": events_last_30_days,
        "statement": (
            "Metrics are computed from persisted Gaia records only. Configured MRR uses current "
            "Paystack plan prices and active canonical subscriptions; it is not booked revenue. "
            "One-time revenue includes only verified successful purchase ledger rows."
        ),
    }
