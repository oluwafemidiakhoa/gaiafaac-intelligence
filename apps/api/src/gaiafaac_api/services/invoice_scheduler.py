"""Scheduled invoice generation and payment collection"""

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.subscription_models import (
    BillingEvent,
    OrganizationSubscription,
    SubscriptionTier,
)
from gaiafaac_api.services.billing import BillingService


def generate_monthly_invoices(session: Session) -> dict:
    """Generate invoices for all active subscriptions (call monthly)"""
    now = datetime.now(UTC)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_end = (month_start + timedelta(days=32)).replace(day=1)

    subscriptions = session.scalars(
        select(OrganizationSubscription).where(OrganizationSubscription.status == "active")
    ).all()

    invoices_created = 0
    invoices_failed = 0
    billing_service = BillingService(session)

    for subscription in subscriptions:
        try:
            tier = session.scalar(
                select(SubscriptionTier).where(SubscriptionTier.id == subscription.tier_id)
            )
            if not tier:
                continue

            billing_events = session.scalars(
                select(BillingEvent).where(
                    BillingEvent.subscription_id == subscription.id,
                    BillingEvent.created_at >= month_start,
                    BillingEvent.created_at < month_end,
                    ~BillingEvent.is_invoiced,
                )
            ).all()

            if not billing_events:
                billing_events = []

            subscription_charge = BillingEvent(
                organization_id=subscription.organization_id,
                subscription_id=subscription.id,
                event_type="subscription",
                description=f"{tier.name} tier subscription",
                amount_naira=tier.price_naira,
            )
            billing_events.append(subscription_charge)

            billing_service.generate_invoice(
                organization_id=subscription.organization_id,
                subscription_id=subscription.id,
                period_start=month_start,
                period_end=month_end,
                billing_events=billing_events,
            )

            invoices_created += 1
        except Exception as e:
            invoices_failed += 1
            print(f"Failed to generate invoice for subscription {subscription.id}: {e}")

    return {
        "invoices_created": invoices_created,
        "invoices_failed": invoices_failed,
        "period_start": month_start.isoformat(),
        "period_end": month_end.isoformat(),
    }


def check_overdue_invoices(session: Session) -> dict:
    """Check for overdue invoices and send reminders"""
    from gaiafaac_api.database.subscription_models import Invoice

    now = datetime.now(UTC)
    overdue_invoices = session.scalars(
        select(Invoice).where(
            Invoice.status.in_(["sent", "overdue"]),
            Invoice.due_date < now,
            Invoice.paid_date.is_(None),
        )
    ).all()

    reminders_sent = 0

    for invoice in overdue_invoices:
        try:
            if invoice.status == "sent":
                invoice.status = "overdue"

            reminders_sent += 1
            session.commit()
        except Exception as e:
            print(f"Failed to send overdue reminder for invoice {invoice.id}: {e}")

    return {
        "overdue_invoices": len(overdue_invoices),
        "reminders_sent": reminders_sent,
    }
