from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException

from gaiafaac_api.customer_auth import CurrentCustomer, DatabaseSession
from gaiafaac_api.decision_review_schemas import DecisionReviewState
from gaiafaac_api.services.account import current_plan, membership_for
from gaiafaac_api.services.decision_reviews import get_decision_review_state

router = APIRouter(prefix="/decision-rooms", tags=["decision review"])


def _require_decision_review_access(
    session: DatabaseSession,
    user: CurrentCustomer,
) -> uuid.UUID:
    if user.organization_id is None:
        raise HTTPException(status_code=403, detail="No customer organization is attached.")
    if membership_for(session, user) is None:
        raise HTTPException(status_code=403, detail="Organization membership is required.")
    _plan_code, entitlements, _subscription = current_plan(session, user.organization_id)
    if entitlements.max_users <= 1:
        raise HTTPException(
            status_code=403,
            detail="Decision review workflows require the Team or API plan.",
        )
    return user.organization_id


@router.get("/{room_id}/review-state", response_model=DecisionReviewState)
def decision_review_state(
    room_id: uuid.UUID,
    session: DatabaseSession,
    user: CurrentCustomer,
) -> DecisionReviewState:
    organization_id = _require_decision_review_access(session, user)
    result = get_decision_review_state(session, organization_id, room_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Decision Room not found.")
    return result
