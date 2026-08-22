from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import select

from gaiafaac_api.database.budget_models import (
    BudgetPerformanceMetric,
    StateBudgetPerformanceRecord,
)
from gaiafaac_api.database.enums import (
    ProcessingStatus,
    SourceStatus,
    UserRole,
    VerificationStatus,
)
from gaiafaac_api.database.ledger_models import FiscalClaim
from gaiafaac_api.database.models import SourceDocument, State, User
from gaiafaac_api.pipeline.errors import ApprovalError
from gaiafaac_api.pipeline.state_budget.performance_approval import (
    PUBLISHABLE_EXPENDITURE_METRICS,
    approve_budget_performance_source,
    publish_budget_performance_source,
)
from gaiafaac_api.services.fiscal_domain_claims import publish_domain_claim


def _reviewer(session) -> User:
    reviewer = User(
        email="performance-reviewer@example.com",
        full_name="Performance Reviewer",
        role=UserRole.REVIEWER,
        is_active=True,
    )
    session.add(reviewer)
    session.flush()
    return reviewer


def _staged_source(
    session,
    *,
    omit_metric: BudgetPerformanceMetric | None = None,
):
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
        source_url="https://budget.oyostate.gov.ng/example-q2-performance.pdf",
        original_filename="oyo-2026-q2-budget-performance.pdf",
        storage_path="/tmp/oyo-2026-q2-budget-performance.pdf",
        sha256="d" * 64,
        mime_type="application/pdf",
        processing_status=ProcessingStatus.READY_FOR_REVIEW,
        source_status=SourceStatus.READY_FOR_REVIEW,
        document_version="budget-performance-oy-2026-q2",
        is_demo=False,
    )
    session.add(source)
    session.flush()
    for index, metric in enumerate(BudgetPerformanceMetric, start=1):
        if metric is omit_metric:
            continue
        original = Decimal(index * 1_000_000)
        ytd = original / Decimal("4")
        quarter = original / Decimal("8")
        balance = original - ytd
        session.add(
            StateBudgetPerformanceRecord(
                state_id=state.id,
                source_document_id=source.id,
                fiscal_year=2026,
                quarter=2,
                metric=metric,
                original_budget=original,
                original_budget_text=f"{original:.2f}",
                quarter_actual=quarter,
                quarter_actual_text=f"{quarter:.2f}",
                ytd_actual=ytd,
                ytd_actual_text=f"{ytd:.2f}",
                performance_percent=Decimal("25.0"),
                performance_percent_text="25.0%",
                balance=balance,
                balance_text=f"{balance:.2f}",
                currency="NGN",
                source_page=7,
                source_table="Table 1: Budget Implementation Summary",
                extraction_method="oyo_budget_performance_pdf_table1_v1",
                verification_status=VerificationStatus.REQUIRES_REVIEW,
                is_demo=False,
                is_published=False,
            )
        )
    session.commit()
    return state, source


def _governed_budget_claim(
    session,
    *,
    state: State,
    metric: str,
    value: Decimal,
) -> None:
    source = SourceDocument(
        source_organization="Oyo State Government",
        source_url="https://budget.oyostate.gov.ng/example-approved-budget.pdf",
        original_filename="oyo-2026-approved-budget.pdf",
        storage_path="/tmp/oyo-2026-approved-budget.pdf",
        sha256="e" * 64,
        mime_type="application/pdf",
        processing_status=ProcessingStatus.COMPLETED,
        source_status=SourceStatus.APPROVED,
        document_version="approved-budget-oy-2026",
        is_demo=False,
    )
    session.add(source)
    session.flush()
    publish_domain_claim(
        session,
        domain="budget",
        state_id=state.id,
        source_document_id=source.id,
        fiscal_period="2026",
        metric=metric,
        value=value,
        value_text=f"{value:.2f}",
        unit="currency",
        currency="NGN",
        effective_at=datetime(2026, 1, 1, tzinfo=UTC),
        published_at=datetime(2026, 1, 2, tzinfo=UTC),
        source_page=1,
        source_table="Approved Budget Summary",
        extraction_method="test_budget_claim",
        human_reviewed=True,
        reconciled=True,
    )
    session.commit()


def test_performance_approval_requires_complete_metric_set(session):
    reviewer = _reviewer(session)
    _state, source = _staged_source(
        session,
        omit_metric=BudgetPerformanceMetric.TOTAL_EXPENDITURE,
    )

    with pytest.raises(ApprovalError, match="complete governed metric set"):
        approve_budget_performance_source(
            session,
            source_document_id=source.id,
            reviewer_id=reviewer.id,
        )


def test_performance_approval_human_verifies_without_publishing(session):
    reviewer = _reviewer(session)
    _state, source = _staged_source(session)

    result = approve_budget_performance_source(
        session,
        source_document_id=source.id,
        reviewer_id=reviewer.id,
    )
    records = list(
        session.scalars(
            select(StateBudgetPerformanceRecord).where(
                StateBudgetPerformanceRecord.source_document_id == source.id
            )
        )
    )

    assert result.records_affected == len(BudgetPerformanceMetric)
    assert result.claims_published == 0
    assert result.published is False
    assert source.source_status is SourceStatus.APPROVED
    assert source.processing_status is ProcessingStatus.COMPLETED
    assert all(
        record.verification_status is VerificationStatus.HUMAN_VERIFIED
        for record in records
    )
    assert all(not record.is_published for record in records)
    assert (
        session.scalar(
            select(FiscalClaim.gaia_id).where(FiscalClaim.source_document_id == source.id)
        )
        is None
    )


def test_performance_approval_rejects_governed_budget_conflict(session):
    reviewer = _reviewer(session)
    state, source = _staged_source(session)
    total = session.scalar(
        select(StateBudgetPerformanceRecord.original_budget).where(
            StateBudgetPerformanceRecord.source_document_id == source.id,
            StateBudgetPerformanceRecord.metric == BudgetPerformanceMetric.TOTAL_EXPENDITURE,
        )
    )
    assert total is not None
    _governed_budget_claim(
        session,
        state=state,
        metric="total_expenditure",
        value=Decimal(total) + Decimal("1.00"),
    )

    with pytest.raises(ApprovalError, match="conflicts with the governed annual budget claim"):
        approve_budget_performance_source(
            session,
            source_document_id=source.id,
            reviewer_id=reviewer.id,
        )


def test_performance_publication_requires_prior_approval(session):
    reviewer = _reviewer(session)
    _state, source = _staged_source(session)

    with pytest.raises(ApprovalError, match="Only approved budget-performance sources"):
        publish_budget_performance_source(
            session,
            source_document_id=source.id,
            reviewer_id=reviewer.id,
        )


def test_performance_publication_creates_only_governed_expenditure_claims(session):
    reviewer = _reviewer(session)
    _state, source = _staged_source(session)
    approve_budget_performance_source(
        session,
        source_document_id=source.id,
        reviewer_id=reviewer.id,
    )

    result = publish_budget_performance_source(
        session,
        source_document_id=source.id,
        reviewer_id=reviewer.id,
    )
    claims = list(
        session.scalars(select(FiscalClaim).where(FiscalClaim.source_document_id == source.id))
    )
    records = list(
        session.scalars(
            select(StateBudgetPerformanceRecord).where(
                StateBudgetPerformanceRecord.source_document_id == source.id
            )
        )
    )
    publishable = [
        record for record in records if record.metric in PUBLISHABLE_EXPENDITURE_METRICS
    ]
    supporting = [
        record for record in records if record.metric not in PUBLISHABLE_EXPENDITURE_METRICS
    ]

    assert result.published is True
    assert result.records_affected == len(PUBLISHABLE_EXPENDITURE_METRICS)
    assert result.claims_published == len(PUBLISHABLE_EXPENDITURE_METRICS) * 4
    assert len(result.proof_gaia_ids) == len(PUBLISHABLE_EXPENDITURE_METRICS) * 4
    assert len(claims) == len(PUBLISHABLE_EXPENDITURE_METRICS) * 4
    assert {claim.object_type for claim in claims} == {"expenditure"}
    assert {claim.fiscal_period for claim in claims} == {"2026Q2"}
    assert all(record.is_published for record in publishable)
    assert all(not record.is_published for record in supporting)
    assert not any(claim.metric.startswith("total_revenue") for claim in claims)
