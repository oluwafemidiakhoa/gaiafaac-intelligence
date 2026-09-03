from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from gaiafaac_api.config import get_settings
from gaiafaac_api.database.debt_models import DebtKind, StateDebtRecord
from gaiafaac_api.database.enums import (
    ProcessingStatus,
    SourceStatus,
    UserRole,
    VerificationStatus,
)
from gaiafaac_api.database.models import SourceDocument, State, User
from gaiafaac_api.database.seeds import seed_states
from gaiafaac_api.database.session import get_session
from gaiafaac_api.main import app
from gaiafaac_api.pipeline.dmo.archive import DMO_ORGANIZATION

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


def _reviewer(session, *, role=UserRole.REVIEWER, email="dmo-reviewer@example.com") -> User:
    user = User(email=email, full_name="DMO Reviewer", role=role, is_active=True)
    session.add(user)
    session.commit()
    return user


def _staged_source(session) -> SourceDocument:
    seed_states(session)
    states = list(session.scalars(select(State).order_by(State.code)))
    source = SourceDocument(
        source_organization=DMO_ORGANIZATION,
        source_url="https://www.dmo.gov.ng/files/test.pdf",
        original_filename="test.pdf",
        storage_path="s3://bucket/dmo/domestic/2026-03-31/hash.pdf",
        sha256="a" * 64,
        mime_type="application/pdf",
        processing_status=ProcessingStatus.READY_FOR_REVIEW,
        source_status=SourceStatus.READY_FOR_REVIEW,
        document_version="domestic-2026-03-31",
        is_demo=False,
    )
    session.add(source)
    session.flush()
    for index, state in enumerate(states, start=1):
        session.add(
            StateDebtRecord(
                state_id=state.id,
                source_document_id=source.id,
                debt_kind=DebtKind.DOMESTIC,
                as_of_date=date(2026, 3, 31),
                debt_amount=Decimal(index * 1_000_000),
                debt_amount_original=f"{index * 1_000_000:.2f}",
                currency="NGN",
                components={},
                source_page=1,
                source_table="DMO domestic state/FCT debt stock",
                verification_status=VerificationStatus.REQUIRES_REVIEW,
                is_demo=False,
                is_published=False,
            )
        )
    session.commit()
    return source


def test_pending_dmo_review_requires_admin_key(session):
    client = _client(session)
    try:
        response = client.get("/api/v1/dmo-review/pending")
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 401


def test_full_review_lifecycle_via_the_api(session, admin_key):
    reviewer = _reviewer(session)
    administrator = _reviewer(session, role=UserRole.ADMINISTRATOR, email="dmo-admin@example.com")
    source = _staged_source(session)
    client = _client(session)
    headers = {"X-Admin-Key": admin_key}
    try:
        pending = client.get("/api/v1/dmo-review/pending", headers=headers)
        assert pending.status_code == 200
        assert len(pending.json()) == 1
        assert pending.json()[0]["source_document_id"] == str(source.id)

        packet = client.get(f"/api/v1/dmo-review/{source.id}", headers=headers)
        assert packet.status_code == 200
        body = packet.json()
        assert len(body["records"]) == 37
        assert body["approval"] is None

        approve = client.post(
            f"/api/v1/dmo-review/{source.id}/approve",
            headers=headers,
            json={"reviewer_id": str(reviewer.id), "attestation": True},
        )
        assert approve.status_code == 200
        assert approve.json()["published"] is False

        same_actor_publish = client.post(
            f"/api/v1/dmo-review/{source.id}/publish",
            headers=headers,
            json={"publisher_id": str(reviewer.id), "attestation": True},
        )
        assert same_actor_publish.status_code == 409

        publish = client.post(
            f"/api/v1/dmo-review/{source.id}/publish",
            headers=headers,
            json={"publisher_id": str(administrator.id), "attestation": True},
        )
        assert publish.status_code == 200
        assert publish.json()["published"] is True

        cleared = client.get("/api/v1/dmo-review/pending", headers=headers)
        assert cleared.json() == []
    finally:
        app.dependency_overrides.clear()
