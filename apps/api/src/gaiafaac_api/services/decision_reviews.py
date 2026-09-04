from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.evidence_room_models import EvidenceRoom, FiscalReceipt
from gaiafaac_api.decision_review_schemas import DecisionReviewState


def get_decision_review_state(
    session: Session,
    organization_id: uuid.UUID,
    room_id: uuid.UUID,
) -> DecisionReviewState | None:
    room = session.scalar(
        select(EvidenceRoom).where(
            EvidenceRoom.id == room_id,
            EvidenceRoom.organization_id == organization_id,
        )
    )
    if room is None:
        return None

    latest = session.scalar(
        select(FiscalReceipt)
        .where(
            FiscalReceipt.organization_id == organization_id,
            FiscalReceipt.room_id == room_id,
        )
        .order_by(FiscalReceipt.created_at.desc(), FiscalReceipt.id.desc())
    )

    return DecisionReviewState(
        room_id=room.id,
        review_required=room.review_required,
        review_trigger_match_id=room.review_trigger_match_id,
        review_required_at=room.review_required_at,
        last_reviewed_at=room.last_reviewed_at,
        reviewed_by_user_id=room.reviewed_by_user_id,
        latest_receipt_id=latest.id if latest else None,
        latest_receipt_sha256=latest.receipt_sha256 if latest else None,
        latest_receipt_created_at=latest.created_at if latest else None,
        predecessor_receipt_id=latest.predecessor_receipt_id if latest else None,
        triggering_match_id=latest.triggering_match_id if latest else None,
    )
