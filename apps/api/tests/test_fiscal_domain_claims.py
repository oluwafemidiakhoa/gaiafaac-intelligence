from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import select

from gaiafaac_api.database.enums import EvidenceStatus, SourceStatus
from gaiafaac_api.database.ledger_models import EvidenceVerification, FiscalClaim, FiscalEvent
from gaiafaac_api.database.models import SourceDocument, State
from gaiafaac_api.database.seeds import seed_states
from gaiafaac_api.services.fiscal_domain_claims import publish_domain_claim
from gaiafaac_api.services.fiscal_ledger import publish_current_fiscal_state


def _source(session, *, sha: str, approved: bool = True):
    source = SourceDocument(
        source_organization="Official fiscal publisher",
        source_url="https://example.gov.ng/fiscal.pdf",
        original_filename="fiscal.pdf",
        storage_path=f"archive/{sha}.pdf",
        sha256=sha,
        mime_type="application/pdf",
        source_status=SourceStatus.APPROVED if approved else SourceStatus.REGISTERED,
        is_demo=False,
    )
    session.add(source)
    session.flush()
    return source


def _lagos(session):
    seed_states(session)
    state = session.scalar(select(State).where(State.code == "LA"))
    assert state is not None
    return state


def test_cross_domain_claims_enter_fiscal_state_without_inference(session):
    state = _lagos(session)
    source = _source(session, sha="b" * 64)
    observed_at = datetime(2026, 8, 21, 12, 0, tzinfo=UTC)

    debt_proof = publish_domain_claim(
        session,
        domain="debt",
        state_id=state.id,
        source_document_id=source.id,
        fiscal_period="2026Q2",
        metric="domestic_debt_stock",
        value=Decimal("123456789.00"),
        value_text="123456789.00",
        unit="naira",
        currency="NGN",
        effective_at=observed_at,
        published_at=observed_at,
        human_reviewed=True,
        reconciled=True,
    )
    service_proof = publish_domain_claim(
        session,
        domain="debt_service",
        state_id=state.id,
        source_document_id=source.id,
        fiscal_period="2026Q2",
        metric="debt_service",
        value=Decimal("12000000.00"),
        value_text="12000000.00",
        unit="naira",
        currency="NGN",
        effective_at=observed_at,
        published_at=observed_at,
        human_reviewed=True,
        reconciled=True,
    )
    session.commit()

    assert debt_proof.gaia_id.startswith("GF-DEBT-NG-LA-2026Q2-")
    assert service_proof.gaia_id.startswith("GF-DEBTSVC-NG-LA-2026Q2-")
    claims = session.scalars(select(FiscalClaim).where(FiscalClaim.state_id == state.id)).all()
    assert {claim.object_type for claim in claims} == {"debt", "debt_service"}
    assert all(claim.evidence_status is EvidenceStatus.VERIFIED for claim in claims)

    fiscal_state = publish_current_fiscal_state(
        session,
        state_id=state.id,
        effective_at=observed_at,
        fiscal_period="2026Q2",
    )
    assert fiscal_state.domains["debt"]["status"] == "verified"
    assert fiscal_state.domains["debt_service"]["status"] == "verified"
    assert fiscal_state.domains["budget"]["status"] == "unavailable"
    assert fiscal_state.domains["budget"]["claims"] == []


def test_unapproved_source_fails_closed_to_partial(session):
    state = _lagos(session)
    source = _source(session, sha="c" * 64, approved=False)
    observed_at = datetime(2026, 8, 21, 12, 0, tzinfo=UTC)
    proof = publish_domain_claim(
        session,
        domain="budget",
        state_id=state.id,
        source_document_id=source.id,
        fiscal_period="2026",
        metric="approved_budget",
        value=Decimal("500000000.00"),
        value_text=None,
        unit="naira",
        currency="NGN",
        effective_at=observed_at,
        published_at=observed_at,
        human_reviewed=True,
        reconciled=True,
    )
    session.flush()
    verification = session.scalar(
        select(EvidenceVerification).where(EvidenceVerification.claim_gaia_id == proof.gaia_id)
    )
    assert verification is not None
    assert verification.status is EvidenceStatus.PARTIAL


def test_revision_preserves_old_claim_and_emits_supersession_event(session):
    state = _lagos(session)
    first = _source(session, sha="d" * 64)
    second = _source(session, sha="e" * 64)
    second.supersedes_document_id = first.id
    observed_at = datetime(2026, 8, 21, 12, 0, tzinfo=UTC)
    revised_at = datetime(2026, 8, 22, 12, 0, tzinfo=UTC)

    original = publish_domain_claim(
        session,
        domain="liabilities",
        state_id=state.id,
        source_document_id=first.id,
        fiscal_period="2026Q2",
        metric="total_liabilities",
        value=Decimal("100.00"),
        value_text="100.00",
        unit="naira",
        currency="NGN",
        effective_at=observed_at,
        published_at=observed_at,
        human_reviewed=True,
        reconciled=True,
    )
    revised = publish_domain_claim(
        session,
        domain="liabilities",
        state_id=state.id,
        source_document_id=second.id,
        fiscal_period="2026Q2",
        metric="total_liabilities",
        value=Decimal("120.00"),
        value_text="120.00",
        unit="naira",
        currency="NGN",
        effective_at=observed_at,
        published_at=revised_at,
        human_reviewed=True,
        reconciled=True,
    )
    session.commit()

    original_claim = session.get(FiscalClaim, original.gaia_id)
    revised_claim = session.get(FiscalClaim, revised.gaia_id)
    assert original_claim is not None
    assert revised_claim is not None
    assert revised_claim.supersedes_gaia_id == original_claim.gaia_id
    events = session.scalars(
        select(FiscalEvent).where(FiscalEvent.event_type == "claim_superseded")
    ).all()
    assert events
    assert revised.gaia_id in events[-1].evidence_ids


def test_missing_observed_value_is_rejected(session):
    state = _lagos(session)
    source = _source(session, sha="f" * 64)
    observed_at = datetime(2026, 8, 21, 12, 0, tzinfo=UTC)
    with pytest.raises(ValueError, match="observed value"):
        publish_domain_claim(
            session,
            domain="expenditure",
            state_id=state.id,
            source_document_id=source.id,
            fiscal_period="2026Q2",
            metric="capital_expenditure",
            value=None,
            value_text=None,
            unit="naira",
            currency="NGN",
            effective_at=observed_at,
            published_at=observed_at,
        )
