from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    CheckConstraint,
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
    """A durable organization case file over governed fiscal evidence."""

    __tablename__ = "evidence_rooms"
    __table_args__ = (
        CheckConstraint(
            "status IN ('open', 'closed', 'archived')",
            name="ck_evidence_room_status",
        ),
        Index("ix_evidence_rooms_org_created", "organization_id", "created_at"),
        Index("ix_evidence_rooms_org_status", "organization_id", "status"),
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
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class EvidenceRoomEvidence(Base):
    """An append-only, tamper-evident reference captured into an Evidence Room."""

    __tablename__ = "evidence_room_evidence"
    __table_args__ = (
        CheckConstraint(
            "reference_kind IN ("
            "'organization_alert', 'fiscal_proof', 'decision_packet', "
            "'source', 'fiscal_event'"
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


def _immutable_reference(_mapper: Mapper[Any], _connection: Any, target: Any) -> None:
    raise ValueError(f"Captured {target.__class__.__name__} records are immutable.")


def _durable_room(_mapper: Mapper[Any], _connection: Any, target: Any) -> None:
    raise ValueError("Evidence Rooms are durable case files; archive them instead of deleting them.")


event.listen(EvidenceRoomEvidence, "before_update", _immutable_reference)
event.listen(EvidenceRoomEvidence, "before_delete", _immutable_reference)
event.listen(EvidenceRoom, "before_delete", _durable_room)
