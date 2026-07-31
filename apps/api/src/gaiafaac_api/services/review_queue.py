from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from gaiafaac_api.database.enums import ValidationSeverity
from gaiafaac_api.database.models import (
    ExtractionRun,
    ReportingPeriod,
    SourceDocument,
    StateAllocation,
    ValidationResult,
)
from gaiafaac_api.review_schemas import PendingReviewItem

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
