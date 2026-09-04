from __future__ import annotations

import hashlib
import json
import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from gaiafaac_api.database.customer_models import OrganizationAlert
from gaiafaac_api.database.evidence_room_models import (
    EvidenceRoom,
    EvidenceRoomEvidence,
    EvidenceRoomNote,
)
from gaiafaac_api.database.ledger_models import FiscalEvent
from gaiafaac_api.database.models import SourceDocument, User
from gaiafaac_api.evidence_room_schemas import (
    EvidenceReferenceCreateRequest,
    EvidenceRoomDetail,
    EvidenceRoomEvidenceResponse,
    EvidenceRoomNoteResponse,
    EvidenceRoomSummary,
)
from gaiafaac_api.services.decision_packet import decision_packet
from gaiafaac_api.services.fiscal_proof import get_fiscal_proof


def _canonical_hash(value: dict[str, Any]) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _summary(session: Session, room: EvidenceRoom) -> EvidenceRoomSummary:
    evidence_count = (
        session.scalar(
            select(func.count())
            .select_from(EvidenceRoomEvidence)
            .where(EvidenceRoomEvidence.room_id == room.id)
        )
        or 0
    )
    note_count = (
        session.scalar(
            select(func.count())
            .select_from(EvidenceRoomNote)
            .where(EvidenceRoomNote.room_id == room.id)
        )
        or 0
    )
    return EvidenceRoomSummary(
        id=room.id,
        title=room.title,
        description=room.description,
        decision_question=room.decision_question,
        jurisdictions=list(room.jurisdictions or []),
        evidence_domains=list(room.evidence_domains or []),
        baseline_date=room.baseline_date,
        evidence_cutoff=room.evidence_cutoff,
        status=room.status,
        created_by_user_id=room.created_by_user_id,
        created_at=room.created_at,
        updated_at=room.updated_at,
        evidence_count=evidence_count,
        note_count=note_count,
    )


def list_rooms(session: Session, organization_id: uuid.UUID) -> list[EvidenceRoomSummary]:
    rooms = session.scalars(
        select(EvidenceRoom)
        .where(EvidenceRoom.organization_id == organization_id)
        .order_by(EvidenceRoom.created_at.desc())
    ).all()
    return [_summary(session, room) for room in rooms]


def get_room_row(
    session: Session,
    organization_id: uuid.UUID,
    room_id: uuid.UUID,
) -> EvidenceRoom | None:
    return session.scalar(
        select(EvidenceRoom).where(
            EvidenceRoom.id == room_id,
            EvidenceRoom.organization_id == organization_id,
        )
    )


def get_room(
    session: Session,
    organization_id: uuid.UUID,
    room_id: uuid.UUID,
) -> EvidenceRoomDetail | None:
    room = get_room_row(session, organization_id, room_id)
    if room is None:
        return None
    summary = _summary(session, room)
    evidence_rows = session.scalars(
        select(EvidenceRoomEvidence)
        .where(EvidenceRoomEvidence.room_id == room.id)
        .order_by(EvidenceRoomEvidence.captured_at, EvidenceRoomEvidence.id)
    ).all()
    note_rows = session.scalars(
        select(EvidenceRoomNote)
        .where(EvidenceRoomNote.room_id == room.id)
        .order_by(EvidenceRoomNote.created_at, EvidenceRoomNote.id)
    ).all()
    return EvidenceRoomDetail(
        **summary.model_dump(),
        evidence=[
            EvidenceRoomEvidenceResponse(
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
            for row in evidence_rows
        ],
        notes=[
            EvidenceRoomNoteResponse(
                id=row.id,
                author_user_id=row.author_user_id,
                body=row.body,
                created_at=row.created_at,
                updated_at=row.updated_at,
            )
            for row in note_rows
        ],
    )


def create_room(
    session: Session,
    organization_id: uuid.UUID,
    user: User,
    *,
    title: str,
    description: str | None,
    decision_question: str | None = None,
    jurisdictions: list[str] | None = None,
    evidence_domains: list[str] | None = None,
    baseline_date: date | None = None,
    evidence_cutoff: datetime | None = None,
) -> EvidenceRoomSummary:
    room = EvidenceRoom(
        organization_id=organization_id,
        created_by_user_id=user.id,
        title=title.strip(),
        description=description.strip() if description else None,
        decision_question=decision_question.strip() if decision_question else None,
        jurisdictions=sorted({item.strip() for item in jurisdictions or [] if item.strip()}),
        evidence_domains=sorted(
            {item.strip().lower() for item in evidence_domains or [] if item.strip()}
        ),
        baseline_date=baseline_date,
        evidence_cutoff=evidence_cutoff,
    )
    session.add(room)
    session.commit()
    session.refresh(room)
    return _summary(session, room)


def update_decision_context(
    session: Session,
    organization_id: uuid.UUID,
    room_id: uuid.UUID,
    *,
    decision_question: str | None,
    jurisdictions: list[str],
    evidence_domains: list[str],
    baseline_date: date | None,
    evidence_cutoff: datetime | None,
) -> EvidenceRoomSummary | None:
    room = get_room_row(session, organization_id, room_id)
    if room is None or room.status == "archived":
        return None
    room.decision_question = decision_question.strip() if decision_question else None
    room.jurisdictions = sorted({item.strip() for item in jurisdictions if item.strip()})
    room.evidence_domains = sorted(
        {item.strip().lower() for item in evidence_domains if item.strip()}
    )
    room.baseline_date = baseline_date
    room.evidence_cutoff = evidence_cutoff
    session.commit()
    session.refresh(room)
    return _summary(session, room)


def set_room_status(
    session: Session,
    organization_id: uuid.UUID,
    room_id: uuid.UUID,
    room_status: str,
) -> EvidenceRoomSummary | None:
    room = get_room_row(session, organization_id, room_id)
    if room is None:
        return None
    room.status = room_status
    session.commit()
    session.refresh(room)
    return _summary(session, room)


def _snapshot_organization_alert(
    session: Session,
    organization_id: uuid.UUID,
    reference_id: str,
) -> tuple[str | None, str | None, dict[str, Any]] | None:
    try:
        alert_id = uuid.UUID(reference_id)
    except ValueError:
        return None
    alert = session.scalar(
        select(OrganizationAlert).where(
            OrganizationAlert.id == alert_id,
            OrganizationAlert.organization_id == organization_id,
        )
    )
    if alert is None:
        return None
    snapshot = {
        "id": str(alert.id),
        "state_id": str(alert.state_id),
        "event_key": alert.event_key,
        "source_kind": alert.source_kind,
        "source_event_id": alert.source_event_id,
        "event_type": alert.event_type,
        "severity": alert.severity,
        "occurred_at": alert.occurred_at.isoformat(),
        "payload": alert.payload,
    }
    return f"/watchlists/organization/alerts#{alert.id}", None, snapshot


def _snapshot_fiscal_event(
    session: Session,
    reference_id: str,
) -> tuple[str | None, str | None, dict[str, Any]] | None:
    fiscal_event = session.get(FiscalEvent, reference_id)
    if fiscal_event is None:
        return None
    snapshot = {
        "event_id": fiscal_event.event_id,
        "state_id": str(fiscal_event.state_id),
        "event_type": fiscal_event.event_type,
        "severity": str(fiscal_event.severity),
        "effective_at": fiscal_event.effective_at.isoformat(),
        "detected_at": fiscal_event.detected_at.isoformat(),
        "evidence_status": str(fiscal_event.evidence_status),
        "evidence_ids": list(fiscal_event.evidence_ids),
        "calculation": dict(fiscal_event.calculation),
        "explanation": fiscal_event.explanation,
        "fiscal_state_id": fiscal_event.fiscal_state_id,
        "methodology_version": fiscal_event.methodology_version,
    }
    return f"/events?event_id={fiscal_event.event_id}", None, snapshot


def _snapshot_source(
    session: Session,
    reference_id: str,
) -> tuple[str | None, str | None, dict[str, Any]] | None:
    source = session.scalar(
        select(SourceDocument).where(
            SourceDocument.sha256 == reference_id.lower(),
            SourceDocument.is_demo.is_(False),
        )
    )
    if source is None:
        return None
    snapshot = {
        "id": str(source.id),
        "source_organization": source.source_organization,
        "source_url": source.source_url,
        "original_filename": source.original_filename,
        "sha256": source.sha256,
        "publication_date": (
            source.publication_date.isoformat() if source.publication_date else None
        ),
        "document_version": source.document_version,
        "source_status": str(source.source_status),
    }
    return source.source_url, source.sha256, snapshot


def _snapshot_fiscal_proof(
    session: Session,
    reference_id: str,
    state_slug: str | None,
    revenue_month: date | None,
) -> tuple[str | None, str | None, dict[str, Any]] | None:
    if state_slug is None or revenue_month is None:
        return None
    proof = get_fiscal_proof(
        session,
        state_slug=state_slug,
        revenue_month=revenue_month,
    )
    if proof is None or proof.proof_id != reference_id:
        return None
    snapshot = proof.model_dump(mode="json")
    return (
        f"/fiscal-proof/{proof.state_slug}/{proof.revenue_month.isoformat()}",
        proof.source.sha256,
        snapshot,
    )


def _snapshot_decision_packet(
    session: Session,
    reference_id: str,
    state_slug: str | None,
    year: int | None,
) -> tuple[str | None, str | None, dict[str, Any]] | None:
    if state_slug is None or year is None:
        return None
    expected_id = f"decision-packet:{state_slug}:{year}"
    if reference_id != expected_id:
        return None
    packet = decision_packet(session, state_slug=state_slug, year=year)
    if packet is None:
        return None
    snapshot = packet.model_dump(mode="json")
    source_hashes = sorted(
        {month.source_sha256 for month in packet.months}
        | {record.source_sha256 for record in packet.igr_records}
    )
    snapshot["captured_source_sha256s"] = source_hashes
    return f"/decision-packet/{state_slug}?year={year}", None, snapshot


def _resolve_reference(
    session: Session,
    organization_id: uuid.UUID,
    request: EvidenceReferenceCreateRequest,
) -> tuple[str | None, str | None, dict[str, Any]] | None:
    if request.reference_kind == "organization_alert":
        return _snapshot_organization_alert(
            session,
            organization_id,
            request.reference_id,
        )
    if request.reference_kind == "fiscal_event":
        return _snapshot_fiscal_event(session, request.reference_id)
    if request.reference_kind == "source":
        return _snapshot_source(session, request.reference_id)
    if request.reference_kind == "fiscal_proof":
        return _snapshot_fiscal_proof(
            session,
            request.reference_id,
            request.state_slug,
            request.revenue_month,
        )
    if request.reference_kind == "decision_packet":
        return _snapshot_decision_packet(
            session,
            request.reference_id,
            request.state_slug,
            request.year,
        )
    return None


def _evidence_response(row: EvidenceRoomEvidence) -> EvidenceRoomEvidenceResponse:
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


def capture_reference(
    session: Session,
    organization_id: uuid.UUID,
    room_id: uuid.UUID,
    user: User,
    request: EvidenceReferenceCreateRequest,
) -> EvidenceRoomEvidenceResponse | None:
    room = get_room_row(session, organization_id, room_id)
    if room is None or room.status == "archived":
        return None
    existing = session.scalar(
        select(EvidenceRoomEvidence).where(
            EvidenceRoomEvidence.room_id == room_id,
            EvidenceRoomEvidence.reference_kind == request.reference_kind,
            EvidenceRoomEvidence.reference_id == request.reference_id,
        )
    )
    if existing is not None:
        return _evidence_response(existing)

    resolved = _resolve_reference(session, organization_id, request)
    if resolved is None:
        return None
    reference_uri, source_sha256, snapshot = resolved
    record = {
        "reference_kind": request.reference_kind,
        "reference_id": request.reference_id,
        "reference_uri": reference_uri,
        "source_sha256": source_sha256,
        "snapshot": snapshot,
    }
    row = EvidenceRoomEvidence(
        room_id=room_id,
        captured_by_user_id=user.id,
        reference_kind=request.reference_kind,
        reference_id=request.reference_id,
        reference_uri=reference_uri,
        source_sha256=source_sha256,
        snapshot=snapshot,
        record_sha256=_canonical_hash(record),
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return _evidence_response(row)


def add_note(
    session: Session,
    organization_id: uuid.UUID,
    room_id: uuid.UUID,
    user: User,
    body: str,
) -> EvidenceRoomNoteResponse | None:
    room = get_room_row(session, organization_id, room_id)
    if room is None or room.status == "archived":
        return None
    row = EvidenceRoomNote(
        room_id=room_id,
        author_user_id=user.id,
        body=body.strip(),
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return EvidenceRoomNoteResponse(
        id=row.id,
        author_user_id=row.author_user_id,
        body=row.body,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def update_note(
    session: Session,
    organization_id: uuid.UUID,
    room_id: uuid.UUID,
    note_id: uuid.UUID,
    user: User,
    body: str,
) -> EvidenceRoomNoteResponse | None:
    if get_room_row(session, organization_id, room_id) is None:
        return None
    row = session.scalar(
        select(EvidenceRoomNote).where(
            EvidenceRoomNote.id == note_id,
            EvidenceRoomNote.room_id == room_id,
            EvidenceRoomNote.author_user_id == user.id,
        )
    )
    if row is None:
        return None
    row.body = body.strip()
    session.commit()
    session.refresh(row)
    return EvidenceRoomNoteResponse(
        id=row.id,
        author_user_id=row.author_user_id,
        body=row.body,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )
