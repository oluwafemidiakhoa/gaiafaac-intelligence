from datetime import UTC, datetime
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import select

from gaiafaac_api.database.enums import SourceStatus
from gaiafaac_api.database.models import SourceDocument, State
from gaiafaac_api.database.seeds import seed_states
from gaiafaac_api.database.session import get_session
from gaiafaac_api.main import app
from gaiafaac_api.services.fiscal_domain_claims import publish_domain_claim
from gaiafaac_api.services.temporal_intelligence import temporal_fiscal_snapshot


def _setup_revisions(session):
    seed_states(session)
    state = session.scalar(select(State).where(State.code == "LA"))
    assert state is not None
    first = SourceDocument(
        source_organization="Official publisher",
        original_filename="first.pdf",
        storage_path="first.pdf",
        sha256="1" * 64,
        mime_type="application/pdf",
        source_status=SourceStatus.APPROVED,
        is_demo=False,
    )
    second = SourceDocument(
        source_organization="Official publisher",
        original_filename="second.pdf",
        storage_path="second.pdf",
        sha256="2" * 64,
        mime_type="application/pdf",
        source_status=SourceStatus.APPROVED,
        is_demo=False,
    )
    session.add_all([first, second])
    session.flush()
    second.supersedes_document_id = first.id
    effective = datetime(2026, 6, 30, 23, 59, tzinfo=UTC)
    first_known = datetime(2026, 7, 15, 10, 0, tzinfo=UTC)
    revised_known = datetime(2026, 8, 15, 10, 0, tzinfo=UTC)
    original = publish_domain_claim(
        session,
        domain="debt",
        state_id=state.id,
        source_document_id=first.id,
        fiscal_period="2026Q2",
        metric="total_debt_stock",
        value=Decimal("100"),
        value_text="100",
        unit="naira",
        currency="NGN",
        effective_at=effective,
        published_at=first_known,
        human_reviewed=True,
        reconciled=True,
    )
    revised = publish_domain_claim(
        session,
        domain="debt",
        state_id=state.id,
        source_document_id=second.id,
        fiscal_period="2026Q2",
        metric="total_debt_stock",
        value=Decimal("120"),
        value_text="120",
        unit="naira",
        currency="NGN",
        effective_at=effective,
        published_at=revised_known,
        human_reviewed=True,
        reconciled=True,
    )
    session.commit()
    return state, original, revised


def test_temporal_snapshot_preserves_what_gaia_knew(session):
    _state, original, revised = _setup_revisions(session)
    effective_cutoff = datetime(2026, 6, 30, 23, 59, tzinfo=UTC)

    before_revision = temporal_fiscal_snapshot(
        session,
        jurisdiction_code="NG-LA",
        effective_as_of=effective_cutoff,
        known_as_of=datetime(2026, 8, 1, 0, 0, tzinfo=UTC),
    )
    assert before_revision is not None
    assert before_revision.data.claim_count == 1
    assert before_revision.data.domains["debt"][0].gaia_id == original.gaia_id
    assert before_revision.data.domains["debt"][0].value == "100"

    after_revision = temporal_fiscal_snapshot(
        session,
        jurisdiction_code="NG-LA",
        effective_as_of=effective_cutoff,
        known_as_of=datetime(2026, 8, 20, 0, 0, tzinfo=UTC),
    )
    assert after_revision is not None
    assert after_revision.data.claim_count == 1
    assert after_revision.data.domains["debt"][0].gaia_id == revised.gaia_id
    assert after_revision.data.domains["debt"][0].value == "120"
    assert after_revision.evidence["history_rewritten"] is False


def test_temporal_api_requires_timezone_aware_cutoffs(session):
    _setup_revisions(session)
    app.dependency_overrides[get_session] = lambda: session
    try:
        client = TestClient(app)
        response = client.get(
            "/api/v1/jurisdictions/LA/temporal-snapshot",
            params={
                "effective_as_of": "2026-06-30T23:59:00",
                "known_as_of": "2026-08-01T00:00:00Z",
            },
        )
        assert response.status_code == 422
        assert "timezone" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()
