from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.customer_models import OrganizationAlert
from gaiafaac_api.database.evidence_room_models import EvidenceRoom, FiscalReceipt
from gaiafaac_api.database.models import State
from gaiafaac_api.database.watch_contract_models import (
    FiscalWatchContract,
    FiscalWatchContractMatch,
)
from gaiafaac_api.decision_review_schemas import (
    DecisionReviewState,
    DecisionReviewTrigger,
)


def _latest_receipt(
    session: Session,
    organization_id: uuid.UUID,
    room_id: uuid.UUID,
) -> FiscalReceipt | None:
    rows = list(
        session.scalars(
            select(FiscalReceipt)
            .where(
                FiscalReceipt.organization_id == organization_id,
                FiscalReceipt.room_id == room_id,
            )
            .order_by(FiscalReceipt.created_at.desc())
        )
    )
    if not rows:
        return None

    predecessor_ids = {
        row.predecessor_receipt_id for row in rows if row.predecessor_receipt_id is not None
    }
    tails = [row for row in rows if row.id not in predecessor_ids]
    return tails[0] if tails else rows[0]


def _trigger_context(
    session: Session,
    organization_id: uuid.UUID,
    match_id: uuid.UUID | None,
) -> DecisionReviewTrigger | None:
    if match_id is None:
        return None

    row = session.execute(
        select(
            FiscalWatchContractMatch,
            FiscalWatchContract,
            OrganizationAlert,
            State,
        )
        .join(
            FiscalWatchContract,
            FiscalWatchContract.id == FiscalWatchContractMatch.contract_id,
        )
        .join(
            OrganizationAlert,
            OrganizationAlert.id == FiscalWatchContractMatch.organization_alert_id,
        )
        .join(State, State.id == OrganizationAlert.state_id)
        .where(
            FiscalWatchContractMatch.id == match_id,
            FiscalWatchContractMatch.organization_id == organization_id,
        )
    ).one_or_none()
    if row is None:
        return None

    match, contract, alert, state = row
    payload = alert.payload if isinstance(alert.payload, dict) else {}
    return DecisionReviewTrigger(
        match_id=match.id,
        contract_id=contract.id,
        contract_name=contract.name,
        state_code=state.code,
        state_name=state.name,
        event_type=alert.event_type,
        severity=str(alert.severity),
        headline=str(payload.get("headline") or alert.event_type.replace("_", " ")),
        detail=str(payload.get("detail") or "Recorded governed fiscal event."),
        occurred_at=alert.occurred_at,
        matched_at=match.matched_at,
    )


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

    latest = _latest_receipt(session, organization_id, room_id)
    trigger = _trigger_context(session, organization_id, room.review_trigger_match_id)

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
        trigger=trigger,
    )
