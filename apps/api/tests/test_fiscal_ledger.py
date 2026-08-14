from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.api.v1.routes.fiscal_ledger import (
    fiscal_proof_by_id,
    fiscal_state_by_id,
    jurisdiction_fiscal_state,
    verify_fiscal_artifact,
)
from gaiafaac_api.database.enums import ReportedUnit, SourceStatus, VerificationStatus
from gaiafaac_api.database.models import ReportingPeriod, SourceDocument, State, StateAllocation
from gaiafaac_api.database.seeds import seed_states
from gaiafaac_api.fiscal_ledger_schemas import EvidenceManifestResponse
from gaiafaac_api.ledger import canonical_sha256
from gaiafaac_api.services.fiscal_ledger import (
    get_fiscal_proof_by_gaia_id,
    get_jurisdiction_fiscal_state,
    publish_faac_claim_proof,
    publish_fiscal_state,
)


def _published_allocation(session: Session) -> tuple[State, StateAllocation]:
    seed_states(session)
    state = session.scalar(select(State).where(State.code == "LA"))
    assert state is not None
    published_at = datetime(2026, 8, 14, 10, 30, tzinfo=UTC)
    period = ReportingPeriod(
        revenue_month=date(2026, 6, 1),
        faac_meeting_date=date(2026, 7, 20),
        publication_date=date(2026, 7, 22),
        reporting_label="June 2026 allocation",
        is_demo=False,
        is_published=True,
        published_at=published_at,
        verification_status=VerificationStatus.HUMAN_VERIFIED,
        source_status=SourceStatus.APPROVED,
    )
    session.add(period)
    session.flush()
    source = SourceDocument(
        reporting_period_id=period.id,
        source_organization="OAGF",
        source_url="https://example.gov.ng/june-2026.pdf",
        original_filename="june-2026.pdf",
        storage_path="source/june-2026.pdf",
        sha256="a" * 64,
        mime_type="application/pdf",
        publication_date=date(2026, 7, 22),
        source_status=SourceStatus.APPROVED,
        is_demo=False,
    )
    session.add(source)
    session.flush()
    allocation = StateAllocation(
        reporting_period_id=period.id,
        state_id=state.id,
        source_document_id=source.id,
        gross_total=Decimal("70000000000.00"),
        total_deductions=Decimal("9651611633.23"),
        net_allocation=Decimal("60348388366.77"),
        reported_unit=ReportedUnit.NAIRA,
        verification_status=VerificationStatus.HUMAN_VERIFIED,
        reviewed_at=published_at,
        is_demo=False,
        is_published=True,
        published_at=published_at,
    )
    session.add(allocation)
    session.flush()
    return state, allocation


def test_proof_and_fiscal_state_are_deterministic_and_do_not_infer_gaps(session: Session) -> None:
    state, allocation = _published_allocation(session)
    proof = publish_faac_claim_proof(session, allocation_id=allocation.id)
    duplicate = publish_faac_claim_proof(session, allocation_id=allocation.id)
    detail = get_fiscal_proof_by_gaia_id(session, proof.gaia_id)

    assert duplicate.id == proof.id
    assert proof.gaia_id.startswith("GF-FAAC-NG-LA-202606-")
    assert detail is not None
    assert detail.data.value == "60348388366.77"
    assert detail.data.verification.source_verified is True
    assert detail.data.verification.reconciled is True
    assert detail.data.verification.human_reviewed is True
    assert canonical_sha256(detail.evidence.manifest.payload) == proof.integrity_hash

    fiscal_state = publish_fiscal_state(
        session,
        jurisdiction_code="NG-LA",
        effective_at=datetime(2026, 8, 14, tzinfo=UTC),
        fiscal_period="2026-YTD",
        claim_gaia_ids=[proof.gaia_id],
    )
    state_detail = get_jurisdiction_fiscal_state(session, jurisdiction_code="NG-LA")

    assert fiscal_state.fiscal_state_id.startswith("GFS-NG-LA-20260814-")
    assert state_detail is not None
    assert state_detail.data.jurisdiction.name == state.name
    assert state_detail.data.domains["faac"]["status"] == "verified"
    assert state_detail.data.domains["debt"] == {"status": "unavailable", "claims": []}
    assert state_detail.data.evidence_coverage is None
    assert state_detail.data.evidence_coverage_status == "insufficient_evidence"
    assert state_detail.data.evidence_integrity["score"] is None


def test_published_ledger_objects_are_immutable(session: Session) -> None:
    _state, allocation = _published_allocation(session)
    proof = publish_faac_claim_proof(session, allocation_id=allocation.id)
    proof.schema_version = "changed"

    with pytest.raises(ValueError, match="immutable"):
        session.flush()


def test_fiscal_ledger_api_exposes_proof_and_state_by_gaia_id(session: Session) -> None:
    _state, allocation = _published_allocation(session)
    proof = publish_faac_claim_proof(session, allocation_id=allocation.id)
    fiscal_state = publish_fiscal_state(
        session,
        jurisdiction_code="NG-LA",
        effective_at=datetime(2026, 8, 14, tzinfo=UTC),
        fiscal_period="2026-YTD",
        claim_gaia_ids=[proof.gaia_id],
    )

    proof_response = fiscal_proof_by_id(proof.gaia_id, session)
    state_response = jurisdiction_fiscal_state("NG-LA", session, None)
    historical_response = fiscal_state_by_id(fiscal_state.fiscal_state_id, session)

    assert proof_response.data.gaia_id == proof.gaia_id
    assert proof_response.meta.schema_version == "1.0.0"
    assert state_response.data.evidence_coverage is None
    assert historical_response.data.fiscal_state_id == fiscal_state.fiscal_state_id


def test_cli_friendly_verifier_distinguishes_integrity_from_recorded_workflow(
    session: Session,
) -> None:
    _state, allocation = _published_allocation(session)
    proof = publish_faac_claim_proof(session, allocation_id=allocation.id)
    detail = get_fiscal_proof_by_gaia_id(session, proof.gaia_id)
    assert detail is not None

    result = verify_fiscal_artifact(detail.evidence.manifest)

    assert result.status == "verified"
    assert result.artifact_integrity == "verified"
    assert result.source_provenance_recorded is True
    assert result.reconciliation_recorded is True
    assert "do not independently prove" in result.meaning

    tampered = detail.evidence.manifest.model_copy(deep=True)
    tampered.payload["value"] = "0.00"
    mismatch = verify_fiscal_artifact(
        EvidenceManifestResponse.model_validate(tampered.model_dump())
    )
    assert mismatch.status == "mismatch"
