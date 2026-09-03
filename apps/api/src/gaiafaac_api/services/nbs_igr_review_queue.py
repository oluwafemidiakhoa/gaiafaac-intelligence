from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.igr_models import StateIgrRecord
from gaiafaac_api.database.models import AuditLog, SourceDocument, State, User
from gaiafaac_api.nbs_igr_review_schemas import (
    IgrReviewApproval,
    IgrReviewPacket,
    IgrReviewRecordItem,
    IgrReviewSource,
    PendingIgrReviewItem,
)
from gaiafaac_api.pipeline.nbs_igr.archive import NBS_IGR_ORGANIZATION

EXPECTED_STATE_COUNT = 37


def _approval(session: Session, source_id: uuid.UUID) -> AuditLog | None:
    return session.scalar(
        select(AuditLog)
        .where(
            AuditLog.action == "igr.approved",
            AuditLog.entity_type == "source_document",
            AuditLog.entity_id == source_id,
        )
        .order_by(AuditLog.created_at.desc())
        .limit(1)
    )


def list_pending_igr_reviews(session: Session) -> list[PendingIgrReviewItem]:
    """Real (non-demo) NBS IGR sources with at least one unpublished record."""
    sources = session.scalars(
        select(SourceDocument)
        .where(
            SourceDocument.source_organization == NBS_IGR_ORGANIZATION,
            SourceDocument.is_demo.is_(False),
        )
        .order_by(SourceDocument.downloaded_at.desc())
    )
    items: list[PendingIgrReviewItem] = []
    for source in sources:
        records = list(
            session.scalars(
                select(StateIgrRecord).where(StateIgrRecord.source_document_id == source.id)
            )
        )
        if not records or all(record.is_published for record in records):
            continue
        approval = _approval(session, source.id)
        items.append(
            PendingIgrReviewItem(
                source_document_id=str(source.id),
                fiscal_year=records[0].fiscal_year,
                source_organization=source.source_organization,
                processing_status=source.processing_status.value,
                covered_states=len({record.state_id for record in records}),
                expected_states=EXPECTED_STATE_COUNT,
                approved=approval is not None,
                approved_by=(
                    str(approval.actor_user_id) if approval and approval.actor_user_id else None
                ),
                created_at=source.downloaded_at,
            )
        )
    return items


def get_igr_review_packet(
    session: Session, source_document_id: uuid.UUID
) -> IgrReviewPacket | None:
    source = session.get(SourceDocument, source_document_id)
    if source is None or source.is_demo or source.source_organization != NBS_IGR_ORGANIZATION:
        return None
    rows = list(
        session.execute(
            select(StateIgrRecord, State)
            .join(State, State.id == StateIgrRecord.state_id)
            .where(StateIgrRecord.source_document_id == source.id)
            .order_by(State.name)
        )
    )
    if not rows:
        return None
    approval = _approval(session, source.id)
    approver = (
        session.get(User, approval.actor_user_id) if approval and approval.actor_user_id else None
    )
    first_record = rows[0][0]
    return IgrReviewPacket(
        source_document_id=str(source.id),
        fiscal_year=first_record.fiscal_year,
        source=IgrReviewSource(
            source_organization=source.source_organization,
            source_url=source.source_url,
            original_filename=source.original_filename,
            sha256=source.sha256,
            document_version=source.document_version,
        ),
        covered_states=len({record.state_id for record, _state in rows}),
        expected_states=EXPECTED_STATE_COUNT,
        records=[
            IgrReviewRecordItem(
                state_name=state.name,
                state_code=state.code,
                igr_amount=str(record.igr_amount),
                reported_unit=record.reported_unit.value,
                verification_status=record.verification_status.value,
                is_published=record.is_published,
            )
            for record, state in rows
        ],
        approval=(
            IgrReviewApproval(
                actor_user_id=str(approval.actor_user_id) if approval.actor_user_id else None,
                actor_name=approver.full_name if approver else None,
                created_at=approval.created_at,
            )
            if approval is not None
            else None
        ),
        published=all(record.is_published for record, _state in rows),
    )
