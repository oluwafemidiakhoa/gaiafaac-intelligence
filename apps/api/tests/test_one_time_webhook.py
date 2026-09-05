import hashlib
import hmac
import json
import uuid

from fastapi.testclient import TestClient

from gaiafaac_api.config import get_settings
from gaiafaac_api.database.commercial_models import OneTimePurchase
from gaiafaac_api.database.session import get_session
from gaiafaac_api.main import app


def test_signed_paystack_webhook_completes_paid_one_time_order(session, monkeypatch):
    signing_key = "unit-test-signing-key"
    monkeypatch.setenv("PAYSTACK_SECRET_KEY", signing_key)
    monkeypatch.setenv("PAYSTACK_PRICE_DECISION_PACK", "75000")
    get_settings.cache_clear()

    from gaiafaac_api.api.v1.routes import one_time_billing

    normalized = {"state_slug": "edo", "state_code": "ED", "year": 2026}
    artifact = {
        "schema": "gaia-one-time-decision-pack-v1",
        "captured_at": "2026-09-05T12:00:00+00:00",
        "request": normalized,
        "decision_packet": {"state_slug": "edo", "year": 2026},
    }
    monkeypatch.setattr(
        one_time_billing,
        "normalize_one_time_context",
        lambda _session, *, product_code, context: normalized,
    )
    monkeypatch.setattr(
        one_time_billing,
        "build_one_time_fulfillment",
        lambda _session, *, product_code, context: artifact,
    )
    monkeypatch.setattr(
        one_time_billing,
        "_initialize_paystack_transaction",
        lambda **_kwargs: "https://checkout.example/order",
    )

    app.dependency_overrides[get_session] = lambda: session
    client = TestClient(app)
    try:
        registration = client.post(
            "/api/v1/account/register",
            json={
                "full_name": "Webhook Buyer",
                "email": "webhook-buyer@example.test",
                "password": "a-long-secure-password",
                "organization_name": "Webhook Test Org",
            },
        )
        assert registration.status_code == 201
        token = registration.json()["token"]
        checkout = client.post(
            "/api/v1/billing/one-time/checkout",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "product_code": "decision_pack",
                "context": {"state_code": "ED", "year": 2026},
            },
        )
        assert checkout.status_code == 200
        purchase_body = checkout.json()["purchase"]
        purchase_id = purchase_body["id"]
        reference = purchase_body["provider_reference"]
        purchase = session.get(OneTimePurchase, uuid.UUID(purchase_id))
        assert purchase is not None

        body = json.dumps(
            {
                "event": "charge.success",
                "data": {
                    "status": "success",
                    "reference": reference,
                    "amount": 7_500_000,
                    "metadata": {
                        "purchase_mode": "one_time",
                        "purchase_id": purchase_id,
                        "organization_id": str(purchase.organization_id),
                        "product_code": "decision_pack",
                    },
                },
            },
            separators=(",", ":"),
        ).encode()
        signature = hmac.new(signing_key.encode(), body, hashlib.sha512).hexdigest()
        webhook = client.post(
            "/api/v1/billing/paystack-webhook",
            content=body,
            headers={
                "content-type": "application/json",
                "x-paystack-signature": signature,
            },
        )

        assert webhook.status_code == 204
        session.refresh(purchase)
        assert purchase.status == "success"
        assert purchase.fulfillment_status == "ready"
        assert purchase.fulfillment_reference is not None
        assert purchase.fulfilled_at is not None
    finally:
        app.dependency_overrides.clear()
        get_settings.cache_clear()
