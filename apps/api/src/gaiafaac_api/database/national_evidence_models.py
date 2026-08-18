from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Date,
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


class NationalEvidenceSyncRun(IdMixin, TimestampMixin, Base):
    """One auditable pass over configured official national FAAC sources."""

    __tablename__ = "national_evidence_sync_runs"

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    options: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    candidates_discovered: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    candidates_archived: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    imported: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    deferred: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    quarantined: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    duplicates: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    errors: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)


class NationalEvidenceCandidate(IdMixin, TimestampMixin, Base):
    """Immutable official bytes plus deterministic extraction/provenance state."""

    __tablename__ = "national_evidence_candidates"
    __table_args__ = (
        CheckConstraint("length(sha256) = 64", name="ck_national_candidate_sha256_length"),
        CheckConstraint("byte_length > 0", name="ck_national_candidate_positive_bytes"),
        UniqueConstraint("sha256", name="uq_national_candidate_sha256"),
        Index("ix_national_candidate_status", "status"),
        Index("ix_national_candidate_period", "reporting_period_id"),
        Index("ix_national_candidate_source_url", "source_url"),
    )

    first_seen_run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("national_evidence_sync_runs.id", ondelete="RESTRICT"), nullable=False
    )
    last_seen_run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("national_evidence_sync_runs.id", ondelete="RESTRICT"), nullable=False
    )
    source_document_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("source_documents.id", ondelete="SET NULL")
    )
    extraction_run_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("extraction_runs.id", ondelete="SET NULL")
    )
    reporting_period_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("reporting_periods.id", ondelete="SET NULL")
    )

    source_organization: Mapped[str] = mapped_column(String(200), nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    publication_date: Mapped[date | None] = mapped_column(Date)
    content_type: Mapped[str] = mapped_column(String(160), nullable=False)
    byte_length: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    content: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)

    status: Mapped[str] = mapped_column(String(40), nullable=False)
    reason_code: Mapped[str | None] = mapped_column(String(120))
    details: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    extracted_claims: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    disbursement_month: Mapped[date | None] = mapped_column(Date)
    allocation_period_month: Mapped[date | None] = mapped_column(Date)

    source_type: Mapped[str] = mapped_column(
        String(80), nullable=False, default="official_government_press_release"
    )
    source_authority: Mapped[str] = mapped_column(
        String(40), nullable=False, default="official_secondary"
    )
    canonical_source_status: Mapped[str] = mapped_column(
        String(40), nullable=False, default="missing"
    )
