from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from gaiafaac_api.database.enums import ValidationSeverity
from gaiafaac_api.database.models import (
    ExtractionRun,
    ReportingPeriod,
    SourceDocument,
    State,
    StateAllocation,
    ValidationResult,
)
from gaiafaac_api.review_schemas import (
    PendingReviewItem,
    ReviewAllocationItem,
    ReviewFindingItem,
    ReviewPacket,
    ReviewSource,
)

EXPECTED_STATE_COUNT = 37
_BLOCKING = {ValidationSeverity.ERROR, ValidationSeverity.CRITICAL}


def list_pending_reviews(session: Session) -> list[PendingReviewItem]:
    """Real (non-demo), unpublished periods awaiting human review. Metadata only."""
    periods = session.scalars(
        select(ReportingPeriod)
        .where(
            ReportingPeriod.is_demo.is_(False),
            ReportingPeriod.is_published.is_(False),
        )
        .order_by(ReportingPeriod.revenue_month.desc())
    )
    items: list[PendingReviewItem] = []
    for period in periods:
        source = session.scalar(
            select(SourceDocument).where(SourceDocument.reporting_period_id == period.id)
        )
        if source is None:
            continue
        run = session.scalar(
            select(ExtractionRun)
            .where(ExtractionRun.source_document_id == source.id)
            .order_by(ExtractionRun.started_at.desc())
        )
        covered = (
            session.scalar(
                select(func.count())
                .select_from(StateAllocation)
                .where(
                    StateAllocation.reporting_period_id == period.id,
                    StateAllocation.is_demo.is_(False),
                )
            )
            or 0
        )
        findings = (
            list(
                session.scalars(
                    select(ValidationResult).where(ValidationResult.extraction_run_id == run.id)
                )
            )
            if run is not None
            else []
        )
        blocking = sum(finding.severity in _BLOCKING for finding in findings)
        items.append(
            PendingReviewItem(
                run_id=str(run.id) if run is not None else "",
                reporting_label=period.reporting_label,
                revenue_month=period.revenue_month,
                source_organization=source.source_organization,
                status=run.status.value if run is not None else "unknown",
                covered_states=covered,
                expected_states=EXPECTED_STATE_COUNT,
                finding_count=len(findings),
                blocking_count=blocking,
                created_at=run.started_at if run is not None else None,
            )
        )
    return items


def get_review_packet(session: Session, run_id: uuid.UUID) -> ReviewPacket | None:
    """Return the evidence packet an authorized accountant needs to review one import."""
    run = session.get(ExtractionRun, run_id)
    if run is None:
        return None
    source = session.get(SourceDocument, run.source_document_id)
    if source is None or source.reporting_period_id is None or source.is_demo:
        return None
    period = session.get(ReportingPeriod, source.reporting_period_id)
    if period is None or period.is_demo or period.is_published:
        return None

    allocations = list(
        session.execute(
            select(StateAllocation, State)
            .join(State, State.id == StateAllocation.state_id)
            .where(
                StateAllocation.reporting_period_id == period.id,
                StateAllocation.is_demo.is_(False),
            )
            .order_by(State.name)
        )
    )
    findings = list(
        session.scalars(
            select(ValidationResult)
            .where(ValidationResult.extraction_run_id == run.id)
            .order_by(ValidationResult.severity.desc(), ValidationResult.rule_code)
        )
    )
    blocking = sum(finding.severity in _BLOCKING for finding in findings)

    return ReviewPacket(
        run_id=str(run.id),
        reporting_label=period.reporting_label,
        revenue_month=period.revenue_month,
        status=run.status.value,
        source=ReviewSource(
            source_organization=source.source_organization,
            source_url=source.source_url,
            original_filename=source.original_filename,
            sha256=source.sha256,
            publication_date=source.publication_date,
            document_version=source.document_version,
        ),
        covered_states=len({allocation.state_id for allocation, _state in allocations}),
        expected_states=EXPECTED_STATE_COUNT,
        finding_count=len(findings),
        blocking_count=blocking,
        allocations=[
            ReviewAllocationItem(
                state_name=state.name,
                state_code=state.code,
                gross_total=str(allocation.gross_total)
                if allocation.gross_total is not None
                else None,
                total_deductions=(
                    str(allocation.total_deductions)
                    if allocation.total_deductions is not None
                    else None
                ),
                net_allocation=(
                    str(allocation.net_allocation)
                    if allocation.net_allocation is not None
                    else None
                ),
                reported_unit=allocation.reported_unit.value,
                verification_status=allocation.verification_status.value,
                extraction_confidence=(
                    str(allocation.extraction_confidence)
                    if allocation.extraction_confidence is not None
                    else None
                ),
            )
            for allocation, state in allocations
        ],
        findings=[
            ReviewFindingItem(
                rule_code=finding.rule_code,
                severity=finding.severity.value,
                message=finding.message,
                details=finding.details,
                outcome=finding.outcome.value,
            )
            for finding in findings
        ],
    )
