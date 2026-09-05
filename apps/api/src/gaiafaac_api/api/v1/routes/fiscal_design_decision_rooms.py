from __future__ import annotations

import uuid
from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from gaiafaac_api.api.v1.routes.evidence_rooms import require_decision_rooms
from gaiafaac_api.customer_auth import CurrentCustomer, DatabaseSession
from gaiafaac_api.database.evidence_room_models import EvidenceRoomEvidence
from gaiafaac_api.evidence_room_schemas import EvidenceRoomEvidenceResponse
from gaiafaac_api.fiscal_design_schemas import FiscalDesignPersistRequest
from gaiafaac_api.services.evidence_rooms import _canonical_hash, get_room_row
from gaiafaac_api.services.fiscal_design import fiscal_design

router = APIRouter(prefix="/decision-rooms", tags=["fiscal design"])


def _response(row: EvidenceRoomEvidence) -> EvidenceRoomEvidenceResponse:
    return EvidenceRoomEvidenceResponse(
        id=row.id,
        reference_kind=row.reference_kind,
        reference_id=row.reference_id,
        reference_uri=row.reference_uri,
        source_sha256=row.source_sha256,
        record_sha256=row.record_sha256,
        snapshot=dict(row.snapshot),
        captured_by_user_id=row.captured_by_user_id,
        captured_at=row.captured_at,
    )


@router.post(
    "/{room_id}/fiscal-design-scenarios",
    response_model=EvidenceRoomEvidenceResponse,
    status_code=status.HTTP_201_CREATED,
)
def persist_fiscal_design_scenario(
    room_id: uuid.UUID,
    payload: FiscalDesignPersistRequest,
    session: DatabaseSession,
    user: CurrentCustomer,
) -> EvidenceRoomEvidenceResponse:
    """Recompute a scenario over governed evidence and freeze it into a Decision Room."""

    organization_id, _membership = require_decision_rooms(session, user)
    room = get_room_row(session, organization_id, room_id)
    if room is None or room.status == "archived":
        raise HTTPException(status_code=404, detail="Decision Room not found or archived.")

    scenario = fiscal_design(
        session,
        state_slug=payload.state_slug,
        year=payload.year,
        faac_shock_pct=payload.faac_shock_pct,
        igr_shock_pct=payload.igr_shock_pct,
        reserve_share_pct=payload.reserve_share_pct,
        debt_change_pct=payload.debt_change_pct,
        debt_service_change_pct=payload.debt_service_change_pct,
        expenditure_change_pct=payload.expenditure_change_pct,
        capital_spending_change_pct=payload.capital_spending_change_pct,
        inflation_assumption_pct=payload.inflation_assumption_pct,
    )
    if scenario is None:
        raise HTTPException(
            status_code=404,
            detail="No governed fiscal evidence exists for this state and year.",
        )

    existing = session.scalar(
        select(EvidenceRoomEvidence).where(
            EvidenceRoomEvidence.room_id == room.id,
            EvidenceRoomEvidence.reference_kind == "fiscal_design_scenario",
            EvidenceRoomEvidence.reference_id == scenario.scenario_gaia_id,
        )
    )
    if existing is not None:
        return _response(existing)

    snapshot = scenario.model_dump(mode="json")
    source_hashes = sorted({item.source_sha256 for item in scenario.evidence})
    snapshot["captured_source_sha256s"] = source_hashes
    query = urlencode(
        {
            "state": scenario.state_slug,
            "year": scenario.year,
            "faacShock": scenario.faac_shock_pct,
            "igrShock": scenario.igr_shock_pct,
            "reserveShare": scenario.reserve_share_pct,
            "debtChange": scenario.debt_change_pct,
            "debtServiceChange": scenario.debt_service_change_pct,
            "expenditureChange": scenario.expenditure_change_pct,
            "capitalSpendingChange": scenario.capital_spending_change_pct,
            "inflationAssumption": scenario.inflation_assumption_pct,
        }
    )
    reference_uri = f"/fiscal-design?{query}"
    record = {
        "reference_kind": "fiscal_design_scenario",
        "reference_id": scenario.scenario_gaia_id,
        "reference_uri": reference_uri,
        "source_sha256": None,
        "snapshot": snapshot,
    }
    row = EvidenceRoomEvidence(
        room_id=room.id,
        captured_by_user_id=user.id,
        reference_kind="fiscal_design_scenario",
        reference_id=scenario.scenario_gaia_id,
        reference_uri=reference_uri,
        source_sha256=None,
        snapshot=snapshot,
        record_sha256=_canonical_hash(record),
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return _response(row)
