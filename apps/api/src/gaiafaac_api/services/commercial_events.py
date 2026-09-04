from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from gaiafaac_api.database.commercial_models import CommercialEvent, PilotLead
from gaiafaac_api.database.enums import SubscriptionStatus
from gaiafaac_api.database.models import Subscription
from gaiafaac_api.database.subscription_models import PaymentRecord


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
    )
    session.add(row)
    if commit:
        session.commit()
        session.refresh(row)
    return row


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
    active_subscriptions_by_plan = {str(name): int(count) for name, count in active_subscription_rows}
    events_last_30_days = {str(name): int(count) for name, count in event_rows}

    return {
        "generated_at": now,
        "leads_total": sum(leads_by_status.values()),
        "leads_by_status": leads_by_status,
        "leads_by_plan": leads_by_plan,
        "active_subscriptions_total": sum(active_subscriptions_by_plan.values()),
        "active_subscriptions_by_plan": active_subscriptions_by_plan,
        "successful_payment_count": int(successful_payment_count or 0),
        "successful_payment_revenue_naira": str(successful_payment_revenue or Decimal("0")),
        "events_last_30_days": events_last_30_days,
        "statement": "Metrics are computed from persisted Gaia commercial, subscription, and payment records only.",
    }
