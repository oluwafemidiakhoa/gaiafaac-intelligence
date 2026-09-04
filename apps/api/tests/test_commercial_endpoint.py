from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from gaiafaac_api.config import get_settings
from gaiafaac_api.database.commercial_models import CommercialEvent, PilotLead
from gaiafaac_api.database.enums import SubscriptionStatus
from gaiafaac_api.database.models import Organization, Subscription
from gaiafaac_api.database.session import get_session
from gaiafaac_api.database.subscription_models import PaymentRecord
from gaiafaac_api.main import app

ADMIN_KEY = "test-admin-key"


@pytest.fixture
def admin_key(monkeypatch):
    monkeypatch.setenv("ADMIN_KEY", ADMIN_KEY)
    get_settings.cache_clear()
    yield ADMIN_KEY
    get_settings.cache_clear()


def _client(session) -> TestClient:
    app.dependency_overrides[get_session] = lambda: session
    return TestClient(app)


def _submit_lead(client: TestClient):
    return client.post(
        "/api/v1/commercial/pilot-leads",
        json={
            "name": "Ada Analyst",
            "email": "ADA@example.com",
            "organization": "Civic Research Lab",
            "role": "Researcher",
            "country": "Nigeria",
            "plan_interest": "analyst",
            "use_case": "I need reviewed historical FAAC data for state-level reporting.",
            "states_or_periods": "Edo, Delta; 2024",
            "preferred_format": "xlsx",
            "expected_users": 2,
            "website": "",
        },
        headers={"User-Agent": "should-not-be-retained/1.0"},
    )


def test_public_pilot_request_is_stored_without_tracking_metadata(session):
    client = _client(session)
    try:
        response = _submit_lead(client)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 202
    lead = session.scalar(select(PilotLead))
    assert lead is not None
    assert lead.email == "ada@example.com"
    assert lead.plan_interest == "analyst"
    assert lead.status == "new"
    assert lead.ip_address is None
    assert lead.user_agent is None
    event = session.scalar(select(CommercialEvent))
    assert event is not None
    assert event.event_name == "pilot_lead_submitted"
    assert event.subject_id == str(lead.id)
    assert event.event_metadata == {"plan_interest": "analyst", "source": "website"}


def test_honeypot_submission_is_not_stored(session):
    client = _client(session)
    try:
        response = client.post(
            "/api/v1/commercial/pilot-leads",
            json={
                "name": "Spam Bot",
                "email": "bot@example.com",
                "plan_interest": "api",
                "use_case": "This field is long enough to pass validation requirements.",
                "website": "https://spam.example",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 202
    count = session.scalar(select(func.count()).select_from(PilotLead))
    assert count == 0
    event_count = session.scalar(select(func.count()).select_from(CommercialEvent))
    assert event_count == 0


def test_admin_list_requires_key(session, admin_key):
    client = _client(session)
    try:
        assert client.get("/api/v1/commercial/pilot-leads").status_code == 401
        response = client.get(
            "/api/v1/commercial/pilot-leads",
            headers={"X-Admin-Key": admin_key},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == []


def test_admin_can_advance_lead_through_declared_stages(session, admin_key):
    client = _client(session)
    try:
        created = _submit_lead(client)
        lead_id = created.json()["id"]
        response = client.patch(
            f"/api/v1/commercial/pilot-leads/{lead_id}",
            headers={"X-Admin-Key": admin_key},
            json={
                "status": "qualified",
                "owner_name": "Commercial Owner",
                "next_action": "Schedule pilot scoping call",
                "next_action_at": "2026-09-08T15:00:00Z",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "qualified"
    assert body["owner_name"] == "Commercial Owner"
    assert body["next_action"] == "Schedule pilot scoping call"
    events = list(
        session.scalars(
            select(CommercialEvent).order_by(CommercialEvent.occurred_at, CommercialEvent.id)
        )
    )
    assert [event.event_name for event in events] == [
        "pilot_lead_submitted",
        "pilot_lead_stage_changed",
    ]
    assert events[-1].event_metadata["from_status"] == "new"
    assert events[-1].event_metadata["to_status"] == "qualified"


def test_invalid_crm_stage_is_rejected(session, admin_key):
    client = _client(session)
    try:
        created = _submit_lead(client)
        response = client.patch(
            f"/api/v1/commercial/pilot-leads/{created.json()['id']}",
            headers={"X-Admin-Key": admin_key},
            json={"status": "money-printing"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422


def test_commercial_analytics_use_persisted_values_only(session, admin_key):
    organization = Organization(name="Paid Org", slug="paid-org")
    session.add(organization)
    session.flush()
    subscription = Subscription(
        organization_id=organization.id,
        status=SubscriptionStatus.ACTIVE,
        plan_code="team",
        external_subscription_id="gfi-paid-test",
        current_period_start=datetime.now(UTC) - timedelta(days=1),
        current_period_end=datetime.now(UTC) + timedelta(days=29),
    )
    session.add(subscription)
    session.flush()
    session.add(
        PaymentRecord(
            organization_id=organization.id,
            canonical_subscription_id=subscription.id,
            paystack_transaction_id="gfi-paid-test",
            amount_naira=Decimal("200000.00"),
            status="success",
            invoice_number="GFI-PAID-TEST",
            completed_at=datetime.now(UTC),
        )
    )
    session.add(
        PilotLead(
            name="Commercial Lead",
            email="lead@example.com",
            plan_interest="team",
            use_case="A sufficiently detailed institutional use case for a paid team pilot.",
            status="pilot",
            source="website",
        )
    )
    session.commit()

    client = _client(session)
    try:
        assert client.get("/api/v1/commercial/analytics").status_code == 401
        response = client.get(
            "/api/v1/commercial/analytics",
            headers={"X-Admin-Key": admin_key},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["leads_total"] == 1
    assert body["leads_by_status"] == {"pilot": 1}
    assert body["active_subscriptions_total"] == 1
    assert body["active_subscriptions_by_plan"] == {"team": 1}
    assert body["successful_payment_count"] == 1
    assert body["successful_payment_revenue_naira"] == "200000.00"
    assert "persisted Gaia" in body["statement"]


def test_invalid_email_is_rejected(session):
    client = _client(session)
    try:
        response = client.post(
            "/api/v1/commercial/pilot-leads",
            json={
                "name": "Bad Email",
                "email": "not-an-email",
                "plan_interest": "team",
                "use_case": "We need a team workflow for monthly public-finance reporting.",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422