import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from gaiafaac_api.config import get_settings
from gaiafaac_api.database.commercial_models import PilotLead
from gaiafaac_api.database.session import get_session
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


def test_public_pilot_request_is_stored(session):
    client = _client(session)
    try:
        response = client.post(
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
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 202
    lead = session.scalar(select(PilotLead))
    assert lead is not None
    assert lead.email == "ada@example.com"
    assert lead.plan_interest == "analyst"
    assert lead.status == "new"


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
