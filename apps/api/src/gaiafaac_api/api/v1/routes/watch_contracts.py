from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from gaiafaac_api.config import get_settings
from gaiafaac_api.customer_auth import CurrentCustomer, DatabaseSession
from gaiafaac_api.services.account import current_plan, membership_for
from gaiafaac_api.services.watch_contract_delivery import run_watch_delivery
from gaiafaac_api.services.watch_contract_operations import (
    acknowledge_operational_review,
    assign_operational_review,
    escalate_overdue_reviews,
    list_operational_reviews,
    resolve_operational_review,
)
from gaiafaac_api.services.watch_contracts import (
    create_contract,
    evaluate_contract,
    list_contract_matches,
    list_contracts,
    set_contract_status,
)
from gaiafaac_api.watch_contract_schemas import (
    FiscalWatchContractCreateRequest,
    FiscalWatchContractEscalationResponse,
    FiscalWatchContractEvaluationResponse,
    FiscalWatchContractMatchResponse,
    FiscalWatchContractResponse,
    FiscalWatchContractReviewAssignRequest,
    FiscalWatchContractReviewResolveRequest,
    FiscalWatchContractReviewResponse,
    FiscalWatchContractStatusUpdate,
    FiscalWatchDeliveryRunResponse,
)

router = APIRouter(prefix="/fiscal-watch-contracts", tags=["fiscal watch contracts"])


def _require_watch_contracts(session: DatabaseSession, user: CurrentCustomer):
    if user.organization_id is None:
        raise HTTPException(status_code=403, detail="No customer organization is attached.")
    membership = membership_for(session, user)
    if membership is None:
        raise HTTPException(status_code=403, detail="Organization membership is required.")
    _plan_code, entitlements, _subscription = current_plan(session, user.organization_id)
    if entitlements.max_users <= 1:
        raise HTTPException(
            status_code=403,
            detail="Fiscal Watch Contracts require the Team or API plan.",
        )
    return user.organization_id, membership


def _require_watch_contract_admin(session: DatabaseSession, user: CurrentCustomer) -> uuid.UUID:
    organization_id, membership = _require_watch_contracts(session, user)
    if membership.role not in {"owner", "admin"}:
        raise HTTPException(
            status_code=403,
            detail="Organization administrator access is required to change monitoring contracts.",
        )
    return organization_id


@router.get("", response_model=list[FiscalWatchContractResponse])
def get_contracts(
    session: DatabaseSession,
    user: CurrentCustomer,
) -> list[FiscalWatchContractResponse]:
    organization_id, _membership = _require_watch_contracts(session, user)
    return list_contracts(session, organization_id)


@router.post(
    "",
    response_model=FiscalWatchContractResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_watch_contract(
    payload: FiscalWatchContractCreateRequest,
    session: DatabaseSession,
    user: CurrentCustomer,
) -> FiscalWatchContractResponse:
    organization_id = _require_watch_contract_admin(session, user)
    contract = create_contract(session, organization_id, user, payload)
    if contract is None:
        raise HTTPException(
            status_code=404,
            detail="Decision Room or baseline Fiscal Receipt was not found in this organization.",
        )
    return contract


@router.patch("/{contract_id}/status", response_model=FiscalWatchContractResponse)
def change_watch_contract_status(
    contract_id: uuid.UUID,
    payload: FiscalWatchContractStatusUpdate,
    session: DatabaseSession,
    user: CurrentCustomer,
) -> FiscalWatchContractResponse:
    organization_id = _require_watch_contract_admin(session, user)
    contract = set_contract_status(session, organization_id, contract_id, payload.status)
    if contract is None:
        raise HTTPException(status_code=404, detail="Fiscal Watch Contract not found.")
    return contract


@router.get(
    "/{contract_id}/matches",
    response_model=list[FiscalWatchContractMatchResponse],
)
def get_watch_contract_matches(
    contract_id: uuid.UUID,
    session: DatabaseSession,
    user: CurrentCustomer,
) -> list[FiscalWatchContractMatchResponse]:
    organization_id, _membership = _require_watch_contracts(session, user)
    contracts = {item.id for item in list_contracts(session, organization_id)}
    if contract_id not in contracts:
        raise HTTPException(status_code=404, detail="Fiscal Watch Contract not found.")
    return list_contract_matches(session, organization_id, contract_id)


@router.post(
    "/{contract_id}/evaluate",
    response_model=FiscalWatchContractEvaluationResponse,
)
def evaluate_watch_contract(
    contract_id: uuid.UUID,
    session: DatabaseSession,
    user: CurrentCustomer,
    year: Annotated[int | None, Query(ge=2000, le=2100)] = None,
) -> FiscalWatchContractEvaluationResponse:
    organization_id, _membership = _require_watch_contracts(session, user)
    resolved_year = year if year is not None else datetime.now(UTC).year
    result = evaluate_contract(session, organization_id, contract_id, resolved_year)
    if result is None:
        raise HTTPException(status_code=404, detail="Fiscal Watch Contract not found.")
    return result


@router.get("/reviews", response_model=list[FiscalWatchContractReviewResponse])
def get_operational_reviews(
    session: DatabaseSession,
    user: CurrentCustomer,
    review_status: Annotated[str | None, Query(alias="status")] = None,
) -> list[FiscalWatchContractReviewResponse]:
    organization_id, _membership = _require_watch_contracts(session, user)
    statuses = {review_status} if review_status else None
    if statuses and not statuses <= {"open", "acknowledged", "resolved"}:
        raise HTTPException(status_code=422, detail="Unsupported operational review status.")
    return list_operational_reviews(session, organization_id, statuses=statuses)


@router.get(
    "/{contract_id}/reviews",
    response_model=list[FiscalWatchContractReviewResponse],
)
def get_contract_operational_reviews(
    contract_id: uuid.UUID,
    session: DatabaseSession,
    user: CurrentCustomer,
) -> list[FiscalWatchContractReviewResponse]:
    organization_id, _membership = _require_watch_contracts(session, user)
    contracts = {item.id for item in list_contracts(session, organization_id)}
    if contract_id not in contracts:
        raise HTTPException(status_code=404, detail="Fiscal Watch Contract not found.")
    return list_operational_reviews(session, organization_id, contract_id=contract_id)


@router.post(
    "/reviews/{review_id}/acknowledge",
    response_model=FiscalWatchContractReviewResponse,
)
def acknowledge_watch_review(
    review_id: uuid.UUID,
    session: DatabaseSession,
    user: CurrentCustomer,
) -> FiscalWatchContractReviewResponse:
    organization_id, _membership = _require_watch_contracts(session, user)
    review = acknowledge_operational_review(session, organization_id, review_id, user)
    if review is None:
        raise HTTPException(status_code=404, detail="Operational review not found.")
    return review


@router.patch(
    "/reviews/{review_id}/assign",
    response_model=FiscalWatchContractReviewResponse,
)
def assign_watch_review(
    review_id: uuid.UUID,
    payload: FiscalWatchContractReviewAssignRequest,
    session: DatabaseSession,
    user: CurrentCustomer,
) -> FiscalWatchContractReviewResponse:
    organization_id = _require_watch_contract_admin(session, user)
    try:
        review = assign_operational_review(
            session,
            organization_id,
            review_id,
            payload.assigned_user_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if review is None:
        raise HTTPException(status_code=404, detail="Operational review not found.")
    return review


@router.post(
    "/reviews/{review_id}/resolve",
    response_model=FiscalWatchContractReviewResponse,
)
def resolve_watch_review(
    review_id: uuid.UUID,
    payload: FiscalWatchContractReviewResolveRequest,
    session: DatabaseSession,
    user: CurrentCustomer,
) -> FiscalWatchContractReviewResponse:
    organization_id, _membership = _require_watch_contracts(session, user)
    review = resolve_operational_review(
        session,
        organization_id,
        review_id,
        user,
        payload.resolution_note,
    )
    if review is None:
        raise HTTPException(status_code=404, detail="Operational review not found.")
    return review


@router.post("/reviews/escalate", response_model=FiscalWatchContractEscalationResponse)
def escalate_watch_reviews(
    session: DatabaseSession,
    user: CurrentCustomer,
) -> FiscalWatchContractEscalationResponse:
    organization_id = _require_watch_contract_admin(session, user)
    reviews = escalate_overdue_reviews(session, organization_id)
    return FiscalWatchContractEscalationResponse(
        escalated_count=len(reviews),
        reviews=reviews,
    )


@router.post("/deliveries/run", response_model=FiscalWatchDeliveryRunResponse)
def run_watch_deliveries(
    session: DatabaseSession,
    user: CurrentCustomer,
) -> FiscalWatchDeliveryRunResponse:
    organization_id = _require_watch_contract_admin(session, user)
    summary = run_watch_delivery(
        session,
        get_settings(),
        organization_id=organization_id,
    )
    return FiscalWatchDeliveryRunResponse(**summary.__dict__)
