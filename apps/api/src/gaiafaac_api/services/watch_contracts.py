from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from gaiafaac_api.database.customer_models import OrganizationAlert
from gaiafaac_api.database.evidence_room_models import EvidenceRoom, FiscalReceipt
from gaiafaac_api.database.models import State, User
from gaiafaac_api.database.watch_contract_models import (
    FiscalWatchContract,
    FiscalWatchContractMatch,
)
from gaiafaac_api.services.watchlists import sync_organization_watchlist_alerts
from gaiafaac_api.watch_contract_schemas import (
    FiscalWatchContractCreateRequest,
    FiscalWatchContractEvaluationResponse,
    FiscalWatchContractMatchResponse,
    FiscalWatchContractResponse,
)

_SEVERITY_RANK = {
    "informational": 0,
    "watch": 1,
    "elevated": 2,
    "notable": 3,
    "material": 4,
    "critical": 5,
}


def _contract_response(session: Session, row: FiscalWatchContract) -> FiscalWatchContractResponse:
    match_count = session.scalar(
        select(func.count(FiscalWatchContractMatch.id)).where(
            FiscalWatchContractMatch.contract_id == row.id
        )
    )
    return FiscalWatchContractResponse(
        id=row.id,
        organization_id=row.organization_id,
        room_id=row.room_id,
        baseline_receipt_id=row.baseline_receipt_id,
        created_by_user_id=row.created_by_user_id,
        name=row.name,
        state_codes=list(row.state_codes or []),
        event_types=list(row.event_types or []),
        minimum_severity=row.minimum_severity,
        status=row.status,
        last_evaluated_at=row.last_evaluated_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
        match_count=int(match_count or 0),
    )


def create_contract(
    session: Session,
    organization_id: uuid.UUID,
    user: User,
    payload: FiscalWatchContractCreateRequest,
) -> FiscalWatchContractResponse | None:
    room = session.scalar(
        select(EvidenceRoom).where(
            EvidenceRoom.id == payload.room_id,
            EvidenceRoom.organization_id == organization_id,
        )
    )
    if room is None:
        return None

    if payload.baseline_receipt_id is not None:
        receipt = session.scalar(
            select(FiscalReceipt).where(
                FiscalReceipt.id == payload.baseline_receipt_id,
                FiscalReceipt.organization_id == organization_id,
                FiscalReceipt.room_id == payload.room_id,
            )
        )
        if receipt is None:
            return None

    row = FiscalWatchContract(
        organization_id=organization_id,
        room_id=payload.room_id,
        baseline_receipt_id=payload.baseline_receipt_id,
        created_by_user_id=user.id,
        name=payload.name,
        state_codes=payload.state_codes,
        event_types=payload.event_types,
        minimum_severity=payload.minimum_severity,
        status="active",
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return _contract_response(session, row)


def list_contracts(
    session: Session, organization_id: uuid.UUID
) -> list[FiscalWatchContractResponse]:
    rows = list(
        session.scalars(
            select(FiscalWatchContract)
            .where(FiscalWatchContract.organization_id == organization_id)
            .order_by(FiscalWatchContract.created_at.desc())
        )
    )
    return [_contract_response(session, row) for row in rows]


def set_contract_status(
    session: Session,
    organization_id: uuid.UUID,
    contract_id: uuid.UUID,
    status: str,
) -> FiscalWatchContractResponse | None:
    row = session.scalar(
        select(FiscalWatchContract).where(
            FiscalWatchContract.id == contract_id,
            FiscalWatchContract.organization_id == organization_id,
        )
    )
    if row is None:
        return None
    row.status = status
    session.commit()
    session.refresh(row)
    return _contract_response(session, row)


def _matches_contract(
    contract: FiscalWatchContract, alert: OrganizationAlert, state: State
) -> bool:
    state_codes = {str(item).upper() for item in (contract.state_codes or [])}
    if state_codes and state.code.upper() not in state_codes:
        return False

    event_types = {str(item) for item in (contract.event_types or [])}
    if event_types and alert.event_type not in event_types:
        return False

    threshold = _SEVERITY_RANK.get(contract.minimum_severity, 1)
    return _SEVERITY_RANK.get(str(alert.severity), 0) >= threshold


def _match_response(match: FiscalWatchContractMatch, alert: OrganizationAlert, state: State):
    payload = alert.payload if isinstance(alert.payload, dict) else {}
    return FiscalWatchContractMatchResponse(
        id=match.id,
        contract_id=match.contract_id,
        room_id=match.room_id,
        organization_alert_id=match.organization_alert_id,
        state_code=state.code,
        state_name=state.name,
        event_type=alert.event_type,
        severity=str(alert.severity),
        headline=str(payload.get("headline") or alert.event_type.replace("_", " ")),
        detail=str(payload.get("detail") or "Recorded governed fiscal event."),
        occurred_at=alert.occurred_at,
        matched_at=match.matched_at,
    )


def evaluate_contract(
    session: Session,
    organization_id: uuid.UUID,
    contract_id: uuid.UUID,
    year: int,
) -> FiscalWatchContractEvaluationResponse | None:
    contract = session.scalar(
        select(FiscalWatchContract).where(
            FiscalWatchContract.id == contract_id,
            FiscalWatchContract.organization_id == organization_id,
        )
    )
    if contract is None:
        return None

    if contract.status != "active":
        matches = list_contract_matches(session, organization_id, contract_id)
        return FiscalWatchContractEvaluationResponse(
            contract=_contract_response(session, contract),
            new_match_count=0,
            total_match_count=len(matches),
            matches=matches,
            note="Paused or archived contracts are not evaluated until reactivated.",
        )

    sync_organization_watchlist_alerts(session, organization_id, year)

    start = datetime(year, 1, 1, tzinfo=UTC)
    end = datetime(year + 1, 1, 1, tzinfo=UTC)
    rows = session.execute(
        select(OrganizationAlert, State)
        .join(State, State.id == OrganizationAlert.state_id)
        .where(
            OrganizationAlert.organization_id == organization_id,
            OrganizationAlert.occurred_at >= start,
            OrganizationAlert.occurred_at < end,
        )
        .order_by(OrganizationAlert.occurred_at, OrganizationAlert.id)
    ).all()

    existing = set(
        session.scalars(
            select(FiscalWatchContractMatch.organization_alert_id).where(
                FiscalWatchContractMatch.contract_id == contract.id
            )
        )
    )
    pending: list[FiscalWatchContractMatch] = []
    for alert, state in rows:
        if alert.id in existing or not _matches_contract(contract, alert, state):
            continue
        pending.append(
            FiscalWatchContractMatch(
                contract_id=contract.id,
                organization_id=organization_id,
                room_id=contract.room_id,
                organization_alert_id=alert.id,
            )
        )
        existing.add(alert.id)

    if pending:
        session.add_all(pending)
    contract.last_evaluated_at = datetime.now(UTC)
    session.commit()

    matches = list_contract_matches(session, organization_id, contract_id)
    return FiscalWatchContractEvaluationResponse(
        contract=_contract_response(session, contract),
        new_match_count=len(pending),
        total_match_count=len(matches),
        matches=matches,
        note=(
            "Matches are deterministic references to governed organization alerts. "
            "They do not constitute a credit rating, solvency assessment, or prediction."
        ),
    )


def list_contract_matches(
    session: Session,
    organization_id: uuid.UUID,
    contract_id: uuid.UUID,
) -> list[FiscalWatchContractMatchResponse]:
    rows = session.execute(
        select(FiscalWatchContractMatch, OrganizationAlert, State)
        .join(
            OrganizationAlert,
            OrganizationAlert.id == FiscalWatchContractMatch.organization_alert_id,
        )
        .join(State, State.id == OrganizationAlert.state_id)
        .where(
            FiscalWatchContractMatch.organization_id == organization_id,
            FiscalWatchContractMatch.contract_id == contract_id,
        )
        .order_by(FiscalWatchContractMatch.matched_at.desc())
    ).all()
    return [_match_response(match, alert, state) for match, alert, state in rows]
