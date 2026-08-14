from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.api.v1.routes.fiscal_ledger import (
    evidence_source_registry,
    fiscal_certificate_by_id,
    fiscal_event_stream,
    fiscal_proof_by_id,
    fiscal_state_by_id,
    jurisdiction_fiscal_state,
    verify_fiscal_artifact,
)
from gaiafaac_api.database.enums import (
    FiscalEventSeverity,
    ReportedUnit,
    SourceStatus,
    VerificationStatus,
)
from gaiafaac_api.database.models import ReportingPeriod, SourceDocument, State, StateAllocation
from gaiafaac_api.database.seeds import seed_states
from gaiafaac_api.fiscal_ledger_schemas import EvidenceManifestResponse
from gaiafaac_api.ledger import canonical_sha256
from gaiafaac_api.services.fiscal_institutional import (
    fiscal_events,
    get_fiscal_certificate,
    publish_fiscal_certificate,
)
from gaiafaac_api.services.fiscal_ledger import (
    get_fiscal_proof_by_gaia_id,
    get_jurisdiction_fiscal_state,
    publish_faac_claim_proof,
    publish_fiscal_state,
)
from gaiafaac_api.services.fiscal_trust import record_evidence_conflict


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
    assert proof.gaia_id == "GF-FAAC-NG-LA-202606-FF3373"
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
    duplicate_state = publish_fiscal_state(
        session,
        jurisdiction_code="NG-LA",
        effective_at=datetime(2026, 8, 14, tzinfo=UTC),
        fiscal_period="2026-YTD",
        claim_gaia_ids=[proof.gaia_id],
    )
    state_detail = get_jurisdiction_fiscal_state(session, jurisdiction_code="NG-LA")

    assert fiscal_state.fiscal_state_id.startswith("GFS-NG-LA-20260814-")
    assert duplicate_state.fiscal_state_id == fiscal_state.fiscal_state_id
    assert state_detail is not None
    assert state_detail.data.jurisdiction.name == state.name
    assert state_detail.data.domains["faac"]["status"] == "verified"
    assert state_detail.data.domains["debt"] == {"status": "unavailable", "claims": []}
    assert state_detail.data.evidence_coverage == "0.1429"
    assert state_detail.data.evidence_coverage_status == "calculated"
    assert state_detail.data.evidence_integrity["status"] == "calculated"
    assert state_detail.data.evidence_integrity["score"] == "74.57"
    assert state_detail.data.evidence_integrity["components"]["cross_source_agreement"] == {
        "score": None,
        "status": "insufficient_evidence",
    }


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
    assert proof_response.meta.methodology_version == "1.0.0"
    assert state_response.data.evidence_coverage == "0.1429"
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


def _revised_allocation(
    session: Session,
    *,
    state: State,
    previous_source_id,
) -> StateAllocation:
    published_at = datetime(2026, 8, 16, 9, 0, tzinfo=UTC)
    period = ReportingPeriod(
        revenue_month=date(2026, 6, 1),
        faac_meeting_date=date(2026, 7, 20),
        publication_date=date(2026, 8, 15),
        reporting_label="June 2026 revised allocation",
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
        source_url="https://example.gov.ng/june-2026-revised.pdf",
        original_filename="june-2026-revised.pdf",
        storage_path="source/june-2026-revised.pdf",
        sha256="b" * 64,
        mime_type="application/pdf",
        publication_date=date(2026, 8, 15),
        source_status=SourceStatus.APPROVED,
        supersedes_document_id=previous_source_id,
        is_demo=False,
    )
    session.add(source)
    session.flush()
    allocation = StateAllocation(
        reporting_period_id=period.id,
        state_id=state.id,
        source_document_id=source.id,
        gross_total=Decimal("73500000000.00"),
        total_deductions=Decimal("9651611633.23"),
        net_allocation=Decimal("63848388366.77"),
        reported_unit=ReportedUnit.NAIRA,
        verification_status=VerificationStatus.HUMAN_VERIFIED,
        reviewed_at=published_at,
        is_demo=False,
        is_published=True,
        published_at=published_at,
    )
    session.add(allocation)
    session.flush()
    return allocation


def test_revision_and_source_registry_preserve_both_versions(session: Session) -> None:
    state, allocation = _published_allocation(session)
    original = publish_faac_claim_proof(session, allocation_id=allocation.id)
    revised_allocation = _revised_allocation(
        session,
        state=state,
        previous_source_id=allocation.source_document_id,
    )
    revised = publish_faac_claim_proof(session, allocation_id=revised_allocation.id)
    session.commit()

    original_detail = get_fiscal_proof_by_gaia_id(session, original.gaia_id)
    revised_detail = get_fiscal_proof_by_gaia_id(session, revised.gaia_id)
    registry = evidence_source_registry(session, "NG-LA", None, "faac")

    assert original.gaia_id != revised.gaia_id
    assert original_detail is not None
    assert revised_detail is not None
    assert original_detail.data.superseded_by_gaia_id == revised.gaia_id
    assert revised_detail.data.supersedes_gaia_id == original.gaia_id
    assert len(revised_detail.evidence.revisions) == 1
    revision = revised_detail.evidence.revisions[0]
    assert revision.value_delta == "3500000000.00"
    assert revision.value_change_percent == "5.799658"
    assert revision.material_change is True
    assert revision.source_revision is True
    assert len(registry.data) == 2
    assert registry.data[0].revision_detected is False
    assert registry.data[1].revision_detected is True
    assert registry.data[1].supersedes_source_id == registry.data[0].source_id
    assert [entry.entry_type for entry in original_detail.evidence.history] == [
        "human_verified",
        "published",
        "claim_superseded",
        "source_revised",
    ]


def test_explicit_conflict_is_retained_without_silently_selecting_a_value(
    session: Session,
) -> None:
    state, allocation = _published_allocation(session)
    original = publish_faac_claim_proof(session, allocation_id=allocation.id)
    revised_allocation = _revised_allocation(
        session,
        state=state,
        previous_source_id=allocation.source_document_id,
    )
    revised = publish_faac_claim_proof(session, allocation_id=revised_allocation.id)
    conflict = record_evidence_conflict(
        session,
        claim_gaia_ids=[original.gaia_id, revised.gaia_id],
        explanation="Two retained authoritative source documents report different values.",
        detected_at=datetime(2026, 8, 16, 10, 0, tzinfo=UTC),
    )
    fiscal_state = publish_fiscal_state(
        session,
        jurisdiction_code="NG-LA",
        effective_at=datetime(2026, 8, 16, 12, 0, tzinfo=UTC),
        fiscal_period="2026-YTD",
        claim_gaia_ids=[original.gaia_id, revised.gaia_id],
    )
    detail = get_jurisdiction_fiscal_state(session, jurisdiction_code="NG-LA")

    assert conflict.conflict_id.startswith("GFC-NG-LA-202606-")
    assert detail is not None
    assert detail.data.ledger_status.value == "conflicting"
    assert detail.data.domains["faac"]["status"] == "conflicting"
    assert len(detail.evidence.conflicts) == 1
    assert len(detail.evidence.conflicts[0].participants) == 2
    assert detail.data.evidence_integrity["components"]["cross_source_agreement"] == {
        "score": "0.00",
        "status": "calculated",
    }
    assert fiscal_state.integrity_hash == canonical_sha256(detail.evidence.manifest.payload)


def test_date_as_of_query_is_inclusive_and_returns_historical_state(session: Session) -> None:
    _state, allocation = _published_allocation(session)
    proof = publish_faac_claim_proof(session, allocation_id=allocation.id)
    first = publish_fiscal_state(
        session,
        jurisdiction_code="NG-LA",
        effective_at=datetime(2026, 8, 14, 10, 0, tzinfo=UTC),
        fiscal_period="2026-YTD",
        claim_gaia_ids=[proof.gaia_id],
    )
    second = publish_fiscal_state(
        session,
        jurisdiction_code="NG-LA",
        effective_at=datetime(2026, 8, 15, 10, 0, tzinfo=UTC),
        fiscal_period="2026-YTD",
        claim_gaia_ids=[proof.gaia_id],
    )

    historical = get_jurisdiction_fiscal_state(
        session, jurisdiction_code="NG-LA", as_of=date(2026, 8, 14)
    )

    assert historical is not None
    assert historical.data.fiscal_state_id == first.fiscal_state_id
    assert second.previous_state_id == first.fiscal_state_id


def test_lifecycle_events_are_deterministic_filterable_and_non_causal(
    session: Session,
) -> None:
    state, allocation = _published_allocation(session)
    original = publish_faac_claim_proof(session, allocation_id=allocation.id)
    revised_allocation = _revised_allocation(
        session,
        state=state,
        previous_source_id=allocation.source_document_id,
    )
    revised = publish_faac_claim_proof(session, allocation_id=revised_allocation.id)
    publish_fiscal_state(
        session,
        jurisdiction_code="NG-LA",
        effective_at=datetime(2026, 8, 16, 12, 0, tzinfo=UTC),
        fiscal_period="2026-YTD",
        claim_gaia_ids=[revised.gaia_id],
    )

    result = fiscal_events(
        session,
        jurisdiction_code="NG-LA",
        event_type="claim_superseded",
        severity=FiscalEventSeverity.MATERIAL,
    )
    api_result = fiscal_event_stream(
        session,
        "NG-LA",
        "claim_superseded",
        FiscalEventSeverity.MATERIAL,
        None,
        date(2026, 8, 16),
        date(2026, 8, 16),
        100,
    )

    assert result.evidence.record_count == 1
    event = result.data[0]
    assert event.event_id.startswith("GFE-NG-LA-20260816-")
    assert event.evidence_ids == sorted([original.gaia_id, revised.gaia_id])
    assert event.calculation["value_change_percent"] == "5.799658"
    assert "caus" not in event.explanation.lower()
    assert api_result.data[0].event_id == event.event_id
    assert "do not infer cause" in result.evidence.meaning


def test_fiscal_certificate_is_immutable_reproducible_and_links_proofs(
    session: Session,
) -> None:
    _state, allocation = _published_allocation(session)
    proof = publish_faac_claim_proof(session, allocation_id=allocation.id)
    fiscal_state = publish_fiscal_state(
        session,
        jurisdiction_code="NG-LA",
        effective_at=datetime(2026, 8, 14, tzinfo=UTC),
        fiscal_period="2026-YTD",
        claim_gaia_ids=[proof.gaia_id],
    )
    issued_at = datetime(2026, 8, 14, 12, 0, tzinfo=UTC)
    certificate = publish_fiscal_certificate(
        session,
        fiscal_state_id=fiscal_state.fiscal_state_id,
        fiscal_period="2026H1",
        issued_at=issued_at,
    )
    duplicate = publish_fiscal_certificate(
        session,
        fiscal_state_id=fiscal_state.fiscal_state_id,
        fiscal_period="2026H1",
        issued_at=issued_at,
    )
    detail = get_fiscal_certificate(session, certificate.gaia_id)
    api_detail = fiscal_certificate_by_id(certificate.gaia_id, session)

    assert duplicate.gaia_id == certificate.gaia_id
    assert certificate.gaia_id.startswith("GF-CERT-NG-LA-2026H1-")
    assert detail is not None
    assert detail.data.proof_gaia_ids == [proof.gaia_id]
    assert detail.data.verified_domains == ["faac"]
    assert "debt" in detail.data.unavailable_domains
    assert detail.data.evidence_integrity["score"] == "74.57"
    assert canonical_sha256(detail.evidence.manifest.payload) == certificate.integrity_hash
    assert api_detail.data.gaia_id == certificate.gaia_id
    verified = verify_fiscal_artifact(detail.evidence.manifest)
    assert verified.status == "verified"
