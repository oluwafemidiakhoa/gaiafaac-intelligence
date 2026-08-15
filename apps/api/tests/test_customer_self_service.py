from fastapi.testclient import TestClient
from sqlalchemy import select

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
    from gaiafaac_api.config import get_settings

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
