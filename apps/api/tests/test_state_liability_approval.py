from decimal import Decimal

import pytest
from sqlalchemy import select

from gaiafaac_api.database.enums import (
    ProcessingStatus,
    SourceStatus,
    UserRole,
    VerificationStatus,
)
from gaiafaac_api.database.ledger_models import FiscalClaim
from gaiafaac_api.database.liability_models import LiabilityMetric, StateLiabilityRecord
from gaiafaac_api.database.models import SourceDocument, State, User
from gaiafaac_api.pipeline.errors import ApprovalError
from gaiafaac_api.pipeline.state_financials.approval import approve_state_liability_source

_AMOUNTS: dict[LiabilityMetric, tuple[Decimal | None, str]] = {
    LiabilityMetric.CONTRACTOR_ARREARS: (Decimal("4338068360.63"), "4,338,068,360.63"),
    LiabilityMetric.PENSIONS_AND_GRATUITY_ARREARS: (
        Decimal("29935642098.27"),
        "29,935,642,098.27",
    ),
    LiabilityMetric.SALARY_ARREARS: (None, "-"),
    LiabilityMetric.OTHER_JUDGMENT_ARREARS: (Decimal("106468643.85"), "106,468,643.85"),
    LiabilityMetric.TOTAL_DOMESTIC_ARREARS: (
        Decimal("34380179102.75"),
        "34,380,179,102.75",
    ),
}


def _reviewer(session, *, role: UserRole = UserRole.REVIEWER, active: bool = True) -> User:
    reviewer = User(
        email=f"liability-{role.value}-{active}@example.com",
        full_name="Liability Reviewer",
        role=role,
        is_active=active,
    )
    session.add(reviewer)
    session.flush()
    return reviewer


def _staged_source(session, *, omit_metric: LiabilityMetric | None = None):
    state = State(
        name="Oyo",
        code="OY",
        slug="oyo",
        geopolitical_zone="South West",
        capital="Ibadan",
        is_fct=False,
    )
    session.add(state)
    session.flush()
    source = SourceDocument(
        source_organization="Oyo State Government",
        source_url="https://finance.oyostate.gov.ng/example-arrears-2021.pdf",
        original_filename="oyo-contractor-arrears-2021.pdf",
        storage_path="/tmp/oyo-contractor-arrears-2021.pdf",
        sha256="f" * 64,
        mime_type="application/pdf",
        processing_status=ProcessingStatus.READY_FOR_REVIEW,
        source_status=SourceStatus.READY_FOR_REVIEW,
        document_version="state-financial-contractor-arrears-register-oy-2021",
        is_demo=False,
    )
    session.add(source)
    session.flush()
    for metric in LiabilityMetric:
        if metric is omit_metric:
            continue
        amount, amount_text = _AMOUNTS[metric]
        session.add(
            StateLiabilityRecord(
                state_id=state.id,
                source_document_id=source.id,
                fiscal_year=2021,
                metric=metric,
                amount=amount,
                amount_text=amount_text,
                currency="NGN",
                source_page=15,
                source_table="Oyo State 2021 Contractor and Domestic Arrears Summary",
                extraction_method="oyo_contractor_arrears_pdf_summary_v1",
                verification_status=VerificationStatus.REQUIRES_REVIEW,
                is_demo=False,
                is_published=False,
            )
        )
    session.commit()
    return state, source


def test_liability_approval_requires_active_reviewer_or_administrator(session):
    viewer = _reviewer(session, role=UserRole.VIEWER)
    _state, source = _staged_source(session)

    with pytest.raises(ApprovalError, match="active reviewer or administrator"):
        approve_state_liability_source(
            session,
            source_document_id=source.id,
            reviewer_id=viewer.id,
        )


def test_liability_approval_requires_complete_metric_set(session):
    reviewer = _reviewer(session)
    _state, source = _staged_source(session, omit_metric=LiabilityMetric.OTHER_JUDGMENT_ARREARS)

    with pytest.raises(ApprovalError, match="complete governed metric set"):
        approve_state_liability_source(
            session,
            source_document_id=source.id,
            reviewer_id=reviewer.id,
        )


def test_liability_approval_preserves_unreported_salary_and_publishes_nothing(session):
    reviewer = _reviewer(session)
    _state, source = _staged_source(session)

    result = approve_state_liability_source(
        session,
        source_document_id=source.id,
        reviewer_id=reviewer.id,
    )
    records = list(
        session.scalars(
            select(StateLiabilityRecord).where(StateLiabilityRecord.source_document_id == source.id)
        )
    )
    salary = next(record for record in records if record.metric is LiabilityMetric.SALARY_ARREARS)

    assert result.records_approved == len(LiabilityMetric)
    assert result.numeric_metrics == 4
    assert result.unreported_metrics == 1
    assert result.reconciliation_checked is True
    assert result.published is False
    assert source.source_status is SourceStatus.APPROVED
    assert source.processing_status is ProcessingStatus.COMPLETED
    assert salary.amount is None
    assert salary.amount_text == "-"
    assert all(
        record.verification_status is VerificationStatus.HUMAN_VERIFIED for record in records
    )
    assert all(record.reviewed_by == reviewer.id for record in records)
    assert all(record.reviewed_at is not None for record in records)
    assert all(not record.is_published for record in records)
    assert (
        session.scalar(
            select(FiscalClaim.gaia_id).where(FiscalClaim.source_document_id == source.id)
        )
        is None
    )


def test_liability_approval_rechecks_arithmetic_reconciliation(session):
    reviewer = _reviewer(session)
    _state, source = _staged_source(session)
    total = session.scalar(
        select(StateLiabilityRecord).where(
            StateLiabilityRecord.source_document_id == source.id,
            StateLiabilityRecord.metric == LiabilityMetric.TOTAL_DOMESTIC_ARREARS,
        )
    )
    assert total is not None
    total.amount = Decimal("34380179102.76")
    session.commit()

    with pytest.raises(ApprovalError, match="reconciliation failed"):
        approve_state_liability_source(
            session,
            source_document_id=source.id,
            reviewer_id=reviewer.id,
        )


def test_liability_approval_rejects_mutated_salary_dash_semantics(session):
    reviewer = _reviewer(session)
    _state, source = _staged_source(session)
    salary = session.scalar(
        select(StateLiabilityRecord).where(
            StateLiabilityRecord.source_document_id == source.id,
            StateLiabilityRecord.metric == LiabilityMetric.SALARY_ARREARS,
        )
    )
    assert salary is not None
    salary.amount = Decimal("0.00")
    salary.amount_text = "0.00"
    session.commit()

    with pytest.raises(ApprovalError, match="must remain unreported"):
        approve_state_liability_source(
            session,
            source_document_id=source.id,
            reviewer_id=reviewer.id,
        )


def test_liability_reapproval_is_idempotent_and_does_not_publish(session):
    reviewer = _reviewer(session)
    _state, source = _staged_source(session)
    first = approve_state_liability_source(
        session,
        source_document_id=source.id,
        reviewer_id=reviewer.id,
    )
    second = approve_state_liability_source(
        session,
        source_document_id=source.id,
        reviewer_id=reviewer.id,
    )

    assert first.records_approved == second.records_approved == len(LiabilityMetric)
    assert second.numeric_metrics == 4
    assert second.unreported_metrics == 1
    assert second.published is False
    assert (
        session.scalar(
            select(FiscalClaim.gaia_id).where(FiscalClaim.source_document_id == source.id)
        )
        is None
    )
