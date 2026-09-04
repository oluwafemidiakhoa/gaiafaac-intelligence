from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.customer_models import OrganizationAlert, OrganizationMembership
from gaiafaac_api.database.models import State, User
from gaiafaac_api.database.watch_contract_models import (
    FiscalWatchContract,
    FiscalWatchContractDelivery,
    FiscalWatchContractDeliveryAttempt,
    FiscalWatchContractMatch,
    FiscalWatchContractReview,
)
from gaiafaac_api.watch_contract_schemas import (
    FiscalWatchContractDeliveryAttemptResponse,
    FiscalWatchContractDeliveryResponse,
    FiscalWatchContractReviewResponse,
)


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _delivery_response(
    session: Session, row: FiscalWatchContractDelivery
) -> FiscalWatchContractDeliveryResponse:
    attempts = list(
        session.scalars(
            select(FiscalWatchContractDeliveryAttempt)
            .where(FiscalWatchContractDeliveryAttempt.delivery_id == row.id)
            .order_by(FiscalWatchContractDeliveryAttempt.attempt_number)
        )
    )
    return FiscalWatchContractDeliveryResponse(
        id=row.id,
        review_id=row.review_id,
        match_id=row.match_id,
        contract_id=row.contract_id,
        recipient_user_id=row.recipient_user_id,
        endpoint_id=row.endpoint_id,
        channel=row.channel,
        destination_key=row.destination_key,
        recipient_address=row.recipient_address,
        status=row.status,
        attempt_count=row.attempt_count,
        next_attempt_at=row.next_attempt_at,
        last_attempt_at=row.last_attempt_at,
        response_status=row.response_status,
        response_body_excerpt=row.response_body_excerpt,
        last_error=row.last_error,
        payload_sha256=row.payload_sha256,
        details=dict(row.details or {}),
        delivered_at=row.delivered_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
        attempts=[
            FiscalWatchContractDeliveryAttemptResponse(
                id=attempt.id,
                delivery_id=attempt.delivery_id,
                attempt_number=attempt.attempt_number,
                attempted_at=attempt.attempted_at,
                response_status=attempt.response_status,
                response_body_excerpt=attempt.response_body_excerpt,
                error=attempt.error,
            )
            for attempt in attempts
        ],
    )


def _review_context(
    session: Session,
    organization_id: uuid.UUID,
    review_id: uuid.UUID,
):
    return session.execute(
        select(
            FiscalWatchContractReview,
            FiscalWatchContractMatch,
            FiscalWatchContract,
            OrganizationAlert,
            State,
        )
        .join(
            FiscalWatchContractMatch,
            FiscalWatchContractMatch.id == FiscalWatchContractReview.match_id,
        )
        .join(
            FiscalWatchContract,
            FiscalWatchContract.id == FiscalWatchContractReview.contract_id,
        )
        .join(
            OrganizationAlert,
            OrganizationAlert.id == FiscalWatchContractMatch.organization_alert_id,
        )
        .join(State, State.id == OrganizationAlert.state_id)
        .where(
            FiscalWatchContractReview.id == review_id,
            FiscalWatchContractReview.organization_id == organization_id,
        )
    ).one_or_none()


def _review_response(
    session: Session,
    review: FiscalWatchContractReview,
    match: FiscalWatchContractMatch,
    contract: FiscalWatchContract,
    alert: OrganizationAlert,
    state: State,
) -> FiscalWatchContractReviewResponse:
    payload = alert.payload if isinstance(alert.payload, dict) else {}
    deliveries = list(
        session.scalars(
            select(FiscalWatchContractDelivery)
            .where(FiscalWatchContractDelivery.review_id == review.id)
            .order_by(FiscalWatchContractDelivery.created_at, FiscalWatchContractDelivery.id)
        )
    )
    return FiscalWatchContractReviewResponse(
        id=review.id,
        match_id=match.id,
        contract_id=contract.id,
        room_id=review.room_id,
        assigned_user_id=review.assigned_user_id,
        status=review.status,
        due_at=review.due_at,
        escalated_at=review.escalated_at,
        acknowledged_at=review.acknowledged_at,
        acknowledged_by_user_id=review.acknowledged_by_user_id,
        resolved_at=review.resolved_at,
        resolved_by_user_id=review.resolved_by_user_id,
        resolution_note=review.resolution_note,
        created_at=review.created_at,
        updated_at=review.updated_at,
        contract_name=contract.name,
        state_code=state.code,
        state_name=state.name,
        event_type=alert.event_type,
        severity=str(alert.severity),
        headline=str(payload.get("headline") or alert.event_type.replace("_", " ")),
        detail=str(payload.get("detail") or "Recorded governed fiscal event."),
        occurred_at=alert.occurred_at,
        deliveries=[_delivery_response(session, item) for item in deliveries],
    )


def ensure_operational_reviews(
    session: Session,
    contract: FiscalWatchContract,
    matches: list[FiscalWatchContractMatch],
) -> int:
    """Create one organization review and one in-app delivery for each new match."""

    created = 0
    now = _utc_now()
    for match in matches:
        existing = session.scalar(
            select(FiscalWatchContractReview).where(FiscalWatchContractReview.match_id == match.id)
        )
        if existing is not None:
            continue

        assignee = None
        if contract.created_by_user_id is not None:
            membership = session.scalar(
                select(OrganizationMembership).where(
                    OrganizationMembership.organization_id == contract.organization_id,
                    OrganizationMembership.user_id == contract.created_by_user_id,
                )
            )
            if membership is not None:
                assignee = contract.created_by_user_id

        review = FiscalWatchContractReview(
            match_id=match.id,
            contract_id=contract.id,
            organization_id=contract.organization_id,
            room_id=contract.room_id,
            assigned_user_id=assignee,
            status="open",
            due_at=now + timedelta(minutes=contract.escalation_after_minutes),
        )
        session.add(review)
        session.flush()
        session.add(
            FiscalWatchContractDelivery(
                review_id=review.id,
                match_id=match.id,
                contract_id=contract.id,
                organization_id=contract.organization_id,
                recipient_user_id=assignee,
                channel="in_app",
                destination_key="organization_watch_inbox",
                status="delivered",
                details={
                    "destination": "organization_watch_inbox",
                    "delivery_scope": "organization",
                },
                delivered_at=now,
            )
        )
        created += 1
    return created


def list_operational_reviews(
    session: Session,
    organization_id: uuid.UUID,
    *,
    contract_id: uuid.UUID | None = None,
    statuses: set[str] | None = None,
) -> list[FiscalWatchContractReviewResponse]:
    statement = (
        select(
            FiscalWatchContractReview,
            FiscalWatchContractMatch,
            FiscalWatchContract,
            OrganizationAlert,
            State,
        )
        .join(
            FiscalWatchContractMatch,
            FiscalWatchContractMatch.id == FiscalWatchContractReview.match_id,
        )
        .join(
            FiscalWatchContract,
            FiscalWatchContract.id == FiscalWatchContractReview.contract_id,
        )
        .join(
            OrganizationAlert,
            OrganizationAlert.id == FiscalWatchContractMatch.organization_alert_id,
        )
        .join(State, State.id == OrganizationAlert.state_id)
        .where(FiscalWatchContractReview.organization_id == organization_id)
    )
    if contract_id is not None:
        statement = statement.where(FiscalWatchContractReview.contract_id == contract_id)
    if statuses:
        statement = statement.where(FiscalWatchContractReview.status.in_(statuses))
    rows = session.execute(
        statement.order_by(
            FiscalWatchContractReview.escalated_at.desc().nullslast(),
            FiscalWatchContractReview.due_at,
            FiscalWatchContractReview.created_at.desc(),
        )
    ).all()
    return [
        _review_response(session, review, match, contract, alert, state)
        for review, match, contract, alert, state in rows
    ]


def acknowledge_operational_review(
    session: Session,
    organization_id: uuid.UUID,
    review_id: uuid.UUID,
    user: User,
) -> FiscalWatchContractReviewResponse | None:
    row = _review_context(session, organization_id, review_id)
    if row is None:
        return None
    review, match, contract, alert, state = row
    if review.status == "open":
        review.status = "acknowledged"
        review.acknowledged_at = _utc_now()
        review.acknowledged_by_user_id = user.id
        session.commit()
        session.refresh(review)
    return _review_response(session, review, match, contract, alert, state)


def assign_operational_review(
    session: Session,
    organization_id: uuid.UUID,
    review_id: uuid.UUID,
    assigned_user_id: uuid.UUID | None,
) -> FiscalWatchContractReviewResponse | None:
    row = _review_context(session, organization_id, review_id)
    if row is None:
        return None
    review, match, contract, alert, state = row
    if assigned_user_id is not None:
        membership = session.scalar(
            select(OrganizationMembership).where(
                OrganizationMembership.organization_id == organization_id,
                OrganizationMembership.user_id == assigned_user_id,
            )
        )
        if membership is None:
            raise ValueError("Assigned user must be a current member of this organization.")
    review.assigned_user_id = assigned_user_id
    session.commit()
    session.refresh(review)
    return _review_response(session, review, match, contract, alert, state)


def resolve_operational_review(
    session: Session,
    organization_id: uuid.UUID,
    review_id: uuid.UUID,
    user: User,
    resolution_note: str,
) -> FiscalWatchContractReviewResponse | None:
    row = _review_context(session, organization_id, review_id)
    if row is None:
        return None
    review, match, contract, alert, state = row
    if review.status != "resolved":
        now = _utc_now()
        if review.acknowledged_at is None:
            review.acknowledged_at = now
            review.acknowledged_by_user_id = user.id
        review.status = "resolved"
        review.resolved_at = now
        review.resolved_by_user_id = user.id
        review.resolution_note = resolution_note.strip()
        session.commit()
        session.refresh(review)
    return _review_response(session, review, match, contract, alert, state)


def escalate_overdue_reviews(
    session: Session,
    organization_id: uuid.UUID,
) -> list[FiscalWatchContractReviewResponse]:
    now = _utc_now()
    reviews = list(
        session.scalars(
            select(FiscalWatchContractReview).where(
                FiscalWatchContractReview.organization_id == organization_id,
                FiscalWatchContractReview.status != "resolved",
                FiscalWatchContractReview.due_at <= now,
                FiscalWatchContractReview.escalated_at.is_(None),
            )
        )
    )
    for review in reviews:
        review.escalated_at = now
    if reviews:
        session.commit()

    responses: list[FiscalWatchContractReviewResponse] = []
    for review in reviews:
        row = _review_context(session, organization_id, review.id)
        if row is None:
            continue
        review_row, match, contract, alert, state = row
        responses.append(_review_response(session, review_row, match, contract, alert, state))
    return responses
