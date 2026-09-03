from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from gaiafaac_api.config import get_settings
from gaiafaac_api.database.enums import (
    ProcessingStatus,
    ReportedUnit,
    SourceStatus,
    UserRole,
    VerificationStatus,
)
from gaiafaac_api.database.igr_models import IgrPeriodType, StateIgrRecord
from gaiafaac_api.database.models import SourceDocument, State, User
from gaiafaac_api.database.seeds import seed_states
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


def _reviewer(session, *, role=UserRole.REVIEWER, email="igr-reviewer@example.com") -> User:
    user = User(email=email, full_name="NBS IGR Reviewer", role=role, is_active=True)
    session.add(user)
    session.commit()
    return user


def _staged_source(session, *, year: int = 2023) -> SourceDocument:
    seed_states(session)
    states = list(session.scalars(select(State).order_by(State.code)))
    source = SourceDocument(
        source_organization="National Bureau of Statistics (NBS)",
        source_url="https://www.nigerianstat.gov.ng/elibrary/read/1241579",
        original_filename="nbs-igr.pdf",
        storage_path="s3://bucket/nbs-igr/2023/hash.pdf",
        sha256="b" * 64,
        mime_type="application/pdf",
        processing_status=ProcessingStatus.READY_FOR_REVIEW,
        source_status=SourceStatus.READY_FOR_REVIEW,
        document_version=f"igr-{year}-report-1241579",
        is_demo=False,
    )
    session.add(source)
    session.flush()
    for index, state in enumerate(states, start=1):
        session.add(
            StateIgrRecord(
                state_id=state.id,
                source_document_id=source.id,
                fiscal_year=year,
                period_type=IgrPeriodType.ANNUAL,
                quarter=None,
                period_start=date(year, 1, 1),
                period_end=date(year, 12, 31),
                igr_amount=Decimal(index * 1_000_000),
                igr_amount_original=f"{index * 1_000_000:.2f}",
                reported_unit=ReportedUnit.NAIRA,
                source_page=43,
                source_table=f"NBS Internally Generated Revenue At State Level ({year})",
                verification_status=VerificationStatus.REQUIRES_REVIEW,
                is_demo=False,
                is_published=False,
            )
        )
    session.commit()
    return source


def test_pending_igr_review_requires_admin_key(session):
    client = _client(session)
    try:
        response = client.get("/api/v1/nbs-igr-review/pending")
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 401


def test_full_review_lifecycle_via_the_api(session, admin_key):
    reviewer = _reviewer(session)
    administrator = _reviewer(session, role=UserRole.ADMINISTRATOR, email="igr-admin@example.com")
    source = _staged_source(session)
    client = _client(session)
    headers = {"X-Admin-Key": admin_key}
    try:
        pending = client.get("/api/v1/nbs-igr-review/pending", headers=headers)
        assert pending.status_code == 200
        assert len(pending.json()) == 1
        assert pending.json()[0]["source_document_id"] == str(source.id)

        packet = client.get(f"/api/v1/nbs-igr-review/{source.id}", headers=headers)
        assert packet.status_code == 200
        assert len(packet.json()["records"]) == 37

        approve = client.post(
            f"/api/v1/nbs-igr-review/{source.id}/approve",
            headers=headers,
            json={"reviewer_id": str(reviewer.id), "attestation": True},
        )
        assert approve.status_code == 200
        assert approve.json()["published"] is False

        same_actor_publish = client.post(
            f"/api/v1/nbs-igr-review/{source.id}/publish",
            headers=headers,
            json={"publisher_id": str(reviewer.id), "attestation": True},
        )
        assert same_actor_publish.status_code == 409

        publish = client.post(
            f"/api/v1/nbs-igr-review/{source.id}/publish",
            headers=headers,
            json={"publisher_id": str(administrator.id), "attestation": True},
        )
        assert publish.status_code == 200
        assert publish.json()["published"] is True

        cleared = client.get("/api/v1/nbs-igr-review/pending", headers=headers)
        assert cleared.json() == []
    finally:
        app.dependency_overrides.clear()
