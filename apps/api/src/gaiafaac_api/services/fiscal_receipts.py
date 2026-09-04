from __future__ import annotations

import hashlib
import json
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.evidence_room_models import (
    EvidenceRoomEvidence,
    FiscalReceipt,
)
from gaiafaac_api.database.models import User
from gaiafaac_api.fiscal_receipt_schemas import (
    FiscalReceiptResponse,
    FiscalReceiptSummary,
    FiscalReceiptVerification,
)
from gaiafaac_api.services.evidence_rooms import get_room_row

_METHODOLOGY_VERSION = "fiscal-receipt-v2"
_CONTENT_SCHEMA = "fiscal-receipt-content-v1"


def _canonical_json(value: dict[str, Any]) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    ).encode("utf-8")


def _sha256(value: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _receipt_response(row: FiscalReceipt) -> FiscalReceiptResponse:
    return FiscalReceiptResponse(
        id=row.id,
        room_id=row.room_id,
        organization_id=row.organization_id,
        created_by_user_id=row.created_by_user_id,
        predecessor_receipt_id=row.predecessor_receipt_id,
        triggering_match_id=row.triggering_match_id,
        evidence_cutoff=row.evidence_cutoff,
        methodology_version=row.methodology_version,
        receipt_sha256=row.receipt_sha256,
        manifest=dict(row.manifest),
        created_at=row.created_at,
    )


def _summary(row: FiscalReceipt) -> FiscalReceiptSummary:
    public = dict(row.public_manifest)
    return FiscalReceiptSummary(
        id=row.id,
        room_id=row.room_id,
        predecessor_receipt_id=row.predecessor_receipt_id,
        triggering_match_id=row.triggering_match_id,
        evidence_cutoff=row.evidence_cutoff,
        methodology_version=row.methodology_version,
        receipt_sha256=row.receipt_sha256,
        evidence_count=int(public.get("evidence_count", 0)),
        created_at=row.created_at,
    )


def _evidence_rows(
    session: Session,
    room_id: uuid.UUID,
    cutoff: datetime | None,
) -> list[EvidenceRoomEvidence]:
    statement = select(EvidenceRoomEvidence).where(EvidenceRoomEvidence.room_id == room_id)
    if cutoff is not None:
        statement = statement.where(EvidenceRoomEvidence.captured_at <= cutoff)
    return list(
        session.scalars(
            statement.order_by(EvidenceRoomEvidence.captured_at, EvidenceRoomEvidence.id)
        )
    )


def _latest_receipt(
    session: Session,
    organization_id: uuid.UUID,
    room_id: uuid.UUID,
) -> FiscalReceipt | None:
    return session.scalar(
        select(FiscalReceipt)
        .where(
            FiscalReceipt.organization_id == organization_id,
            FiscalReceipt.room_id == room_id,
        )
        .order_by(FiscalReceipt.created_at.desc(), FiscalReceipt.id.desc())
    )


def generate_receipt(
    session: Session,
    organization_id: uuid.UUID,
    room_id: uuid.UUID,
    user: User,
) -> FiscalReceiptResponse | None:
    room = get_room_row(session, organization_id, room_id)
    if room is None:
        return None

    rows = _evidence_rows(session, room.id, room.evidence_cutoff)
    effective_cutoff = room.evidence_cutoff
    if effective_cutoff is None and rows:
        effective_cutoff = max(row.captured_at for row in rows)

    evidence = [
        {
            "reference_kind": row.reference_kind,
            "reference_id": row.reference_id,
            "reference_uri": row.reference_uri,
            "source_sha256": row.source_sha256,
            "record_sha256": row.record_sha256,
            "captured_at": row.captured_at.isoformat(),
            "snapshot": dict(row.snapshot),
        }
        for row in rows
    ]
    source_hashes = sorted({row.source_sha256 for row in rows if row.source_sha256})
    record_hashes = [row.record_sha256 for row in rows]
    evidence_kinds = [row.reference_kind for row in rows]

    content = {
        "schema": _CONTENT_SCHEMA,
        "decision_room_id": str(room.id),
        "decision_room_title": room.title,
        "decision_question": room.decision_question,
        "jurisdictions": list(room.jurisdictions or []),
        "evidence_domains": list(room.evidence_domains or []),
        "baseline_date": room.baseline_date.isoformat() if room.baseline_date else None,
        "evidence_cutoff": effective_cutoff.isoformat() if effective_cutoff else None,
        "room_status": room.status,
        "evidence_count": len(evidence),
        "evidence": evidence,
        "source_sha256s": source_hashes,
        "evidence_record_sha256s": record_hashes,
        "missing_evidence": [],
        "assumptions": [],
    }
    content_sha256 = _sha256(content)
    predecessor = _latest_receipt(session, organization_id, room.id)

    if (
        predecessor is not None
        and not room.review_required
        and str(predecessor.manifest.get("content_sha256") or "") == content_sha256
    ):
        return _receipt_response(predecessor)

    triggering_match_id = room.review_trigger_match_id if room.review_required else None
    lineage = {
        "predecessor_receipt_id": str(predecessor.id) if predecessor else None,
        "predecessor_receipt_sha256": predecessor.receipt_sha256 if predecessor else None,
        "triggering_watch_contract_match_id": (
            str(triggering_match_id) if triggering_match_id else None
        ),
    }
    manifest = {
        **content,
        "schema": _METHODOLOGY_VERSION,
        "methodology_version": _METHODOLOGY_VERSION,
        "content_sha256": content_sha256,
        "lineage": lineage,
    }
    receipt_sha256 = _sha256(manifest)

    existing = session.scalar(
        select(FiscalReceipt).where(
            FiscalReceipt.room_id == room.id,
            FiscalReceipt.receipt_sha256 == receipt_sha256,
        )
    )
    if existing is not None:
        return _receipt_response(existing)

    public_manifest = {
        "schema": _METHODOLOGY_VERSION,
        "jurisdictions": list(room.jurisdictions or []),
        "evidence_domains": list(room.evidence_domains or []),
        "evidence_cutoff": effective_cutoff.isoformat() if effective_cutoff else None,
        "evidence_count": len(rows),
        "source_sha256s": source_hashes,
        "evidence_record_sha256s": record_hashes,
        "evidence_kinds": evidence_kinds,
        "content_sha256": content_sha256,
        "predecessor_receipt_id": lineage["predecessor_receipt_id"],
        "predecessor_receipt_sha256": lineage["predecessor_receipt_sha256"],
        "triggering_watch_contract_match_id": lineage[
            "triggering_watch_contract_match_id"
        ],
    }
    row = FiscalReceipt(
        organization_id=organization_id,
        room_id=room.id,
        created_by_user_id=user.id,
        predecessor_receipt_id=predecessor.id if predecessor else None,
        triggering_match_id=triggering_match_id,
        evidence_cutoff=effective_cutoff,
        methodology_version=_METHODOLOGY_VERSION,
        manifest=manifest,
        public_manifest=public_manifest,
        receipt_sha256=receipt_sha256,
    )
    session.add(row)

    if room.review_required:
        room.review_required = False
        room.last_reviewed_at = datetime.now(UTC)
        room.reviewed_by_user_id = user.id

    session.commit()
    session.refresh(row)
    return _receipt_response(row)


def list_receipts(
    session: Session,
    organization_id: uuid.UUID,
    room_id: uuid.UUID,
) -> list[FiscalReceiptSummary] | None:
    room = get_room_row(session, organization_id, room_id)
    if room is None:
        return None
    rows = session.scalars(
        select(FiscalReceipt)
        .where(
            FiscalReceipt.organization_id == organization_id,
            FiscalReceipt.room_id == room_id,
        )
        .order_by(FiscalReceipt.created_at.desc())
    ).all()
    return [_summary(row) for row in rows]


def get_private_receipt(
    session: Session,
    organization_id: uuid.UUID,
    receipt_id: uuid.UUID,
) -> FiscalReceiptResponse | None:
    row = session.scalar(
        select(FiscalReceipt).where(
            FiscalReceipt.id == receipt_id,
            FiscalReceipt.organization_id == organization_id,
        )
    )
    return _receipt_response(row) if row is not None else None


def verify_receipt(
    session: Session,
    receipt_id: uuid.UUID,
) -> FiscalReceiptVerification | None:
    row = session.get(FiscalReceipt, receipt_id)
    if row is None:
        return None
    public = dict(row.public_manifest)
    predecessor_id = public.get("predecessor_receipt_id")
    triggering_match_id = public.get("triggering_watch_contract_match_id")
    return FiscalReceiptVerification(
        id=row.id,
        receipt_sha256=row.receipt_sha256,
        methodology_version=row.methodology_version,
        created_at=row.created_at,
        evidence_cutoff=row.evidence_cutoff,
        jurisdictions=list(public.get("jurisdictions") or []),
        evidence_domains=list(public.get("evidence_domains") or []),
        evidence_count=int(public.get("evidence_count", 0)),
        source_sha256s=list(public.get("source_sha256s") or []),
        evidence_record_sha256s=list(public.get("evidence_record_sha256s") or []),
        evidence_kinds=list(public.get("evidence_kinds") or []),
        predecessor_receipt_id=(uuid.UUID(predecessor_id) if predecessor_id else None),
        predecessor_receipt_sha256=public.get("predecessor_receipt_sha256"),
        triggering_match_id=(uuid.UUID(triggering_match_id) if triggering_match_id else None),
        content_sha256=public.get("content_sha256"),
        statement=(
            "This Fiscal Receipt identifies the Gaia evidence records captured at the "
            "stated evidence boundary, the SHA-256 digest of the canonical manifest, "
            "and any declared predecessor/monitoring lineage."
        ),
        limitations=[
            (
                "It does not certify or approve a lending, investment, procurement, "
                "or policy decision."
            ),
            "It does not make Gaia an official government publisher or credit-rating agency.",
            (
                "It proves the recorded evidence manifest and hashes, not that every "
                "possible source existed or was captured."
            ),
            (
                "Human notes and private organization context are intentionally excluded "
                "from public verification."
            ),
        ],
    )
