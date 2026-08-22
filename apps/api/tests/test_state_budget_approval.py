from decimal import Decimal

import pytest
from sqlalchemy import select

from gaiafaac_api.database.budget_models import BudgetMetric, StateBudgetRecord
from gaiafaac_api.database.enums import (
    ProcessingStatus,
    SourceStatus,
    UserRole,
    VerificationStatus,
)
from gaiafaac_api.database.ledger_models import FiscalClaim
from gaiafaac_api.database.models import SourceDocument, State, User
from gaiafaac_api.pipeline.errors import ApprovalError
from gaiafaac_api.pipeline.state_budget.approval import (
    approve_budget_source,
    publish_budget_source,
)


def _reviewer(session) -> User:
    reviewer = User(
        email="budget-reviewer@example.com",
        full_name="Budget Reviewer",
        role=UserRole.REVIEWER,
        is_active=True,
    )
    session.add(reviewer)
    session.flush()
    return reviewer


def _staged_source(session, *, omit_metric: BudgetMetric | None = None):
    state = State(
        name="Zamfara",
        code="ZA",
        slug="zamfara",
        geopolitical_zone="North West",
        capital="Gusau",
        is_fct=False,
    )
    session.add(state)
    session.flush()
    source = SourceDocument(
        source_organization="Zamfara State Government",
        source_url="https://zamfara.gov.ng/example-approved-budget.pdf",
        original_filename="zamfara-2026-approved-budget.pdf",
        storage_path="/tmp/zamfara-2026-approved-budget.pdf",
        sha256="c" * 64,
        mime_type="application/pdf",
        processing_status=ProcessingStatus.READY_FOR_REVIEW,
        source_status=SourceStatus.READY_FOR_REVIEW,
        document_version="approved-budget-za-2026",
        is_demo=False,
    )
    session.add(source)
    session.flush()
    for index, metric in enumerate(BudgetMetric, start=1):
        if metric is omit_metric:
            continue
        session.add(
            StateBudgetRecord(
                state_id=state.id,
                source_document_id=source.id,
                fiscal_year=2026,
                metric=metric,
                amount=Decimal(index * 1_000_000),
                amount_original=f"{index * 1_000_000:.2f}",
                currency="NGN",
                source_page=23,
                source_table="Zamfara State Government 2026 Approved Budget Summary",
                extraction_method="zamfara_approved_budget_pdf_summary_v1",
                verification_status=VerificationStatus.REQUIRES_REVIEW,
                is_demo=False,
                is_published=False,
            )
        )
    session.commit()
    return source


def test_approve_budget_requires_complete_metric_set(session):
    reviewer = _reviewer(session)
    source = _staged_source(session, omit_metric=BudgetMetric.TOTAL_EXPENDITURE)

    with pytest.raises(ApprovalError, match="complete governed metric set"):
        approve_budget_source(
            session,
            source_document_id=source.id,
            reviewer_id=reviewer.id,
        )


def test_approve_budget_human_verifies_without_publishing(session):
    reviewer = _reviewer(session)
    source = _staged_source(session)

    result = approve_budget_source(
        session,
        source_document_id=source.id,
        reviewer_id=reviewer.id,
    )
    records = list(
        session.scalars(
            select(StateBudgetRecord).where(StateBudgetRecord.source_document_id == source.id)
        )
    )

    assert result.records_affected == len(BudgetMetric)
    assert result.published is False
    assert source.source_status is SourceStatus.APPROVED
    assert source.processing_status is ProcessingStatus.COMPLETED
    assert all(
        record.verification_status is VerificationStatus.HUMAN_VERIFIED for record in records
    )
    assert all(not record.is_published for record in records)
    assert (
        session.scalar(
            select(FiscalClaim.gaia_id).where(FiscalClaim.source_document_id == source.id)
        )
        is None
    )


def test_publish_budget_requires_prior_approval(session):
    reviewer = _reviewer(session)
    source = _staged_source(session)

    with pytest.raises(ApprovalError, match="Only approved state-budget sources"):
        publish_budget_source(
            session,
            source_document_id=source.id,
            reviewer_id=reviewer.id,
        )


def test_publish_budget_creates_only_governed_budget_claims(session):
    reviewer = _reviewer(session)
    source = _staged_source(session)
    approve_budget_source(
        session,
        source_document_id=source.id,
        reviewer_id=reviewer.id,
    )

    result = publish_budget_source(
        session,
        source_document_id=source.id,
        reviewer_id=reviewer.id,
    )
    claims = list(
        session.scalars(
            select(FiscalClaim).where(FiscalClaim.source_document_id == source.id)
        )
    )
    records = list(
        session.scalars(
            select(StateBudgetRecord).where(StateBudgetRecord.source_document_id == source.id)
        )
    )

    assert result.published is True
    assert len(result.proof_gaia_ids) == len(BudgetMetric)
    assert len(claims) == len(BudgetMetric)
    assert {claim.object_type for claim in claims} == {"budget"}
    assert {claim.fiscal_period for claim in claims} == {"2026"}
    assert {claim.currency for claim in claims} == {"NGN"}
    assert {claim.metric for claim in claims} == {metric.value for metric in BudgetMetric}
    assert all(record.is_published for record in records)
