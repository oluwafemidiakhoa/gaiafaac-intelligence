import csv
import uuid
from datetime import date

import pytest
from fastapi.testclient import TestClient

from gaiafaac_api.config import get_settings
from gaiafaac_api.database.enums import UserRole
from gaiafaac_api.database.models import User
from gaiafaac_api.database.seeds import seed_states
from gaiafaac_api.database.session import get_session
from gaiafaac_api.main import app
from gaiafaac_api.pipeline.extraction.file_import import import_file
from gaiafaac_api.pipeline.importer import ImportRequest

ADMIN_KEY = "test-admin-key"


@pytest.fixture
def admin_key(monkeypatch):
    monkeypatch.setenv("ADMIN_KEY", ADMIN_KEY)
    get_settings.cache_clear()
    yield ADMIN_KEY
    get_settings.cache_clear()


def _seed_pending(session, tmp_path):
    seed_states(session)
    csv_path = tmp_path / "jan.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            ["state", "gross_total", "total_deductions", "net_allocation", "reported_unit"]
        )
        writer.writerow(["Lagos", "1000.00", "100.00", "900.00", "naira"])
    import_file(
        session,
        ImportRequest(
            path=csv_path,
            source_organization="OAGF",
            revenue_month=date(2024, 1, 1),
            reporting_label="OAGF Jan 2024",
            reported_unit="naira",
        ),
    )


def _user(session, *, role: UserRole, active: bool = True) -> User:
    user = User(
        email=f"{uuid.uuid4()}@example.test",
        full_name=f"{role.value.title()} User",
        role=role,
        is_active=active,
    )
    session.add(user)
    session.commit()
    return user


def test_pending_requires_admin_key(session, tmp_path, admin_key):
    _seed_pending(session, tmp_path)
    app.dependency_overrides[get_session] = lambda: session
    try:
        client = TestClient(app)
        assert client.get("/api/v1/review/pending").status_code == 401
        assert (
            client.get("/api/v1/review/pending", headers={"X-Admin-Key": "wrong"}).status_code
            == 401
        )
    finally:
        app.dependency_overrides.clear()


def test_pending_returns_queue_with_admin_key(session, tmp_path, admin_key):
    _seed_pending(session, tmp_path)
    app.dependency_overrides[get_session] = lambda: session
    try:
        client = TestClient(app)
        response = client.get("/api/v1/review/pending", headers={"X-Admin-Key": admin_key})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["reporting_label"] == "OAGF Jan 2024"
    assert body[0]["approved"] is False
    assert body[0]["approved_by"] is None
    assert "gross_total" not in body[0]
    assert "total_deductions" not in body[0]
    assert "net_allocation" not in body[0]


def test_review_actors_are_dynamic_and_role_scoped(session, admin_key):
    reviewer = _user(session, role=UserRole.REVIEWER)
    administrator = _user(session, role=UserRole.ADMINISTRATOR)
    _user(session, role=UserRole.VIEWER)
    _user(session, role=UserRole.REVIEWER, active=False)

    app.dependency_overrides[get_session] = lambda: session
    try:
        client = TestClient(app)
        response = client.get("/api/v1/review/actors", headers={"X-Admin-Key": admin_key})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    actors = response.json()
    assert {item["id"] for item in actors} == {str(reviewer.id), str(administrator.id)}
    assert {item["role"] for item in actors} == {"reviewer", "administrator"}


def test_publish_endpoint_requires_admin_key(session, admin_key):
    app.dependency_overrides[get_session] = lambda: session
    try:
        client = TestClient(app)
        run_id = uuid.uuid4()
        response = client.post(
            f"/api/v1/review/{run_id}/publish",
            json={"publisher_id": str(uuid.uuid4()), "attestation": True},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 401
