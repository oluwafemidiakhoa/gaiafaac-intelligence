from __future__ import annotations

import socket
import uuid
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select

from gaiafaac_api.config import Settings
from gaiafaac_api.database.customer_models import (
    CustomerNotificationPreference,
    OrganizationAlert,
)
from gaiafaac_api.database.enums import SubscriptionStatus
from gaiafaac_api.database.models import State, Subscription, User
from gaiafaac_api.database.session import get_session
from gaiafaac_api.database.watch_contract_models import (
    FiscalWatchContract,
    FiscalWatchContractDelivery,
    FiscalWatchContractDeliveryAttempt,
    FiscalWatchContractMatch,
)
from gaiafaac_api.main import app
from gaiafaac_api.services import institutional_webhooks as webhooks
from gaiafaac_api.services import watch_contract_delivery as delivery
from gaiafaac_api.services.watch_contract_operations import ensure_operational_reviews


def _client(session) -> TestClient:
    app.dependency_overrides[get_session] = lambda: session
    return TestClient(app)


def _register(client: TestClient, email: str) -> str:
    response = client.post(
        "/api/v1/account/register",
        json={
            "full_name": "Watch Delivery Owner",
            "email": email,
            "password": "a-long-secure-password",
            "organization_name": f"Watch Delivery {email}",
        },
    )
    assert response.status_code == 201
    return response.json()["token"]


def _activate_api(session, email: str) -> User:
    user = session.scalar(select(User).where(User.email == email))
    assert user is not None and user.organization_id is not None
    session.add(
        Subscription(
            organization_id=user.organization_id,
            status=SubscriptionStatus.ACTIVE,
            plan_code="api",
            external_customer_id=f"cus_{user.organization_id.hex[:12]}",
            external_subscription_id=f"sub_{user.organization_id.hex[:12]}",
        )
    )
    session.commit()
    return user


def _public_dns(*args, **kwargs):
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))]


def _review_fixture(session, client: TestClient, token: str, user: User):
    assert user.organization_id is not None
    state = State(
        name="Outbound Watch Test State",
        code="ZZ",
        slug="outbound-watch-test-state",
        geopolitical_zone="Test Zone",
        capital="Test Capital",
        is_fct=False,
    )
    session.add(state)
    session.flush()
    room_response = client.post(
        "/api/v1/evidence-rooms",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Outbound watch decision",
            "decision_question": "Does this governed change require re-review?",
            "jurisdictions": ["Outbound Watch Test State"],
            "evidence_domains": ["FAAC"],
            "baseline_date": "2026-09-04",
        },
    )
    assert room_response.status_code == 201
    contract_response = client.post(
        "/api/v1/fiscal-watch-contracts",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "room_id": room_response.json()["id"],
            "name": "Outbound Watch Contract",
            "state_codes": ["ZZ"],
            "event_types": ["source_revised"],
            "minimum_severity": "watch",
            "escalation_after_minutes": 60,
        },
    )
    assert contract_response.status_code == 201
    contract = session.get(
        FiscalWatchContract,
        uuid.UUID(contract_response.json()["id"]),
    )
    assert contract is not None
    alert = OrganizationAlert(
        organization_id=user.organization_id,
        state_id=state.id,
        event_key="watch-outbound-source-revised",
        source_kind="publication",
        event_type="source_revised",
        severity="material",
        occurred_at=datetime.now(UTC),
        payload={
            "headline": "Official source revision",
            "detail": "The retained source changed after the baseline receipt.",
        },
    )
    session.add(alert)
    session.flush()
    match = FiscalWatchContractMatch(
        contract_id=contract.id,
        organization_id=user.organization_id,
        room_id=contract.room_id,
        organization_alert_id=alert.id,
    )
    session.add(match)
    session.flush()
    assert ensure_operational_reviews(session, contract, [match]) == 1
    session.commit()
    return state, contract


def _settings() -> Settings:
    return Settings(
        customer_app_url="https://gaia.example",
        customer_alert_email_enabled=True,
        smtp_host="smtp.example.com",
        smtp_port=465,
        smtp_username="smtp-user",
        smtp_password="smtp-password",
        alert_from="alerts@gaia.example",
        institutional_webhook_enabled=True,
        institutional_webhook_master_secret="w" * 64,
    )


def test_watch_outbound_materializes_and_delivers_email_and_webhook_once(session, monkeypatch):
    client = _client(session)
    try:
        email = "watch-outbound@example.com"
        token = _register(client, email)
        user = _activate_api(session, email)
        state, _contract = _review_fixture(session, client, token, user)
        session.add(
            CustomerNotificationPreference(
                user_id=user.id,
                email_enabled=True,
                include_fiscal_watch=True,
                include_fiscal_events=True,
                email_enabled_at=datetime.now(UTC) - timedelta(hours=1),
            )
        )
        session.commit()

        monkeypatch.setattr(socket, "getaddrinfo", _public_dns)
        endpoint, _secret = webhooks.create_endpoint(
            session,
            _settings(),
            organization_id=user.organization_id,
            created_by_user_id=user.id,
            name="Watch receiver",
            url="https://hooks.example.com/watch",
            event_types=["source_revised"],
            jurisdiction_codes=[state.code],
        )
        endpoint.created_at = datetime.now(UTC) - timedelta(hours=1)
        session.commit()

        sent_email: list[str] = []
        sent_webhook: list[dict[str, str]] = []

        def fake_email(settings, row):
            sent_email.append(row.recipient_address or "")
            return True, None

        def fake_post(*, endpoint_url, body, headers, timeout=10.0):
            assert endpoint_url == endpoint.url
            assert b'"type":"watch_contract_match"' in body
            sent_webhook.append(headers)
            return webhooks.WebhookHttpResult(status=204, body_excerpt="")

        monkeypatch.setattr(delivery, "_send_email", fake_email)
        monkeypatch.setattr(delivery, "_post_https", fake_post)

        first = delivery.run_watch_delivery(
            session, _settings(), organization_id=user.organization_id
        )
        second = delivery.run_watch_delivery(
            session, _settings(), organization_id=user.organization_id
        )

        assert first.deliveries_created == 2
        assert first.delivered == 2
        assert second.deliveries_created == 0
        assert second.delivered == 0
        assert sent_email == [email]
        assert len(sent_webhook) == 1
        assert sent_webhook[0]["Gaia-Webhook-Schema"] == delivery.WATCH_WEBHOOK_SCHEMA_VERSION
        assert sent_webhook[0]["Gaia-Webhook-Signature"].startswith("v1=")

        rows = list(
            session.scalars(
                select(FiscalWatchContractDelivery).where(
                    FiscalWatchContractDelivery.organization_id == user.organization_id
                )
            )
        )
        assert {row.channel for row in rows} == {"in_app", "email", "webhook"}
        outbound = [row for row in rows if row.channel != "in_app"]
        assert all(row.status == "delivered" for row in outbound)
        assert all(row.attempt_count == 1 for row in outbound)
        assert all(row.payload_sha256 and len(row.payload_sha256) == 64 for row in outbound)
        attempts = list(session.scalars(select(FiscalWatchContractDeliveryAttempt)))
        assert len(attempts) == 2
        assert all(attempt.attempt_number == 1 for attempt in attempts)
    finally:
        app.dependency_overrides.clear()


def test_watch_webhook_failure_dead_letters_and_attempt_is_immutable(session, monkeypatch):
    client = _client(session)
    try:
        email = "watch-dead-letter@example.com"
        token = _register(client, email)
        user = _activate_api(session, email)
        state, _contract = _review_fixture(session, client, token, user)
        monkeypatch.setattr(socket, "getaddrinfo", _public_dns)
        webhooks.create_endpoint(
            session,
            _settings(),
            organization_id=user.organization_id,
            created_by_user_id=user.id,
            name="Failing receiver",
            url="https://hooks.example.com/fail",
            event_types=["source_revised"],
            jurisdiction_codes=[state.code],
        )
        endpoint = session.scalars(select(webhooks.OrganizationWebhookEndpoint)).first()
        assert endpoint is not None
        endpoint.created_at = datetime.now(UTC) - timedelta(hours=1)
        session.commit()

        monkeypatch.setattr(
            delivery,
            "_post_https",
            lambda **kwargs: (_ for _ in ()).throw(ConnectionError("receiver unavailable")),
        )
        result = delivery.run_watch_delivery(
            session,
            _settings(),
            organization_id=user.organization_id,
            max_attempts=1,
        )
        webhook_delivery = session.scalar(
            select(FiscalWatchContractDelivery).where(
                FiscalWatchContractDelivery.organization_id == user.organization_id,
                FiscalWatchContractDelivery.channel == "webhook",
            )
        )
        assert result.dead_letter == 1
        assert webhook_delivery is not None
        assert webhook_delivery.status == "dead_letter"
        assert webhook_delivery.attempt_count == 1
        attempt = session.scalar(
            select(FiscalWatchContractDeliveryAttempt).where(
                FiscalWatchContractDeliveryAttempt.delivery_id == webhook_delivery.id
            )
        )
        assert attempt is not None
        assert attempt.error == "receiver unavailable"
        attempt.error = "tampered"
        try:
            session.commit()
        except ValueError:
            session.rollback()
        else:
            raise AssertionError("Watch delivery attempts must be immutable")
    finally:
        app.dependency_overrides.clear()


def test_watch_email_is_not_backfilled_before_explicit_opt_in(session, monkeypatch):
    client = _client(session)
    try:
        email = "watch-late-opt-in@example.com"
        token = _register(client, email)
        user = _activate_api(session, email)
        _state, _contract = _review_fixture(session, client, token, user)
        session.add(
            CustomerNotificationPreference(
                user_id=user.id,
                email_enabled=True,
                include_fiscal_watch=True,
                include_fiscal_events=True,
                email_enabled_at=datetime.now(UTC) + timedelta(minutes=5),
            )
        )
        session.commit()
        monkeypatch.setattr(delivery, "_send_email", lambda settings, row: (True, None))

        result = delivery.run_watch_delivery(
            session, _settings(), organization_id=user.organization_id
        )
        email_delivery = session.scalar(
            select(FiscalWatchContractDelivery).where(
                FiscalWatchContractDelivery.organization_id == user.organization_id,
                FiscalWatchContractDelivery.channel == "email",
            )
        )
        assert result.deliveries_created == 0
        assert email_delivery is None
    finally:
        app.dependency_overrides.clear()
