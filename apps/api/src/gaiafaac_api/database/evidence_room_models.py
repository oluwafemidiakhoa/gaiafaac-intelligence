from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    event,
    func,
)
from sqlalchemy.orm import Mapped, Mapper, mapped_column

from gaiafaac_api.database.base import Base


class EvidenceRoom(Base):
    """A durable organization decision case file over governed fiscal evidence.

    The historical table name remains ``evidence_rooms`` for backwards
    compatibility. Commercially this is the storage layer for a Gaia Fiscal
    Decision Room: decision context is editable while captured evidence and
    generated receipts are durable records.
    """

    __tablename__ = "evidence_rooms"
    __table_args__ = (
        CheckConstraint(
            "status IN ('open', 'closed', 'archived')",
            name="ck_evidence_room_status",
        ),
        Index("ix_evidence_rooms_org_created", "organization_id", "created_at"),
        Index("ix_evidence_rooms_org_status", "organization_id", "status"),
        Index("ix_evidence_rooms_review_required", "organization_id", "review_required"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    decision_question: Mapped[str | None] = mapped_column(Text)
    jurisdictions: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    evidence_domains: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    baseline_date: Mapped[date | None] = mapped_column(Date)
    evidence_cutoff: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open")
    review_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    review_trigger_match_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("fiscal_watch_contract_matches.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    review_required_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reviewed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class EvidenceRoomEvidence(Base):
    """An append-only, tamper-evident reference captured into a Decision Room."""

    __tablename__ = "evidence_room_evidence"
    __table_args__ = (
        CheckConstraint(
            "reference_kind IN ("
            "'organization_alert', 'fiscal_proof', 'decision_packet', "
            "'fiscal_design_scenario', 'source', 'fiscal_event'"
            ")",
            name="ck_evidence_room_reference_kind",
        ),
        CheckConstraint(
            "source_sha256 IS NULL OR length(source_sha256) = 64",
            name="ck_evidence_room_source_hash",
        ),
        CheckConstraint(
            "length(record_sha256) = 64",
            name="ck_evidence_room_record_hash",
        ),
        UniqueConstraint(
            "room_id",
            "reference_kind",
            "reference_id",
            name="uq_evidence_room_reference",
        ),
        Index("ix_evidence_room_evidence_room_captured", "room_id", "captured_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("evidence_rooms.id", ondelete="CASCADE"), nullable=False, index=True
    )
    captured_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    reference_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    reference_id: Mapped[str] = mapped_column(String(240), nullable=False)
    reference_uri: Mapped[str | None] = mapped_column(Text)
    source_sha256: Mapped[str | None] = mapped_column(String(64))
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    record_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class EvidenceRoomNote(Base):
    """Editable human commentary kept structurally separate from governed evidence."""

    __tablename__ = "evidence_room_notes"
    __table_args__ = (Index("ix_evidence_room_notes_room_created", "room_id", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("evidence_rooms.id", ondelete="CASCADE"), nullable=False, index=True
    )
    author_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class FiscalReceipt(Base):
    """Immutable evidence manifest identifying one Decision Room evidence boundary."""

    __tablename__ = "fiscal_receipts"
    __table_args__ = (
        CheckConstraint("length(receipt_sha256) = 64", name="ck_fiscal_receipt_hash_length"),
        UniqueConstraint("room_id", "receipt_sha256", name="uq_fiscal_receipt_room_hash"),
        Index("ix_fiscal_receipts_org_created", "organization_id", "created_at"),
        Index("ix_fiscal_receipts_room_created", "room_id", "created_at"),
        Index("ix_fiscal_receipts_predecessor", "predecessor_receipt_id"),
        Index("ix_fiscal_receipts_trigger_match", "triggering_match_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    room_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("evidence_rooms.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    predecessor_receipt_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("fiscal_receipts.id", ondelete="RESTRICT"), nullable=True
    )
    triggering_match_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("fiscal_watch_contract_matches.id", ondelete="RESTRICT"), nullable=True
    )
    evidence_cutoff: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    methodology_version: Mapped[str] = mapped_column(
        String(80), nullable=False, default="fiscal-receipt-v2"
    )
    manifest: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    public_manifest: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    receipt_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


def _immutable_reference(_mapper: Mapper[Any], _connection: Any, target: Any) -> None:
    raise ValueError(f"Captured {target.__class__.__name__} records are immutable.")


def _durable_room(_mapper: Mapper[Any], _connection: Any, target: Any) -> None:
    raise ValueError(
        "Decision Rooms are durable case files; archive them instead of deleting them."
    )


event.listen(EvidenceRoomEvidence, "before_update", _immutable_reference)
event.listen(EvidenceRoomEvidence, "before_delete", _immutable_reference)
event.listen(FiscalReceipt, "before_update", _immutable_reference)
event.listen(FiscalReceipt, "before_delete", _immutable_reference)
event.listen(EvidenceRoom, "before_delete", _durable_room)
