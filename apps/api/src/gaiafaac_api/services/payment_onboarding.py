from __future__ import annotations

import logging
from html import escape

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.commercial_models import CommercialEvent
from gaiafaac_api.database.models import Subscription
from gaiafaac_api.database.subscription_models import PaymentRecord
from gaiafaac_api.services.commercial_events import record_commercial_event
from gaiafaac_api.services.zoho_email import EmailMessage, get_email_service

logger = logging.getLogger(__name__)


def _already_delivered(session: Session, payment: PaymentRecord) -> bool:
    return (
        session.scalar(
            select(CommercialEvent.id).where(
                CommercialEvent.event_name == "onboarding_email_sent",
                CommercialEvent.subject_type == "payment_record",
                CommercialEvent.subject_id == str(payment.id),
            )
        )
        is not None
    )


def deliver_payment_onboarding(
    session: Session,
    *,
    payment: PaymentRecord,
    subscription: Subscription,
    email: str | None,
) -> bool:
    """Deliver onboarding after verified payment without making entitlement depend on email."""

    normalized_email = (email or "").strip().lower()
    if not normalized_email:
        return False
    if _already_delivered(session, payment):
        return True

    plan_label = subscription.plan_code.replace("_", " ").title()
    invoice = payment.invoice_number or payment.paystack_transaction_id or str(payment.id)
    body_html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6;">
        <h2>Your Gaia Fiscal Intelligence access is active</h2>
        <p>Your verified payment has activated the <strong>{escape(plan_label)}</strong> plan.</p>
        <p>Receipt reference: <strong>{escape(invoice)}</strong></p>
        <p>You can now return to your Gaia account to use the capabilities included in your plan.</p>
        <p>Gaia preserves source provenance, evidence state and revision history. Paid access does not convert unavailable evidence into a reported fact.</p>
      </body>
    </html>
    """

    try:
        sent = get_email_service().send_email(
            EmailMessage(
                to=normalized_email,
                subject="Gaia Fiscal Intelligence access is active",
                body_html=body_html,
            )
        )
    except Exception as error:  # noqa: BLE001 - payment/entitlement must remain committed
        logger.warning("Post-payment onboarding email failed: %s", error)
        sent = False

    record_commercial_event(
        session,
        event_name="onboarding_email_sent" if sent else "onboarding_email_failed",
        organization_id=payment.organization_id,
        subject_type="payment_record",
        subject_id=str(payment.id),
        metadata={
            "plan_code": subscription.plan_code,
            "invoice_number": payment.invoice_number,
        },
    )
    return sent
