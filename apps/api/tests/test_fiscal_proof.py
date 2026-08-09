from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import select

from gaiafaac_api.database.enums import ReportedUnit, SourceStatus, VerificationStatus
from gaiafaac_api.database.models import ReportingPeriod, SourceDocument, State, StateAllocation
from gaiafaac_api.database.seeds import seed_states
from gaiafaac_api.services.fiscal_proof import get_fiscal_proof


def _published_record(session):
    seed_states(session)
    state = session.scalars(select(State).where(State.is_fct.is_(False))).first()
    assert state is not None
    reviewed_at = datetime(2026, 8, 9, tzinfo=UTC)
    period = ReportingPeriod(
        revenue_month=date(2024, 1, 1),
        reporting_label="January 2024 allocation",
        is_demo=False,
        is_published=True,
        published_at=reviewed_at,
        verification_status=VerificationStatus.HUMAN_VERIFIED,
        source_status=SourceStatus.APPROVED,
    )
    session.add(period)
    session.flush()
    source = SourceDocument(
        reporting_period_id=period.id,
        source_organization="OAGF",
        source_url="https://example.gov.ng/january-2024.pdf",
        original_filename="january-2024.pdf",
        storage_path="source/january-2024.pdf",
        sha256="a" * 64,
        mime_type="application/pdf",
        document_version="1",
        source_status=SourceStatus.APPROVED,
        is_demo=False,
    )
    session.add(source)
    session.flush()
    allocation = StateAllocation(
        reporting_period_id=period.id,
        state_id=state.id,
        source_document_id=source.id,
        gross_total=Decimal("120.00"),
        total_deductions=Decimal("20.00"),
        net_allocation=Decimal("100.00"),
        reported_unit=ReportedUnit.NAIRA,
        verification_status=VerificationStatus.HUMAN_VERIFIED,
        reviewed_at=reviewed_at,
        is_demo=False,
        is_published=True,
        published_at=reviewed_at,
    )
    session.add(allocation)
    session.flush()
    return state


def test_fiscal_proof_is_deterministic_and_reconciled(session):
    state = _published_record(session)
    first = get_fiscal_proof(session, state_slug=state.slug, revenue_month=date(2024, 1, 1))
    second = get_fiscal_proof(session, state_slug=state.slug, revenue_month=date(2024, 1, 1))

    assert first is not None
    assert second is not None
    assert first.proof_id == second.proof_id
    assert first.proof_digest_sha256 == second.proof_digest_sha256
    assert first.proof_id.startswith(f"GF1-NG-{state.code}-202401-")
    assert first.financials.reconciliation_status == "reconciled"
    assert first.financials.reconciliation_delta == "0.00"
    assert first.verification.human_verified is True
    assert first.source.sha256 == "a" * 64


def test_fiscal_proof_excludes_unpublished_records(session):
    state = _published_record(session)
    allocation = session.scalars(select(StateAllocation)).one()
    allocation.is_published = False
    session.flush()

    proof = get_fiscal_proof(session, state_slug=state.slug, revenue_month=date(2024, 1, 1))
    assert proof is None


def test_fiscal_proof_allows_net_only_record_without_inventing_reconciliation(session):
    state = _published_record(session)
    allocation = session.scalars(select(StateAllocation)).one()
    allocation.gross_total = None
    allocation.total_deductions = None
    session.flush()

    proof = get_fiscal_proof(session, state_slug=state.slug, revenue_month=date(2024, 1, 1))
    assert proof is not None
    assert proof.financials.gross_total is None
    assert proof.financials.total_deductions is None
    assert proof.financials.reconciliation_status == "not_applicable"
    assert proof.financials.reconciliation_delta is None
