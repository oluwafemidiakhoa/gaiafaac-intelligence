from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.enums import UserRole
from gaiafaac_api.database.models import AuditLog, OagfDiscoveryRecord, ReportingPeriod, User
from gaiafaac_api.database.oagf_revision_models import OagfArchiveObject, OagfRevisionCase
from gaiafaac_api.oagf_revision_schemas import OagfRevisionCaseItem, RevisionResolution
from gaiafaac_api.pipeline.errors import ApprovalError


def _item(session: Session, case: OagfRevisionCase) -> OagfRevisionCaseItem:
    current = session.get(OagfDiscoveryRecord, case.discovery_record_id)
    previous = session.get(OagfDiscoveryRecord, case.previous_record_id)
    if current is None or previous is None or current.sha256 is None or previous.sha256 is None:
        raise RuntimeError("OAGF revision case has incomplete discovery lineage")
    period = (
        session.get(ReportingPeriod, case.reporting_period_id) if case.reporting_period_id else None
    )
    reviewer = session.get(User, case.reviewed_by) if case.reviewed_by else None
    return OagfRevisionCaseItem(
        id=str(case.id),
        status=case.status,
        detected_at=case.detected_at,
        title=current.title,
        reporting_label=period.reporting_label if period else None,
        revenue_month=period.revenue_month if period else None,
        current_version=current.version,
        previous_version=previous.version,
        current_sha256=current.sha256,
        previous_sha256=previous.sha256,
        current_source_url=current.document_url,
        previous_source_url=previous.document_url,
        resolution_code=case.resolution_code,
        review_note=case.review_note,
        reviewed_by=reviewer.full_name if reviewer else None,
        reviewed_at=case.reviewed_at,
    )


def list_oagf_revision_cases(session: Session) -> list[OagfRevisionCaseItem]:
    cases = session.scalars(
        select(OagfRevisionCase)
        .where(OagfRevisionCase.status != "resolved")
        .order_by(OagfRevisionCase.detected_at.desc())
    ).all()
    return [_item(session, case) for case in cases]


def get_oagf_revision_case(session: Session, case_id: uuid.UUID) -> OagfRevisionCaseItem | None:
    case = session.get(OagfRevisionCase, case_id)
    return _item(session, case) if case else None


def resolve_oagf_revision_case(
    session: Session,
    *,
    case_id: uuid.UUID,
    reviewer_id: uuid.UUID,
    resolution_code: RevisionResolution,
    note: str,
) -> OagfRevisionCaseItem:
    case = session.get(OagfRevisionCase, case_id)
    reviewer = session.get(User, reviewer_id)
    if case is None:
        raise ApprovalError("OAGF revision case does not exist")
    if (
        reviewer is None
        or not reviewer.is_active
        or reviewer.role
        not in {
            UserRole.REVIEWER,
            UserRole.ADMINISTRATOR,
        }
    ):
        raise ApprovalError("Revision review requires an active reviewer or administrator")
    if case.status == "resolved":
        return _item(session, case)

    case.reviewed_by = reviewer.id
    case.reviewed_at = datetime.now(UTC)
    case.resolution_code = resolution_code
    case.review_note = note.strip()
    case.status = (
        "investigation_required"
        if resolution_code in {"requires_data_republication", "investigation_required"}
        else "resolved"
    )
    session.add(
        AuditLog(
            actor_user_id=reviewer.id,
            action="oagf.revision.classified",
            entity_type="oagf_revision_case",
            entity_id=case.id,
            payload={
                "resolution_code": resolution_code,
                "status": case.status,
                "note": case.review_note,
                "published_data_mutated": False,
            },
        )
    )
    session.commit()
    return _item(session, case)


def get_oagf_revision_bytes(
    session: Session, *, case_id: uuid.UUID, version: str
) -> OagfArchiveObject | None:
    case = session.get(OagfRevisionCase, case_id)
    if case is None:
        return None
    record_id = case.discovery_record_id if version == "current" else case.previous_record_id
    record = session.get(OagfDiscoveryRecord, record_id)
    if record is None or record.sha256 is None:
        return None
    return session.scalar(
        select(OagfArchiveObject).where(OagfArchiveObject.sha256 == record.sha256)
    )
