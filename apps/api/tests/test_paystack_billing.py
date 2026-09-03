import hashlib
import hmac
import uuid
from decimal import Decimal

from sqlalchemy import func, select

from gaiafaac_api.api.v1.routes.billing import (
    _activate_paystack_subscription,
    _record_paystack_payment,
    _verify_paystack_webhook,
)
from gaiafaac_api.database.models import Subscription
from gaiafaac_api.database.subscription_models import PaymentRecord


def _successful_payment(organization_id: uuid.UUID, reference: str = "gfi-test-reference"):
    return {
        "reference": reference,
        "amount": 5_000_000,
        "status": "success",
        "metadata": {
            "organization_id": str(organization_id),
            "plan_code": "analyst",
            "gaia_reference": reference,
        },
    }


def test_paystack_webhook_uses_hmac_sha512():
    secret = "sk_test_example"
    payload = b'{"event":"charge.success","data":{"reference":"gfi-test"}}'
    signature = hmac.new(secret.encode("utf-8"), payload, hashlib.sha512).hexdigest()

    assert _verify_paystack_webhook(signature, payload, secret)


def test_paystack_webhook_rejects_modified_payload():
    secret = "sk_test_example"
    payload = b'{"event":"charge.success"}'
    signature = hmac.new(secret.encode("utf-8"), payload, hashlib.sha512).hexdigest()

    assert not _verify_paystack_webhook(signature, payload + b" ", secret)


def test_paystack_activation_is_idempotent_for_same_reference(session):
    organization_id = uuid.uuid4()
    data = _successful_payment(organization_id)

    first = _activate_paystack_subscription(session, data)
    assert first is not None
    first_end = first.current_period_end

    second = _activate_paystack_subscription(session, data)
    assert second is not None
    assert second.id == first.id
    assert second.current_period_end == first_end

    count = session.scalar(select(func.count()).select_from(Subscription))
    assert count == 1


def test_paystack_payment_record_is_idempotent_and_keeps_receipt(session):
    organization_id = uuid.uuid4()
    data = _successful_payment(organization_id)
    subscription = _activate_paystack_subscription(session, data)
    assert subscription is not None

    first = _record_paystack_payment(session, data, subscription)
    second = _record_paystack_payment(session, data, subscription)

    assert first is not None
    assert second is not None
    assert second.id == first.id
    assert first.amount_naira == Decimal("50000")
    assert first.invoice_number == "GFI-GFI-TEST-REFERENCE"
    assert first.status == "success"

    count = session.scalar(select(func.count()).select_from(PaymentRecord))
    assert count == 1
