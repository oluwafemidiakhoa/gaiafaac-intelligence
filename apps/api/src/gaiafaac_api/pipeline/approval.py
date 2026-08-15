from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from gaiafaac_api.database.enums import (
    ExtractionStatus,
    ProcessingStatus,
    SourceStatus,
    UserRole,
    ValidationSeverity,
    VerificationStatus,
)
from gaiafaac_api.database.models import (
    AuditLog,
    ExtractionRun,
    ReportingPeriod,
    SourceDocument,
    State,
    StateAllocation,
    User,
    ValidationResult,
)
from gaiafaac_api.pipeline.errors import ApprovalError
from gaiafaac_api.pipeline.validation import validate_import
from gaiafaac_api.services.fiscal_ledger import (
    publish_current_fiscal_state,
    publish_faac_claim_proof,
)


@dataclass(frozen=True)
class ApprovalResult:
    run_id: str
    reporting_period_id: str
    allocations_approved: int
    published: bool


def _approval_context(
    session: Session, run_id: uuid.UUID, reviewer_id: uuid.UUID
) -> tuple[ExtractionRun, SourceDocument, ReportingPeriod, User, list[StateAllocation]]:
    run = session.get(ExtractionRun, run_id)
    if run is None:
        raise ApprovalError("Extraction run does not exist")
    source = session.get(SourceDocument, run.source_document_id)
    if source is None or source.reporting_period_id is None:
        raise ApprovalError("Extraction run has no reporting-period lineage")
    period = session.get(ReportingPeriod, source.reporting_period_id)
    reviewer = session.get(User, reviewer_id)
    if period is None or reviewer is None:
        raise ApprovalError("Reporting period or reviewer does not exist")
    if not reviewer.is_active or reviewer.role not in {
        UserRole.REVIEWER,
        UserRole.ADMINISTRATOR,
    }:
        raise ApprovalError("Approval requires an active reviewer or administrator")
    allocations = list(
        session.scalars(
            select(StateAllocation).where(StateAllocation.reporting_period_id == period.id)
        )
    )
    return run, source, period, reviewer, allocations


def approve_import(
    session: Session,
    *,
    run_id: uuid.UUID,
    reviewer_id: uuid.UUID,
    note: str | None = None,
) -> ApprovalResult:
    """Human-verify a clean import without publishing it."""
    run, source, period, reviewer, allocations = _approval_context(session, run_id, reviewer_id)
    if (
        run.status is ExtractionStatus.COMPLETED
        and period.verification_status is VerificationStatus.HUMAN_VERIFIED
    ):
        return ApprovalResult(str(run.id), str(period.id), len(allocations), False)
    if run.status is not ExtractionStatus.REQUIRES_REVIEW:
        raise ApprovalError("Extraction run is not awaiting explicit review")

    validate_import(session, run)
    blocking_count = session.scalar(
        select(func.count())
        .select_from(ValidationResult)
        .where(
            ValidationResult.extraction_run_id == run.id,
            ValidationResult.severity.in_([ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]),
        )
    )
    if blocking_count:
        session.commit()
        raise ApprovalError(f"Import has {blocking_count} blocking validation findings")
    expected_count = session.scalar(select(func.count()).select_from(State)) or 0
    if len({allocation.state_id for allocation in allocations}) != expected_count:
        raise ApprovalError("Import does not contain every canonical state and the FCT")
    if any(
        allocation.verification_status is not VerificationStatus.AUTOMATICALLY_VALIDATED
        for allocation in allocations
    ):
        raise ApprovalError("Every allocation must pass automated validation before approval")

    reviewed_at = datetime.now(UTC)
    for allocation in allocations:
        allocation.verification_status = VerificationStatus.HUMAN_VERIFIED
        allocation.reviewed_by = reviewer.id
        allocation.reviewed_at = reviewed_at
    for finding in session.scalars(
        select(ValidationResult).where(ValidationResult.extraction_run_id == run.id)
    ):
        finding.outcome = VerificationStatus.HUMAN_VERIFIED
    period.verification_status = VerificationStatus.HUMAN_VERIFIED
    period.source_status = SourceStatus.APPROVED
    source.source_status = SourceStatus.APPROVED
    source.processing_status = ProcessingStatus.COMPLETED
    run.status = ExtractionStatus.COMPLETED
    session.add(
        AuditLog(
            actor_user_id=reviewer.id,
            action="import.approved",
            entity_type="extraction_run",
            entity_id=run.id,
            payload={
                "reporting_period_id": str(period.id),
                "source_document_id": str(source.id),
                "allocations_approved": len(allocations),
                "review_note": note.strip() if note and note.strip() else None,
                "published": False,
            },
        )
    )
    session.commit()
    return ApprovalResult(str(run.id), str(period.id), len(allocations), False)


def reject_import(
    session: Session,
    *,
    run_id: uuid.UUID,
    reviewer_id: uuid.UUID,
    reason: str,
) -> ApprovalResult:
    """Explicitly reject an import while preserving its records and audit history."""
    if not reason.strip():
        raise ApprovalError("Rejection requires a reason")
    run, source, period, reviewer, allocations = _approval_context(session, run_id, reviewer_id)
    if run.status is not ExtractionStatus.REQUIRES_REVIEW:
        raise ApprovalError("Extraction run is not awaiting explicit review")
    reviewed_at = datetime.now(UTC)
    for allocation in allocations:
        allocation.verification_status = VerificationStatus.REJECTED
        allocation.reviewed_by = reviewer.id
        allocation.reviewed_at = reviewed_at
    for finding in session.scalars(
        select(ValidationResult).where(ValidationResult.extraction_run_id == run.id)
    ):
        finding.outcome = VerificationStatus.REJECTED
    period.verification_status = VerificationStatus.REJECTED
    period.source_status = SourceStatus.REJECTED
    source.source_status = SourceStatus.REJECTED
    source.processing_status = ProcessingStatus.REJECTED
    run.status = ExtractionStatus.COMPLETED
    session.add(
        AuditLog(
            actor_user_id=reviewer.id,
            action="import.rejected",
            entity_type="extraction_run",
            entity_id=run.id,
            payload={"reason": reason.strip(), "published": False},
        )
    )
    session.commit()
    return ApprovalResult(str(run.id), str(period.id), 0, False)


def publish_import(
    session: Session, *, run_id: uuid.UUID, reviewer_id: uuid.UUID
) -> ApprovalResult:
    """Publish human-verified evidence under a four-eyes administrator control."""
    run, source, period, publisher, allocations = _approval_context(session, run_id, reviewer_id)
    if publisher.role is not UserRole.ADMINISTRATOR:
        raise ApprovalError("Publishing requires an active administrator")
    if any(allocation.reviewed_by == publisher.id for allocation in allocations):
        raise ApprovalError("The human reviewer cannot publish the same import")
    if period.is_demo or source.is_demo:
        raise ApprovalError("Demo data can never be published")
    if period.verification_status is not VerificationStatus.HUMAN_VERIFIED:
        raise ApprovalError("Only human-verified imports can be published")
    if any(
        allocation.verification_status is not VerificationStatus.HUMAN_VERIFIED
        for allocation in allocations
    ):
        raise ApprovalError("Every allocation must be human-verified before publishing")
    if period.is_published:
        return ApprovalResult(str(run.id), str(period.id), len(allocations), True)

    published_at = datetime.now(UTC)
    for allocation in allocations:
        allocation.is_published = True
        allocation.published_at = published_at
    period.is_published = True
    period.published_at = published_at
    source.source_status = SourceStatus.APPROVED
    session.flush()
    for allocation in allocations:
        publish_faac_claim_proof(session, allocation_id=allocation.id)
    for state_id in sorted({allocation.state_id for allocation in allocations}, key=str):
        publish_current_fiscal_state(
            session,
            state_id=state_id,
            effective_at=published_at,
            fiscal_period=f"{period.revenue_month.year}-YTD",
        )
    session.add(
        AuditLog(
            actor_user_id=publisher.id,
            action="import.published",
            entity_type="reporting_period",
            entity_id=period.id,
            payload={
                "allocations_published": len(allocations),
                "published": True,
                "separation_of_duties": True,
            },
        )
    )
    session.commit()
    return ApprovalResult(str(run.id), str(period.id), len(allocations), True)
