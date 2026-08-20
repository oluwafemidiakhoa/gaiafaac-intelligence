from __future__ import annotations

import hashlib
import hmac
import socket
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from gaiafaac_api.config import Settings, get_settings
from gaiafaac_api.database.enums import EvidenceStatus, FiscalEventSeverity, SubscriptionStatus
from gaiafaac_api.database.models import Organization, State, Subscription, User
from gaiafaac_api.database.seeds import seed_states
from gaiafaac_api.database.session import get_session
from gaiafaac_api.database.webhook_models import (
    OrganizationWebhookDelivery,
    OrganizationWebhookEndpoint,
)
from gaiafaac_api.main import app
from gaiafaac_api.services import institutional_webhooks as webhooks
from gaiafaac_api.services.fiscal_institutional import publish_fiscal_event


def _public_dns(*args, **kwargs):
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))]


def _organization_with_api(session) -> tuple[Organization, User]:
    organization = Organization(name="Webhook Research", slug="webhook-research")
    session.add(organization)
    session.flush()
    user = User(
        organization_id=organization.id,
        email="webhooks@example.com",
        full_name="Webhook Owner",
        is_active=True,
    )
    session.add(user)
    session.flush()
    session.add(
        Subscription(
            organization_id=organization.id,
            status=SubscriptionStatus.ACTIVE,
            plan_code="api",
        )
    )
    session.commit()
    return organization, user


def _publish_event(session, state: State, *, detected_at: datetime, event_type: str = "source_revised"):
    event = publish_fiscal_event(
        session,
        state_id=state.id,
        event_type=event_type,
        severity=FiscalEventSeverity.MATERIAL,
        effective_at=detected_at,
        detected_at=detected_at,
        evidence_status=EvidenceStatus.VERIFIED,
        evidence_ids=["evidence-sha-1"],
        explanation="A retained official source changed at the same publication location.",
        calculation={"changed_claims": Decimal("2")},
    )
    session.commit()
    return event


def test_webhook_url_rejects_non_public_destinations(monkeypatch):
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *args, **kwargs: [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443))
        ],
    )
    with pytest.raises(ValueError, match="non-public"):
        webhooks.validate_webhook_url("https://hooks.example.com/gaia")
    with pytest.raises(ValueError, match="HTTPS"):
        webhooks.validate_webhook_url("http://example.com/gaia")
    with pytest.raises(ValueError, match="port 443"):
        webhooks.validate_webhook_url("https://example.com:8443/gaia")


def test_endpoint_enqueue_starts_at_creation_and_does_not_backfill_history(session, monkeypatch):
    seed_states(session)
    state = session.scalars(select(State).order_by(State.name)).first()
    assert state is not None
    organization, user = _organization_with_api(session)
    _publish_event(session, state, detected_at=datetime(2026, 1, 1, tzinfo=UTC))
    monkeypatch.setattr(socket, "getaddrinfo", _public_dns)
    settings = Settings(institutional_webhook_master_secret="m" * 64)
    endpoint, _secret = webhooks.create_endpoint(
        session,
        settings,
        organization_id=organization.id,
        created_by_user_id=user.id,
        name="Core feed",
        url="https://hooks.example.com/gaia",
        event_types=["source_revised"],
        jurisdiction_codes=[state.code],
    )
    endpoint.created_at = datetime(2026, 2, 1, tzinfo=UTC)
    session.commit()
    _publish_event(session, state, detected_at=datetime(2026, 3, 1, tzinfo=UTC))

    assert webhooks.enqueue_endpoint_events(session, endpoint) == 1
    deliveries = list(
        session.scalars(
            select(OrganizationWebhookDelivery).where(
                OrganizationWebhookDelivery.endpoint_id == endpoint.id
            )
        )
    )
    assert len(deliveries) == 1
    assert deliveries[0].payload["data"]["detected_at"].startswith("2026-03-01")


def test_delivery_is_signed_integrity_checked_and_sent_once(session, monkeypatch):
    seed_states(session)
    state = session.scalars(select(State).order_by(State.name)).first()
    assert state is not None
    organization, user = _organization_with_api(session)
    monkeypatch.setattr(socket, "getaddrinfo", _public_dns)
    settings = Settings(
        institutional_webhook_enabled=True,
        institutional_webhook_master_secret="s" * 64,
    )
    endpoint, secret = webhooks.create_endpoint(
        session,
        settings,
        organization_id=organization.id,
        created_by_user_id=user.id,
        name="Production events",
        url="https://hooks.example.com/gaia",
        event_types=["source_revised"],
        jurisdiction_codes=[],
    )
    endpoint.created_at = datetime(2026, 1, 1, tzinfo=UTC)
    session.commit()
    event = _publish_event(session, state, detected_at=datetime(2026, 4, 1, tzinfo=UTC))
    captured: list[tuple[bytes, dict[str, str]]] = []

    def _fake_post(*, endpoint_url, body, headers, timeout=10.0):
        assert endpoint_url == endpoint.url
        captured.append((body, headers))
        return webhooks.WebhookHttpResult(status=204, body_excerpt="")

    monkeypatch.setattr(webhooks, "_post_https", _fake_post)
    first = webhooks.run_webhook_delivery(session, settings)
    second = webhooks.run_webhook_delivery(session, settings)

    assert first.deliveries_created == 1
    assert first.delivered == 1
    assert second.deliveries_created == 0
    assert second.delivered == 0
    assert len(captured) == 1
    delivery = session.scalar(
        select(OrganizationWebhookDelivery).where(
            OrganizationWebhookDelivery.fiscal_event_id == event.event_id
        )
    )
    assert delivery is not None
    assert delivery.status == "delivered"
    assert webhooks.canonical_sha256(delivery.payload) == delivery.payload_sha256

    body, headers = captured[0]
    timestamp = int(headers["Gaia-Webhook-Timestamp"])
    signed = f"{timestamp}.{delivery.id}.{body.decode()}".encode()
    expected = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    assert headers["Gaia-Webhook-Signature"] == f"v1={expected}"
    assert headers["Gaia-Webhook-Id"] == str(delivery.id)


def test_failed_delivery_dead_letters_at_attempt_limit(session, monkeypatch):
    seed_states(session)
    state = session.scalars(select(State).order_by(State.name)).first()
    assert state is not None
    organization, user = _organization_with_api(session)
    monkeypatch.setattr(socket, "getaddrinfo", _public_dns)
    settings = Settings(
        institutional_webhook_enabled=True,
        institutional_webhook_master_secret="d" * 64,
    )
    endpoint, _secret = webhooks.create_endpoint(
        session,
        settings,
        organization_id=organization.id,
        created_by_user_id=user.id,
        name="Dead letter test",
        url="https://hooks.example.com/gaia",
        event_types=["source_revised"],
        jurisdiction_codes=[],
    )
    endpoint.created_at = datetime(2026, 1, 1, tzinfo=UTC)
    session.commit()
    _publish_event(session, state, detected_at=datetime(2026, 5, 1, tzinfo=UTC))
    monkeypatch.setattr(
        webhooks,
        "_post_https",
        lambda **kwargs: (_ for _ in ()).throw(ConnectionError("receiver unavailable")),
    )

    result = webhooks.run_webhook_delivery(session, settings, max_attempts=1)
    delivery = session.scalar(
        select(OrganizationWebhookDelivery).where(
            OrganizationWebhookDelivery.endpoint_id == endpoint.id
        )
    )
    assert result.dead_letter == 1
    assert delivery is not None
    assert delivery.status == "dead_letter"
    assert delivery.attempt_count == 1


def test_delivery_is_deferred_when_api_entitlement_is_revoked(session, monkeypatch):
    seed_states(session)
    state = session.scalars(select(State).order_by(State.name)).first()
    assert state is not None
    organization, user = _organization_with_api(session)
    monkeypatch.setattr(socket, "getaddrinfo", _public_dns)
    settings = Settings(
        institutional_webhook_enabled=True,
        institutional_webhook_master_secret="e" * 64,
    )
    endpoint, _secret = webhooks.create_endpoint(
        session,
        settings,
        organization_id=organization.id,
        created_by_user_id=user.id,
        name="Entitlement test",
        url="https://hooks.example.com/gaia",
        event_types=["source_revised"],
        jurisdiction_codes=[],
    )
    endpoint.created_at = datetime(2026, 1, 1, tzinfo=UTC)
    session.commit()
    _publish_event(session, state, detected_at=datetime(2026, 6, 1, tzinfo=UTC))
    assert webhooks.enqueue_endpoint_events(session, endpoint) == 1
    subscription = session.scalar(
        select(Subscription).where(Subscription.organization_id == organization.id)
    )
    assert subscription is not None
    subscription.status = SubscriptionStatus.CANCELED
    session.commit()

    result = webhooks.run_webhook_delivery(session, settings)
    delivery = session.scalar(
        select(OrganizationWebhookDelivery).where(
            OrganizationWebhookDelivery.endpoint_id == endpoint.id
        )
    )
    assert result.deferred >= 1
    assert delivery is not None
    assert delivery.status == "deferred"


def test_webhook_management_requires_api_entitlement(session, monkeypatch):
    client = TestClient(app)
    app.dependency_overrides[get_session] = lambda: session
    monkeypatch.setattr(socket, "getaddrinfo", _public_dns)
    monkeypatch.setenv("INSTITUTIONAL_WEBHOOK_MASTER_SECRET", "r" * 64)
    get_settings.cache_clear()
    try:
        response = client.post(
            "/api/v1/account/register",
            json={
                "full_name": "Webhook Admin",
                "email": "webhook-admin@example.com",
                "password": "a-long-secure-password",
                "organization_name": "Webhook Admin Org",
            },
        )
        assert response.status_code == 201
        headers = {"Authorization": f"Bearer {response.json()['token']}"}
        denied = client.get("/api/v1/account/webhooks", headers=headers)
        assert denied.status_code == 403

        user = session.scalar(select(User).where(User.email == "webhook-admin@example.com"))
        assert user is not None and user.organization_id is not None
        session.add(
            Subscription(
                organization_id=user.organization_id,
                status=SubscriptionStatus.ACTIVE,
                plan_code="api",
            )
        )
        session.commit()
        created = client.post(
            "/api/v1/account/webhooks",
            headers=headers,
            json={
                "name": "Core feed",
                "url": "https://hooks.example.com/gaia",
                "event_types": ["source_revised"],
                "jurisdiction_codes": [],
            },
        )
        assert created.status_code == 201
        assert created.json()["signing_secret"].startswith("gwhsec_")
        listed = client.get("/api/v1/account/webhooks", headers=headers)
        assert listed.status_code == 200
        assert "signing_secret" not in listed.json()[0]
    finally:
        app.dependency_overrides.clear()
        get_settings.cache_clear()
