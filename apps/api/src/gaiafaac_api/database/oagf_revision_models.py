from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from gaiafaac_api.database.base import Base
from gaiafaac_api.database.models import IdMixin, TimestampMixin


class OagfArchiveObject(IdMixin, TimestampMixin, Base):
    """Content-addressed OAGF source bytes retained durably in Postgres."""

    __tablename__ = "oagf_archive_objects"
    __table_args__ = (
        UniqueConstraint("sha256", name="uq_oagf_archive_sha256"),
        Index("ix_oagf_archive_created_at", "created_at"),
    )

    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    content: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    byte_length: Mapped[int] = mapped_column(Integer, nullable=False)
    content_type: Mapped[str] = mapped_column(String(160), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)


class OagfRevisionCase(IdMixin, TimestampMixin, Base):
    """Human-action case created when an official OAGF publication changes bytes."""

    __tablename__ = "oagf_revision_cases"
    __table_args__ = (
        UniqueConstraint("discovery_record_id", name="uq_oagf_revision_discovery_record"),
        Index("ix_oagf_revision_case_status", "status"),
        Index("ix_oagf_revision_case_period", "reporting_period_id"),
    )

    discovery_record_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("oagf_discovery_records.id", ondelete="RESTRICT"), nullable=False
    )
    previous_record_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("oagf_discovery_records.id", ondelete="RESTRICT"), nullable=False
    )
    source_document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("source_documents.id", ondelete="RESTRICT"), nullable=False
    )
    previous_source_document_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("source_documents.id", ondelete="SET NULL")
    )
    reporting_period_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("reporting_periods.id", ondelete="SET NULL")
    )
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="pending_review")
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolution_code: Mapped[str | None] = mapped_column(String(80))
    review_note: Mapped[str | None] = mapped_column(Text)
