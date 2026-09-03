from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.debt_models import StateDebtRecord
from gaiafaac_api.database.models import AuditLog, SourceDocument, State, User
from gaiafaac_api.dmo_review_schemas import (
    DmoReviewApproval,
    DmoReviewPacket,
    DmoReviewRecordItem,
    DmoReviewSource,
    PendingDmoReviewItem,
)
from gaiafaac_api.pipeline.dmo.archive import DMO_ORGANIZATION

EXPECTED_STATE_COUNT = 37


def _approval(session: Session, source_id: uuid.UUID) -> AuditLog | None:
    return session.scalar(
        select(AuditLog)
        .where(
            AuditLog.action == "debt.approved",
            AuditLog.entity_type == "source_document",
            AuditLog.entity_id == source_id,
        )
        .order_by(AuditLog.created_at.desc())
        .limit(1)
    )


def list_pending_dmo_reviews(session: Session) -> list[PendingDmoReviewItem]:
    """Real (non-demo) DMO debt sources with at least one unpublished record."""
    sources = session.scalars(
        select(SourceDocument)
        .where(
            SourceDocument.source_organization == DMO_ORGANIZATION,
            SourceDocument.is_demo.is_(False),
        )
        .order_by(SourceDocument.downloaded_at.desc())
    )
    items: list[PendingDmoReviewItem] = []
    for source in sources:
        records = list(
            session.scalars(
                select(StateDebtRecord).where(StateDebtRecord.source_document_id == source.id)
            )
        )
        if not records or all(record.is_published for record in records):
            continue
        approval = _approval(session, source.id)
        items.append(
            PendingDmoReviewItem(
                source_document_id=str(source.id),
                debt_kind=records[0].debt_kind.value,
                as_of_date=records[0].as_of_date,
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


def get_dmo_review_packet(
    session: Session, source_document_id: uuid.UUID
) -> DmoReviewPacket | None:
    source = session.get(SourceDocument, source_document_id)
    if source is None or source.is_demo or source.source_organization != DMO_ORGANIZATION:
        return None
    rows = list(
        session.execute(
            select(StateDebtRecord, State)
            .join(State, State.id == StateDebtRecord.state_id)
            .where(StateDebtRecord.source_document_id == source.id)
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
    return DmoReviewPacket(
        source_document_id=str(source.id),
        debt_kind=first_record.debt_kind.value,
        as_of_date=first_record.as_of_date,
        source=DmoReviewSource(
            source_organization=source.source_organization,
            source_url=source.source_url,
            original_filename=source.original_filename,
            sha256=source.sha256,
            document_version=source.document_version,
        ),
        covered_states=len({record.state_id for record, _state in rows}),
        expected_states=EXPECTED_STATE_COUNT,
        records=[
            DmoReviewRecordItem(
                state_name=state.name,
                state_code=state.code,
                debt_amount=str(record.debt_amount),
                currency=record.currency,
                verification_status=record.verification_status.value,
                is_published=record.is_published,
            )
            for record, state in rows
        ],
        approval=(
            DmoReviewApproval(
                actor_user_id=str(approval.actor_user_id) if approval.actor_user_id else None,
                actor_name=approver.full_name if approver else None,
                created_at=approval.created_at,
            )
            if approval is not None
            else None
        ),
        published=all(record.is_published for record, _state in rows),
    )
