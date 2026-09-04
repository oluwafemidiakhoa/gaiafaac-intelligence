from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.lga_models import LocalGovernmentReview
from gaiafaac_api.database.models import ExtractionRun, ReportingPeriod, SourceDocument, State
from gaiafaac_api.lga_schemas import LgaPublicationStatus


def lga_publication_status(
    session: Session,
    *,
    state_code: str,
) -> LgaPublicationStatus | None:
    state = session.scalar(select(State).where(State.code == state_code.upper()))
    if state is None:
        return None

    row = session.execute(
        select(LocalGovernmentReview, ReportingPeriod, SourceDocument, ExtractionRun)
        .join(
            ReportingPeriod,
            LocalGovernmentReview.reporting_period_id == ReportingPeriod.id,
        )
        .join(
            SourceDocument,
            LocalGovernmentReview.source_document_id == SourceDocument.id,
        )
        .join(
            ExtractionRun,
            LocalGovernmentReview.extraction_run_id == ExtractionRun.id,
        )
        .order_by(
            ReportingPeriod.disbursement_month.desc().nullslast(),
            ReportingPeriod.revenue_month.desc(),
            LocalGovernmentReview.created_at.desc(),
        )
        .limit(1)
    ).first()

    if row is None:
        return LgaPublicationStatus(
            state_name=state.name,
            state_code=state.code,
            stage="not_ingested",
            reporting_label=None,
            disbursement_month=None,
            source_format=None,
            original_filename=None,
            source_sha256=None,
            record_count=0,
            blocking_count=0,
            message=(
                "No governed OAGF Table IV batch has entered the LGA publication pipeline yet."
            ),
        )

    review, period, source, run = row
    source_format_raw = (run.configuration or {}).get("source_format")
    source_format = source_format_raw if source_format_raw in {"excel", "pdf"} else None

    if review.status == "published":
        stage = "published"
        message = "Complete human-verified LGA evidence has been published."
    elif review.status == "approved":
        stage = "awaiting_publication"
        message = (
            "The 774-jurisdiction batch has been approved and is waiting for a separate publisher."
        )
    elif review.blocking_count > 0 or review.status == "investigation_required":
        stage = "investigation_required"
        message = (
            "The source has been ingested, but extraction or coverage findings block publication."
        )
    else:
        stage = "awaiting_review"
        message = "The complete extraction is staged for human review before four-eyes publication."

    return LgaPublicationStatus(
        state_name=state.name,
        state_code=state.code,
        stage=stage,
        reporting_label=period.reporting_label,
        disbursement_month=period.disbursement_month or period.revenue_month,
        source_format=source_format,
        original_filename=source.original_filename,
        source_sha256=source.sha256,
        record_count=review.record_count,
        blocking_count=review.blocking_count,
        message=message,
    )
