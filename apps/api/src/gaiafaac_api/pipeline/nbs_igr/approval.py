from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime, time

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from gaiafaac_api.database.enums import (
    ProcessingStatus,
    ReportedUnit,
    SourceStatus,
    UserRole,
    VerificationStatus,
)
from gaiafaac_api.database.igr_models import IgrPeriodType, StateIgrRecord
from gaiafaac_api.database.models import AuditLog, SourceDocument, State, User
from gaiafaac_api.pipeline.errors import ApprovalError
from gaiafaac_api.services.fiscal_domain_claims import publish_domain_claim

_VERSION_RE = re.compile(r"^igr-(?P<year>20\d{2})-report-(?P<report_id>\d+)$")


@dataclass(frozen=True)
class IgrApprovalResult:
    source_document_id: str
    fiscal_year: int
    records_affected: int
    published: bool
    proof_gaia_ids: tuple[str, ...] = ()


def _reviewer(session: Session, reviewer_id: uuid.UUID) -> User:
    reviewer = session.get(User, reviewer_id)
    if reviewer is None:
        raise ApprovalError("Reviewer does not exist")
    if not reviewer.is_active or reviewer.role not in {
        UserRole.REVIEWER,
        UserRole.ADMINISTRATOR,
    }:
        raise ApprovalError("NBS IGR approval requires an active reviewer or administrator")
    return reviewer


def _context(
    session: Session,
    *,
    source_document_id: uuid.UUID,
    reviewer_id: uuid.UUID,
) -> tuple[SourceDocument, User, list[StateIgrRecord], int]:
    source = session.get(SourceDocument, source_document_id)
    if source is None:
        raise ApprovalError("NBS IGR source document does not exist")
    if source.is_demo:
        raise ApprovalError("Demo IGR evidence can never be approved or published")
    if "National Bureau of Statistics" not in source.source_organization:
        raise ApprovalError("Source document is not registered as NBS evidence")

    reviewer = _reviewer(session, reviewer_id)
    records = list(
        session.scalars(
            select(StateIgrRecord)
            .where(StateIgrRecord.source_document_id == source.id)
            .order_by(StateIgrRecord.state_id)
        )
    )
    if not records:
        raise ApprovalError("NBS IGR source has no staged records")

    expected_count = session.scalar(select(func.count()).select_from(State)) or 0
    state_ids = {record.state_id for record in records}
    if expected_count != 37 or len(records) != 37 or len(state_ids) != expected_count:
        raise ApprovalError("NBS IGR source must contain all 36 states and the FCT exactly once")

    years = {record.fiscal_year for record in records}
    period_types = {record.period_type for record in records}
    reported_units = {record.reported_unit for record in records}
    if len(years) != 1:
        raise ApprovalError("NBS IGR source records must share one fiscal year")
    if period_types != {IgrPeriodType.ANNUAL}:
        raise ApprovalError("NBS IGR source records must all be annual observations")
    if reported_units != {ReportedUnit.NAIRA}:
        raise ApprovalError("NBS IGR source records must all be reported in naira")

    fiscal_year = years.pop()
    expected_start = date(fiscal_year, 1, 1)
    expected_end = date(fiscal_year, 12, 31)
    if any(
        record.quarter is not None
        or record.period_start != expected_start
        or record.period_end != expected_end
        for record in records
    ):
        raise ApprovalError("NBS IGR annual record periods do not match the fiscal year")

    version = _VERSION_RE.fullmatch(source.document_version or "")
    if version is None or int(version.group("year")) != fiscal_year:
        raise ApprovalError("NBS IGR source version does not match the staged fiscal year")
    if any(record.is_demo for record in records):
        raise ApprovalError("Demo IGR evidence can never be approved or published")

    return source, reviewer, records, fiscal_year


def approve_igr_source(
    session: Session,
    *,
    source_document_id: uuid.UUID,
    reviewer_id: uuid.UUID,
) -> IgrApprovalResult:
    """Human-verify a complete NBS IGR source without publishing ledger claims."""

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
        return IgrApprovalResult(
            source_document_id=str(source.id),
            fiscal_year=fiscal_year,
            records_affected=len(records),
            published=False,
        )

    if source.source_status is not SourceStatus.READY_FOR_REVIEW:
        raise ApprovalError("NBS IGR source is not awaiting explicit review")
    if source.processing_status is not ProcessingStatus.READY_FOR_REVIEW:
        raise ApprovalError("NBS IGR source processing is not ready for review")
    if any(record.is_published for record in records):
        raise ApprovalError("Unapproved NBS IGR records must not already be published")
    if any(
        record.verification_status is not VerificationStatus.REQUIRES_REVIEW
        for record in records
    ):
        raise ApprovalError("Every NBS IGR record must be awaiting review before approval")

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
    return IgrApprovalResult(
        source_document_id=str(source.id),
        fiscal_year=fiscal_year,
        records_affected=len(records),
        published=False,
    )


def publish_igr_source(
    session: Session,
    *,
    source_document_id: uuid.UUID,
    reviewer_id: uuid.UUID,
) -> IgrApprovalResult:
    """Publish approved annual NBS IGR observations into immutable governed claims."""

    source, reviewer, records, fiscal_year = _context(
        session,
        source_document_id=source_document_id,
        reviewer_id=reviewer_id,
    )

    if source.source_status is not SourceStatus.APPROVED:
        raise ApprovalError("Only approved NBS IGR sources can be published")
    if source.processing_status is not ProcessingStatus.COMPLETED:
        raise ApprovalError("NBS IGR source processing must be completed before publication")
    if any(
        record.verification_status is not VerificationStatus.HUMAN_VERIFIED
        for record in records
    ):
        raise ApprovalError("Every NBS IGR record must be human-verified before publication")

    if all(record.is_published for record in records):
        return IgrApprovalResult(
            source_document_id=str(source.id),
            fiscal_year=fiscal_year,
            records_affected=len(records),
            published=True,
        )
    if any(record.is_published for record in records):
        raise ApprovalError("NBS IGR source is only partially published; investigation required")

    published_at = datetime.now(UTC)
    effective_at = datetime.combine(date(fiscal_year, 12, 31), time.min, tzinfo=UTC)
    proof_ids: list[str] = []
    try:
        for record in records:
            proof = publish_domain_claim(
                session,
                domain="igr",
                state_id=record.state_id,
                source_document_id=source.id,
                fiscal_period=str(fiscal_year),
                metric="igr",
                value=record.igr_amount,
                value_text=format(record.igr_amount, "f"),
                unit="currency",
                currency="NGN",
                effective_at=effective_at,
                published_at=published_at,
                source_page=record.source_page,
                source_table=record.source_table,
                extraction_method="nbs_igr_pdf_deterministic_v1",
                human_reviewed=True,
                reconciled=None,
            )
            proof_ids.append(proof.gaia_id)
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
                    "proof_count": len(proof_ids),
                    "published": True,
                },
            )
        )
        session.commit()
    except Exception:
        session.rollback()
        raise

    return IgrApprovalResult(
        source_document_id=str(source.id),
        fiscal_year=fiscal_year,
        records_affected=len(records),
        published=True,
        proof_gaia_ids=tuple(proof_ids),
    )
