from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import select

from gaiafaac_api.config import get_settings
from gaiafaac_api.database.commercial_models import CommercialEvent, OneTimePurchase
from gaiafaac_api.database.enums import SubscriptionStatus
from gaiafaac_api.database.models import Subscription, User
from gaiafaac_api.database.session import get_session
from gaiafaac_api.main import app
from gaiafaac_api.services.passwords import verify_password


def _client(session) -> TestClient:
    app.dependency_overrides[get_session] = lambda: session
    return TestClient(app)


def _register(client: TestClient):
    response = client.post(
        "/api/v1/account/register",
        json={
            "full_name": "Ada Analyst",
            "email": "ADA@example.com",
            "password": "a-long-secure-password",
            "organization_name": "Civic Research Lab",
        },
    )
    assert response.status_code == 201
    return response.json()["token"]


def test_customer_register_login_and_profile(session):
    client = _client(session)
    try:
        token = _register(client)
        user = session.scalar(select(User).where(User.email == "ada@example.com"))
        assert user is not None
        assert user.password_hash != "a-long-secure-password"
        assert verify_password("a-long-secure-password", user.password_hash)

        profile = client.get(
            "/api/v1/account/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert profile.status_code == 200
        assert profile.json()["plan_code"] == "free"
        assert profile.json()["membership_role"] == "owner"

        login = client.post(
            "/api/v1/account/login",
            json={"email": "ADA@example.com", "password": "a-long-secure-password"},
        )
        assert login.status_code == 200
        assert login.json()["token"].startswith("gfs_")
    finally:
        app.dependency_overrides.clear()


def test_free_account_cannot_export(session):
    client = _client(session)
    try:
        token = _register(client)
        response = client.get(
            "/api/v1/account/exports/allocations.csv?month=2026-06-01",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_api_plan_can_create_and_revoke_key(session):
    client = _client(session)
    try:
        token = _register(client)
        user = session.scalar(select(User).where(User.email == "ada@example.com"))
        assert user is not None and user.organization_id is not None
        session.add(
            Subscription(
                organization_id=user.organization_id,
                status=SubscriptionStatus.ACTIVE,
                plan_code="api",
                external_customer_id="cus_test",
                external_subscription_id="sub_test",
            )
        )
        session.commit()

        created = client.post(
            "/api/v1/account/api-keys",
            headers={"Authorization": f"Bearer {token}"},
            json={"name": "Production"},
        )
        assert created.status_code == 201
        body = created.json()
        assert body["api_key"].startswith("gfk_")

        listed = client.get(
            "/api/v1/account/api-keys",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert listed.status_code == 200
        assert listed.json()[0]["key_prefix"] == body["key_prefix"]

        revoked = client.delete(
            f"/api/v1/account/api-keys/{body['id']}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert revoked.status_code == 204
    finally:
        app.dependency_overrides.clear()


def test_checkout_is_securely_disabled_without_stripe_configuration(session, monkeypatch):
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    get_settings.cache_clear()
    client = _client(session)
    try:
        token = _register(client)
        response = client.post(
            "/api/v1/billing/checkout",
            headers={"Authorization": f"Bearer {token}"},
            json={"plan_code": "analyst"},
        )
        assert response.status_code == 503
    finally:
        app.dependency_overrides.clear()
        get_settings.cache_clear()


def test_one_time_checkout_fails_closed_until_price_is_approved(session, monkeypatch):
    monkeypatch.setenv("PAYSTACK_SECRET_KEY", "test-secret")
    monkeypatch.setenv("PAYSTACK_PRICE_DECISION_PACK", "0")
    get_settings.cache_clear()
    client = _client(session)
    try:
        token = _register(client)
        response = client.post(
            "/api/v1/billing/one-time/checkout",
            headers={"Authorization": f"Bearer {token}"},
            json={"product_code": "decision_pack", "context": {"state": "ED"}},
        )
        assert response.status_code == 503
        assert session.scalar(select(OneTimePurchase)) is None
    finally:
        app.dependency_overrides.clear()
        get_settings.cache_clear()


def test_one_time_purchase_is_persisted_and_verified_once(session, monkeypatch):
    monkeypatch.setenv("PAYSTACK_SECRET_KEY", "test-secret")
    monkeypatch.setenv("PAYSTACK_PRICE_DECISION_PACK", "75000")
    get_settings.cache_clear()

    from gaiafaac_api.api.v1.routes import one_time_billing

    monkeypatch.setattr(
        one_time_billing,
        "_initialize_paystack_transaction",
        lambda **_kwargs: "https://checkout.example/order",
    )

    client = _client(session)
    try:
        token = _register(client)
        headers = {"Authorization": f"Bearer {token}"}
        checkout = client.post(
            "/api/v1/billing/one-time/checkout",
            headers=headers,
            json={
                "product_code": "decision_pack",
                "context": {"state_code": "ED", "period": "2026-06"},
            },
        )
        assert checkout.status_code == 200
        body = checkout.json()
        assert body["url"] == "https://checkout.example/order"
        assert body["purchase"]["amount_naira"] == "75000.00"
        purchase_id = body["purchase"]["id"]
        reference = body["purchase"]["provider_reference"]

        purchase = session.get(OneTimePurchase, purchase_id)
        assert purchase is not None
        assert purchase.status == "pending"
        assert purchase.amount_naira == Decimal("75000")
        assert purchase.purchase_metadata == {"state_code": "ED", "period": "2026-06"}

        monkeypatch.setattr(
            one_time_billing,
            "_verify_paystack_transaction",
            lambda _reference: {
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
        )
        verified = client.post(
            f"/api/v1/billing/one-time/paystack-verify?reference={reference}",
            headers=headers,
        )
        assert verified.status_code == 200
        assert verified.json()["status"] == "success"

        verified_again = client.post(
            f"/api/v1/billing/one-time/paystack-verify?reference={reference}",
            headers=headers,
        )
        assert verified_again.status_code == 200
        events = list(
            session.scalars(
                select(CommercialEvent).where(
                    CommercialEvent.subject_type == "one_time_purchase",
                    CommercialEvent.subject_id == purchase_id,
                )
            )
        )
        assert sorted(event.event_name for event in events) == [
            "one_time_checkout_started",
            "one_time_purchase_completed",
        ]
    finally:
        app.dependency_overrides.clear()
        get_settings.cache_clear()
