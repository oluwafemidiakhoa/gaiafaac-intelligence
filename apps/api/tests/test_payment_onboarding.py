from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select

from gaiafaac_api.database.commercial_models import CommercialEvent
from gaiafaac_api.database.enums import SubscriptionStatus
from gaiafaac_api.database.models import Organization, Subscription
from gaiafaac_api.database.subscription_models import PaymentRecord
from gaiafaac_api.services.payment_onboarding import deliver_payment_onboarding


class _FakeEmailService:
    def __init__(self, result: bool = True):
        self.result = result
        self.messages = []

    def send_email(self, message):
        self.messages.append(message)
        return self.result


def _paid_records(session):
    organization = Organization(name="Onboarding Org", slug="onboarding-org")
    session.add(organization)
    session.flush()
    subscription = Subscription(
        organization_id=organization.id,
        status=SubscriptionStatus.ACTIVE,
        plan_code="team",
        external_subscription_id="gfi-onboarding-test",
        current_period_start=datetime.now(UTC),
        current_period_end=datetime.now(UTC) + timedelta(days=30),
    )
    session.add(subscription)
    session.flush()
    payment = PaymentRecord(
        organization_id=organization.id,
        canonical_subscription_id=subscription.id,
        paystack_transaction_id="gfi-onboarding-test",
        amount_naira=Decimal("200000.00"),
        status="success",
        invoice_number="GFI-ONBOARDING-TEST",
        completed_at=datetime.now(UTC),
    )
    session.add(payment)
    session.commit()
    return subscription, payment


def test_payment_onboarding_sends_once_and_is_auditable(session, monkeypatch):
    subscription, payment = _paid_records(session)
    email_service = _FakeEmailService()
    monkeypatch.setattr(
        "gaiafaac_api.services.payment_onboarding.get_email_service",
        lambda: email_service,
    )

    assert deliver_payment_onboarding(
        session,
        payment=payment,
        subscription=subscription,
        email="buyer@example.com",
    )
    assert len(email_service.messages) == 1
    assert "access is active" in email_service.messages[0].subject.lower()

    assert deliver_payment_onboarding(
        session,
        payment=payment,
        subscription=subscription,
        email="buyer@example.com",
    )
    assert len(email_service.messages) == 1

    events = list(
        session.scalars(
            select(CommercialEvent).where(
                CommercialEvent.subject_type == "payment_record",
                CommercialEvent.subject_id == str(payment.id),
            )
        )
    )
    assert sum(event.event_name == "onboarding_email_sent" for event in events) == 1


def test_payment_onboarding_failure_does_not_change_entitlement(session, monkeypatch):
    subscription, payment = _paid_records(session)
    email_service = _FakeEmailService(result=False)
    monkeypatch.setattr(
        "gaiafaac_api.services.payment_onboarding.get_email_service",
        lambda: email_service,
    )

    assert not deliver_payment_onboarding(
        session,
        payment=payment,
        subscription=subscription,
        email="buyer@example.com",
    )
    session.refresh(subscription)
    assert subscription.status == SubscriptionStatus.ACTIVE

    event = session.scalar(
        select(CommercialEvent).where(
            CommercialEvent.event_name == "onboarding_email_failed",
            CommercialEvent.subject_id == str(payment.id),
        )
    )
    assert event is not None
