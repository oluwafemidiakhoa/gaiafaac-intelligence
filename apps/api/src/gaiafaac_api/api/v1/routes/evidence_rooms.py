from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, status

from gaiafaac_api.customer_auth import CurrentCustomer, DatabaseSession
from gaiafaac_api.evidence_room_schemas import (
    DecisionContextUpdate,
    EvidenceReferenceCreateRequest,
    EvidenceRoomCreateRequest,
    EvidenceRoomDetail,
    EvidenceRoomEvidenceResponse,
    EvidenceRoomNoteCreateRequest,
    EvidenceRoomNoteResponse,
    EvidenceRoomNoteUpdateRequest,
    EvidenceRoomStatusUpdate,
    EvidenceRoomSummary,
)
from gaiafaac_api.services.account import current_plan, membership_for
from gaiafaac_api.services.evidence_rooms import (
    add_note,
    capture_reference,
    create_room,
    get_room,
    list_rooms,
    set_room_status,
    update_decision_context,
    update_note,
)

router = APIRouter(prefix="/evidence-rooms", tags=["evidence rooms"])


def require_decision_rooms(session: DatabaseSession, user: CurrentCustomer):
    if user.organization_id is None:
        raise HTTPException(status_code=403, detail="No customer organization is attached.")
    membership = membership_for(session, user)
    if membership is None:
        raise HTTPException(status_code=403, detail="Organization membership is required.")
    _plan_code, entitlements, _subscription = current_plan(session, user.organization_id)
    if entitlements.max_users <= 1:
        raise HTTPException(
            status_code=403,
            detail="Decision Rooms require the Team or API plan.",
        )
    return user.organization_id, membership


def _require_room_admin(session: DatabaseSession, user: CurrentCustomer) -> uuid.UUID:
    organization_id, membership = require_decision_rooms(session, user)
    if membership.role not in {"owner", "admin"}:
        raise HTTPException(
            status_code=403,
            detail="Organization administrator access is required to change room status.",
        )
    return organization_id


@router.get("", response_model=list[EvidenceRoomSummary])
def evidence_rooms(session: DatabaseSession, user: CurrentCustomer) -> list[EvidenceRoomSummary]:
    organization_id, _membership = require_decision_rooms(session, user)
    return list_rooms(session, organization_id)


@router.post("", response_model=EvidenceRoomSummary, status_code=status.HTTP_201_CREATED)
def create_evidence_room(
    payload: EvidenceRoomCreateRequest,
    session: DatabaseSession,
    user: CurrentCustomer,
) -> EvidenceRoomSummary:
    organization_id, _membership = require_decision_rooms(session, user)
    return create_room(
        session,
        organization_id,
        user,
        title=payload.title,
        description=payload.description,
        decision_question=payload.decision_question,
        jurisdictions=payload.jurisdictions,
        evidence_domains=payload.evidence_domains,
        baseline_date=payload.baseline_date,
        evidence_cutoff=payload.evidence_cutoff,
    )


@router.get("/{room_id}", response_model=EvidenceRoomDetail)
def evidence_room(
    room_id: uuid.UUID,
    session: DatabaseSession,
    user: CurrentCustomer,
) -> EvidenceRoomDetail:
    organization_id, _membership = require_decision_rooms(session, user)
    room = get_room(session, organization_id, room_id)
    if room is None:
        raise HTTPException(status_code=404, detail="Decision Room not found.")
    return room


@router.patch("/{room_id}/decision-context", response_model=EvidenceRoomSummary)
def change_decision_context(
    room_id: uuid.UUID,
    payload: DecisionContextUpdate,
    session: DatabaseSession,
    user: CurrentCustomer,
) -> EvidenceRoomSummary:
    organization_id, _membership = require_decision_rooms(session, user)
    room = update_decision_context(
        session,
        organization_id,
        room_id,
        decision_question=payload.decision_question,
        jurisdictions=payload.jurisdictions,
        evidence_domains=payload.evidence_domains,
        baseline_date=payload.baseline_date,
        evidence_cutoff=payload.evidence_cutoff,
    )
    if room is None:
        raise HTTPException(status_code=404, detail="Decision Room not found or archived.")
    return room


@router.patch("/{room_id}/status", response_model=EvidenceRoomSummary)
def change_evidence_room_status(
    room_id: uuid.UUID,
    payload: EvidenceRoomStatusUpdate,
    session: DatabaseSession,
    user: CurrentCustomer,
) -> EvidenceRoomSummary:
    organization_id = _require_room_admin(session, user)
    room = set_room_status(session, organization_id, room_id, payload.status)
    if room is None:
        raise HTTPException(status_code=404, detail="Decision Room not found.")
    return room


@router.post(
    "/{room_id}/evidence",
    response_model=EvidenceRoomEvidenceResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_evidence_to_room(
    room_id: uuid.UUID,
    payload: EvidenceReferenceCreateRequest,
    session: DatabaseSession,
    user: CurrentCustomer,
) -> EvidenceRoomEvidenceResponse:
    organization_id, _membership = require_decision_rooms(session, user)
    evidence = capture_reference(session, organization_id, room_id, user, payload)
    if evidence is None:
        raise HTTPException(
            status_code=404,
            detail="Decision Room or governed evidence reference was not found.",
        )
    return evidence


@router.post(
    "/{room_id}/notes",
    response_model=EvidenceRoomNoteResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_room_note(
    room_id: uuid.UUID,
    payload: EvidenceRoomNoteCreateRequest,
    session: DatabaseSession,
    user: CurrentCustomer,
) -> EvidenceRoomNoteResponse:
    organization_id, _membership = require_decision_rooms(session, user)
    note = add_note(session, organization_id, room_id, user, payload.body)
    if note is None:
        raise HTTPException(status_code=404, detail="Decision Room not found or archived.")
    return note


@router.patch("/{room_id}/notes/{note_id}", response_model=EvidenceRoomNoteResponse)
def edit_room_note(
    room_id: uuid.UUID,
    note_id: uuid.UUID,
    payload: EvidenceRoomNoteUpdateRequest,
    session: DatabaseSession,
    user: CurrentCustomer,
) -> EvidenceRoomNoteResponse:
    organization_id, _membership = require_decision_rooms(session, user)
    note = update_note(session, organization_id, room_id, note_id, user, payload.body)
    if note is None:
        raise HTTPException(status_code=404, detail="Editable room note not found.")
    return note
