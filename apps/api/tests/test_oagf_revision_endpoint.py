from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from gaiafaac_api.config import get_settings
from gaiafaac_api.database.enums import UserRole
from gaiafaac_api.database.models import User
from gaiafaac_api.database.oagf_revision_models import OagfRevisionCase
from gaiafaac_api.database.session import get_session
from gaiafaac_api.main import app
from gaiafaac_api.pipeline.oagf.discovery import (
    DiscoveryInventory,
    FetchResponse,
    PublicationCandidate,
    PublicationCategory,
)
from gaiafaac_api.pipeline.oagf.revision_monitor import run_revision_monitor

ADMIN_KEY = "test-admin-key"
CATEGORY = PublicationCategory(
    name="FAAC Report",
    slug="faac-report",
    url="https://oagf.gov.ng/publications/faac-report/",
)
CANDIDATE = PublicationCandidate(
    category_name=CATEGORY.name,
    category_slug=CATEGORY.slug,
    title="Disbursement June, 2026",
    publication_page_url="https://oagf.gov.ng/oagf_publications/disbursement-june-2026/",
    document_url="https://oagf.gov.ng/wp-content/uploads/2026/08/Disbursement-June-2026.pdf",
    discovery_url="https://oagf.gov.ng/publications/faac-report/",
    source_publication_date=date(2026, 6, 1),
    displayed_year="2026",
    displayed_month="June",
    original_filename="Disbursement-June-2026.pdf",
)


class FakeClient:
    def __init__(self, body: bytes) -> None:
        self.body = body

    def inventory(self, **kwargs) -> DiscoveryInventory:
        return DiscoveryInventory((CATEGORY,), (CANDIDATE,), 1, ())

    def fetch_document(self, url: str) -> FetchResponse:
        return FetchResponse(self.body, "application/pdf", url)


@pytest.fixture
def admin_key(monkeypatch):
    monkeypatch.setenv("ADMIN_KEY", ADMIN_KEY)
    get_settings.cache_clear()
    yield ADMIN_KEY
    get_settings.cache_clear()


def _revision_case(session) -> OagfRevisionCase:
    run_revision_monitor(
        session,
        now=datetime(2026, 8, 18, tzinfo=UTC),
        client=FakeClient(b"%PDF version-one"),
    )
    run_revision_monitor(
        session,
        now=datetime(2026, 8, 19, tzinfo=UTC),
        client=FakeClient(b"%PDF version-two"),
    )
    return session.scalar(select(OagfRevisionCase))


def _reviewer(session) -> User:
    user = User(
        email=f"{uuid.uuid4()}@example.test",
        full_name="Revision Reviewer",
        role=UserRole.REVIEWER,
        is_active=True,
    )
    session.add(user)
    session.commit()
    return user


def test_revision_queue_requires_admin_key(session, admin_key):
    _revision_case(session)
    app.dependency_overrides[get_session] = lambda: session
    try:
        response = TestClient(app).get("/api/v1/review/oagf-revisions")
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 401


def test_revision_queue_and_retained_sources_are_available(session, admin_key):
    case = _revision_case(session)
    app.dependency_overrides[get_session] = lambda: session
    try:
        client = TestClient(app)
        queue = client.get(
            "/api/v1/review/oagf-revisions",
            headers={"X-Admin-Key": admin_key},
        )
        previous = client.get(
            f"/api/v1/review/oagf-revisions/{case.id}/source/previous",
            headers={"X-Admin-Key": admin_key},
        )
        current = client.get(
            f"/api/v1/review/oagf-revisions/{case.id}/source/current",
            headers={"X-Admin-Key": admin_key},
        )
    finally:
        app.dependency_overrides.clear()

    assert queue.status_code == 200
    assert len(queue.json()) == 1
    assert previous.content == b"%PDF version-one"
    assert current.content == b"%PDF version-two"


def test_revision_classification_is_attributable_and_does_not_publish(session, admin_key):
    case = _revision_case(session)
    reviewer = _reviewer(session)
    app.dependency_overrides[get_session] = lambda: session
    try:
        response = TestClient(app).post(
            f"/api/v1/review/oagf-revisions/{case.id}/resolve",
            headers={"X-Admin-Key": admin_key},
            json={
                "reviewer_id": str(reviewer.id),
                "resolution_code": "requires_data_republication",
                "attestation": True,
                "note": "The official revision changes fiscal values and needs a governed replacement.",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["status"] == "investigation_required"
    session.refresh(case)
    assert case.reviewed_by == reviewer.id
    assert case.resolution_code == "requires_data_republication"
