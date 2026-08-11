from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from gaiafaac_api.database.enums import (
    ProcessingStatus,
    SourceStatus,
    UserRole,
    VerificationStatus,
)
from gaiafaac_api.database.igr_models import IgrPeriodType, StateIgrRecord
from gaiafaac_api.database.models import AuditLog, SourceDocument, State, User
from gaiafaac_api.pipeline.errors import ApprovalError


@dataclass(frozen=True)
class IgrApprovalResult:
    source_document_id: str
    fiscal_year: int
    records_approved: int
    published: bool


def _reviewer(session: Session, reviewer_id: uuid.UUID) -> User:
    reviewer = session.get(User, reviewer_id)
    if reviewer is None:
        raise ApprovalError("Reviewer does not exist")
    if not reviewer.is_active or reviewer.role not in {
        UserRole.REVIEWER,
        UserRole.ADMINISTRATOR,
    }:
        raise ApprovalError("IGR approval requires an active reviewer or administrator")
    return reviewer


def _context(
    session: Session,
    *,
    source_document_id: uuid.UUID,
    reviewer_id: uuid.UUID,
) -> tuple[SourceDocument, User, list[StateIgrRecord], int]:
    source = session.get(SourceDocument, source_document_id)
    if source is None:
        raise ApprovalError("IGR source document does not exist")
    if source.is_demo:
        raise ApprovalError("Demo IGR evidence can never be approved or published")

    reviewer = _reviewer(session, reviewer_id)
    records = list(
        session.scalars(
            select(StateIgrRecord)
            .where(StateIgrRecord.source_document_id == source.id)
            .order_by(StateIgrRecord.state_id)
        )
    )
    if not records:
        raise ApprovalError("IGR source has no evidence records")

    years = {record.fiscal_year for record in records}
    if len(years) != 1:
        raise ApprovalError("IGR source must contain exactly one fiscal year")
    fiscal_year = years.pop()

    expected_count = session.scalar(select(func.count()).select_from(State)) or 0
    state_ids = {record.state_id for record in records}
    if expected_count != 37 or len(records) != 37 or len(state_ids) != expected_count:
        raise ApprovalError("IGR source must contain all 36 states and the FCT exactly once")

    if any(record.is_demo for record in records):
        raise ApprovalError("Demo IGR evidence can never be approved or published")
    if any(record.period_type is not IgrPeriodType.ANNUAL for record in records):
        raise ApprovalError("This IGR approval flow currently supports annual records only")
    if any(record.quarter is not None for record in records):
        raise ApprovalError("Annual IGR records must not contain a quarter")
    if any(
        record.period_start != date(fiscal_year, 1, 1)
        or record.period_end != date(fiscal_year, 12, 31)
        for record in records
    ):
        raise ApprovalError("Annual IGR records must span the full fiscal year")

    return source, reviewer, records, fiscal_year


def approve_igr_source(
    session: Session,
    *,
    source_document_id: uuid.UUID,
    reviewer_id: uuid.UUID,
) -> IgrApprovalResult:
    """Human-verify a complete IGR source without publishing it."""
    source, reviewer, records, fiscal_year = _context(
        session,
        source_document_id=source_document_id,
        reviewer_id=reviewer_id,
    )

    if (
        source.source_status is SourceStatus.APPROVED
        and source.processing_status is ProcessingStatus.COMPLETED
        and all(
            record.verification_status is VerificationStatus.HUMAN_VERIFIED
            for record in records
        )
    ):
        return IgrApprovalResult(str(source.id), fiscal_year, len(records), False)

    if source.source_status is not SourceStatus.READY_FOR_REVIEW:
        raise ApprovalError("IGR source is not awaiting explicit review")
    if source.processing_status is not ProcessingStatus.READY_FOR_REVIEW:
        raise ApprovalError("IGR source processing is not ready for review")
    if any(record.is_published for record in records):
        raise ApprovalError("Unapproved IGR records must not already be published")
    if any(
        record.verification_status is not VerificationStatus.REQUIRES_REVIEW
        for record in records
    ):
        raise ApprovalError("Every IGR record must be awaiting review before approval")

    reviewed_at = datetime.now(UTC)
    for record in records:
        record.verification_status = VerificationStatus.HUMAN_VERIFIED
        record.reviewed_by = reviewer.id
        record.reviewed_at = reviewed_at

    source.source_status = SourceStatus.APPROVED
    source.processing_status = ProcessingStatus.COMPLETED
    session.add(
        AuditLog(
            actor_user_id=reviewer.id,
            action="igr.approved",
            entity_type="source_document",
            entity_id=source.id,
            payload={
                "fiscal_year": fiscal_year,
                "records_approved": len(records),
                "published": False,
            },
        )
    )
    session.commit()
    return IgrApprovalResult(str(source.id), fiscal_year, len(records), False)


def publish_igr_source(
    session: Session,
    *,
    source_document_id: uuid.UUID,
    reviewer_id: uuid.UUID,
) -> IgrApprovalResult:
    """Publish a complete, human-verified IGR source."""
    source, reviewer, records, fiscal_year = _context(
        session,
        source_document_id=source_document_id,
        reviewer_id=reviewer_id,
    )

    if source.source_status is not SourceStatus.APPROVED:
        raise ApprovalError("Only approved IGR sources can be published")
    if source.processing_status is not ProcessingStatus.COMPLETED:
        raise ApprovalError("IGR source processing must be completed before publication")
    if any(
        record.verification_status is not VerificationStatus.HUMAN_VERIFIED
        for record in records
    ):
        raise ApprovalError("Every IGR record must be human-verified before publication")

    if all(record.is_published for record in records):
        return IgrApprovalResult(str(source.id), fiscal_year, len(records), True)
    if any(record.is_published for record in records):
        raise ApprovalError("IGR source is only partially published; manual investigation required")

    published_at = datetime.now(UTC)
    for record in records:
        record.is_published = True
        record.published_at = published_at

    session.add(
        AuditLog(
            actor_user_id=reviewer.id,
            action="igr.published",
            entity_type="source_document",
            entity_id=source.id,
            payload={
                "fiscal_year": fiscal_year,
                "records_published": len(records),
                "published": True,
            },
        )
    )
    session.commit()
    return IgrApprovalResult(str(source.id), fiscal_year, len(records), True)
