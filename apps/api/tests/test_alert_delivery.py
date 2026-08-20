import smtplib
from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy import select

from gaiafaac_api.config import Settings, get_settings
from gaiafaac_api.database.customer_models import (
    CustomerAlert,
    CustomerAlertDelivery,
    CustomerNotificationPreference,
)
from gaiafaac_api.database.models import State, User
from gaiafaac_api.database.seeds import seed_states
from gaiafaac_api.database.session import get_session
from gaiafaac_api.main import app
from gaiafaac_api.services.alert_delivery import deliver_customer_alerts


class _FakeSMTP:
    sent: list = []

    def __init__(self, host, port):
        self.host = host
        self.port = port

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def login(self, user, password):
        return None

    def send_message(self, message):
        _FakeSMTP.sent.append(message)


def _settings(**overrides) -> Settings:
    values = {
        "customer_alert_email_enabled": True,
        "customer_app_url": "https://gaia.example",
        "smtp_host": "smtp.example.com",
        "smtp_port": 465,
        "smtp_username": "alerts@example.com",
        "smtp_password": "app-password",
        "alert_from": "alerts@example.com",
    }
    values.update(overrides)
    return Settings(**values)


def _seed_alert(session):
    seed_states(session)
    state = session.scalars(select(State).order_by(State.name)).first()
    assert state is not None
    user = User(email="alerts-user@example.com", full_name="Alerts User", is_active=True)
    session.add(user)
    session.flush()
    session.add(
        CustomerNotificationPreference(
            user_id=user.id,
            email_enabled=True,
            include_fiscal_watch=True,
            include_fiscal_events=True,
            email_enabled_at=datetime.now(UTC),
        )
    )
    alert = CustomerAlert(
        user_id=user.id,
        state_id=state.id,
        event_key="fiscal-event:GFE-TEST",
        source_kind="fiscal_event",
        source_event_id=None,
        event_type="source_revised",
        severity="material",
        occurred_at=datetime(2026, 8, 1, tzinfo=UTC),
        payload={
            "headline": "Official fiscal source revised",
            "detail": "A revised official source was retained.",
            "link_path": "/events?event_type=source_revised",
            "evidence_ids": ["sha256:test"],
            "metrics": {},
        },
    )
    session.add(alert)
    session.commit()
    return user, alert


def test_delivery_sends_once_and_records_success(session, monkeypatch):
    _FakeSMTP.sent = []
    monkeypatch.setattr(smtplib, "SMTP_SSL", _FakeSMTP)
    _, alert = _seed_alert(session)

    first = deliver_customer_alerts(session, _settings(), year=2026)
    assert first.sent == 1
    assert len(_FakeSMTP.sent) == 1
    assert "Official fiscal source revised" in _FakeSMTP.sent[0]["Subject"]

    delivery = session.scalar(
        select(CustomerAlertDelivery).where(CustomerAlertDelivery.alert_id == alert.id)
    )
    assert delivery is not None
    assert delivery.status == "sent"
    assert delivery.attempt_count == 1
    assert delivery.delivered_at is not None

    second = deliver_customer_alerts(session, _settings(), year=2026)
    assert second.sent == 0
    assert second.skipped_sent == 1
    assert len(_FakeSMTP.sent) == 1


def test_delivery_is_deferred_when_operator_gate_is_off(session, monkeypatch):
    def _boom(*args, **kwargs):
        raise AssertionError("SMTP must not be called while delivery is disabled")

    monkeypatch.setattr(smtplib, "SMTP_SSL", _boom)
    _, alert = _seed_alert(session)
    result = deliver_customer_alerts(
        session,
        _settings(customer_alert_email_enabled=False),
        year=2026,
    )
    assert result.deferred == 1
    delivery = session.scalar(
        select(CustomerAlertDelivery).where(CustomerAlertDelivery.alert_id == alert.id)
    )
    assert delivery is not None
    assert delivery.status == "deferred"
    assert delivery.attempt_count == 0
    assert delivery.delivered_at is None


def _client(session) -> TestClient:
    app.dependency_overrides[get_session] = lambda: session
    return TestClient(app)


def _register(client: TestClient) -> str:
    response = client.post(
        "/api/v1/account/register",
        json={
            "full_name": "Preference User",
            "email": "preference@example.com",
            "password": "a-long-secure-password",
            "organization_name": "Preference Research",
        },
    )
    assert response.status_code == 201
    return response.json()["token"]


def test_customer_notification_preferences_are_explicit_opt_in(session, monkeypatch):
    monkeypatch.setenv("CUSTOMER_ALERT_EMAIL_ENABLED", "false")
    get_settings.cache_clear()
    client = _client(session)
    try:
        token = _register(client)
        headers = {"Authorization": f"Bearer {token}"}
        initial = client.get("/api/v1/watchlists/preferences", headers=headers)
        assert initial.status_code == 200
        assert initial.json()["email_enabled"] is False
        assert initial.json()["delivery_available"] is False

        updated = client.post(
            "/api/v1/watchlists/preferences",
            headers=headers,
            json={
                "email_enabled": True,
                "include_fiscal_watch": False,
                "include_fiscal_events": True,
            },
        )
        assert updated.status_code == 200
        assert updated.json()["email_enabled"] is True
        assert updated.json()["include_fiscal_watch"] is False
        assert updated.json()["include_fiscal_events"] is True
        assert updated.json()["email_enabled_at"] is not None
    finally:
        app.dependency_overrides.clear()
        get_settings.cache_clear()
