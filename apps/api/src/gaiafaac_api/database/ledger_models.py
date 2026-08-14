from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    event,
    func,
)
from sqlalchemy.orm import Mapped, Mapper, mapped_column

from gaiafaac_api.database.base import Base
from gaiafaac_api.database.enums import EvidenceConflictStatus, EvidenceStatus


def _evidence_status(name: str) -> Enum:
    return Enum(
        EvidenceStatus,
        name=name,
        native_enum=False,
        create_constraint=True,
        values_callable=lambda members: [member.value for member in members],
    )


def _conflict_status(name: str) -> Enum:
    return Enum(
        EvidenceConflictStatus,
        name=name,
        native_enum=False,
        create_constraint=True,
        values_callable=lambda members: [member.value for member in members],
    )


class FiscalClaim(Base):
    """An immutable, source-linked fiscal assertion."""

    __tablename__ = "fiscal_claims"
    __table_args__ = (
        CheckConstraint("length(source_sha256) = 64", name="ck_fiscal_claim_source_hash"),
        CheckConstraint(
            "currency IS NULL OR length(currency) = 3", name="ck_fiscal_claim_currency"
        ),
        Index("ix_fiscal_claims_jurisdiction_period", "state_id", "fiscal_period"),
        Index("ix_fiscal_claims_status", "evidence_status"),
    )

    gaia_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    object_type: Mapped[str] = mapped_column(String(40), nullable=False)
    state_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("states.state_id", ondelete="RESTRICT"), nullable=False
    )
    fiscal_period: Mapped[str] = mapped_column(String(32), nullable=False)
    metric: Mapped[str] = mapped_column(String(120), nullable=False)
    value: Mapped[Decimal | None] = mapped_column(Numeric(30, 6))
    value_text: Mapped[str | None] = mapped_column(String(160))
    unit: Mapped[str] = mapped_column(String(80), nullable=False)
    currency: Mapped[str | None] = mapped_column(String(3))
    source_document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("source_documents.id", ondelete="RESTRICT"), nullable=False
    )
    source_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    source_page: Mapped[int | None]
    source_table: Mapped[str | None] = mapped_column(String(160))
    extraction_method: Mapped[str] = mapped_column(String(40), nullable=False)
    evidence_status: Mapped[EvidenceStatus] = mapped_column(
        _evidence_status("fiscal_claim_evidence_status"), nullable=False
    )
    methodology_version: Mapped[str] = mapped_column(String(32), nullable=False)
    supersedes_gaia_id: Mapped[str | None] = mapped_column(
        ForeignKey("fiscal_claims.gaia_id", ondelete="RESTRICT")
    )
    effective_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class EvidenceVerification(Base):
    __tablename__ = "evidence_verifications"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_gaia_id: Mapped[str] = mapped_column(
        ForeignKey("fiscal_claims.gaia_id", ondelete="CASCADE"), nullable=False, unique=True
    )
    status: Mapped[EvidenceStatus] = mapped_column(
        _evidence_status("evidence_verification_status"), nullable=False
    )
    source_verified: Mapped[bool] = mapped_column(Boolean, nullable=False)
    reconciled: Mapped[bool | None] = mapped_column(Boolean)
    human_reviewed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    published: Mapped[bool] = mapped_column(Boolean, nullable=False)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    methodology_version: Mapped[str] = mapped_column(String(32), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class EvidenceManifest(Base):
    __tablename__ = "evidence_manifests"
    __table_args__ = (
        CheckConstraint("length(payload_sha256) = 64", name="ck_evidence_manifest_hash"),
        UniqueConstraint("subject_gaia_id", "payload_sha256", name="uq_manifest_subject_hash"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subject_gaia_id: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    manifest_version: Mapped[str] = mapped_column(String(80), nullable=False)
    schema_version: Mapped[str] = mapped_column(String(32), nullable=False)
    canonicalization_version: Mapped[str] = mapped_column(String(80), nullable=False)
    hash_algorithm: Mapped[str] = mapped_column(String(20), nullable=False, default="sha256")
    payload_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class FiscalProof(Base):
    __tablename__ = "fiscal_proofs"
    __table_args__ = (CheckConstraint("length(integrity_hash) = 64", name="ck_fiscal_proof_hash"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    gaia_id: Mapped[str] = mapped_column(
        ForeignKey("fiscal_claims.gaia_id", ondelete="RESTRICT"), nullable=False, unique=True
    )
    manifest_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("evidence_manifests.id", ondelete="RESTRICT"), nullable=False, unique=True
    )
    schema_version: Mapped[str] = mapped_column(String(32), nullable=False)
    methodology_version: Mapped[str] = mapped_column(String(32), nullable=False)
    integrity_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    previous_proof_gaia_id: Mapped[str | None] = mapped_column(
        ForeignKey("fiscal_proofs.gaia_id", ondelete="RESTRICT")
    )
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class FiscalState(Base):
    __tablename__ = "fiscal_states"
    __table_args__ = (
        CheckConstraint("length(integrity_hash) = 64", name="ck_fiscal_state_hash"),
        CheckConstraint(
            "evidence_coverage IS NULL OR (evidence_coverage >= 0 AND evidence_coverage <= 1)",
            name="ck_fiscal_state_coverage_range",
        ),
        UniqueConstraint(
            "state_id", "effective_at", "integrity_hash", name="uq_fiscal_state_version"
        ),
        Index("ix_fiscal_states_jurisdiction_effective", "state_id", "effective_at"),
    )

    fiscal_state_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    state_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("states.state_id", ondelete="RESTRICT"), nullable=False
    )
    effective_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    fiscal_period: Mapped[str] = mapped_column(String(32), nullable=False)
    ledger_status: Mapped[EvidenceStatus] = mapped_column(
        _evidence_status("fiscal_state_ledger_status"), nullable=False
    )
    evidence_coverage: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    evidence_coverage_status: Mapped[str] = mapped_column(String(40), nullable=False)
    domains: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    evidence_integrity: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    events: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    sources: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    manifest_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("evidence_manifests.id", ondelete="RESTRICT"), nullable=False, unique=True
    )
    integrity_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    schema_version: Mapped[str] = mapped_column(String(32), nullable=False)
    methodology_version: Mapped[str] = mapped_column(String(32), nullable=False)
    previous_state_id: Mapped[str | None] = mapped_column(
        ForeignKey("fiscal_states.fiscal_state_id", ondelete="RESTRICT")
    )
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class EvidenceSource(Base):
    """A versioned registry view of one source document in one fiscal domain."""

    __tablename__ = "evidence_sources"
    __table_args__ = (
        CheckConstraint("length(document_sha256) = 64", name="ck_evidence_source_hash"),
        UniqueConstraint(
            "source_document_id",
            "state_id",
            "fiscal_domain",
            name="uq_evidence_source_document_jurisdiction_domain",
        ),
        Index("ix_evidence_sources_publisher", "publisher"),
        Index("ix_evidence_sources_jurisdiction_domain", "state_id", "fiscal_domain"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("source_documents.id", ondelete="RESTRICT"), nullable=False
    )
    state_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("states.state_id", ondelete="RESTRICT"), nullable=False
    )
    publisher: Mapped[str] = mapped_column(String(200), nullable=False)
    source_type: Mapped[str] = mapped_column(String(80), nullable=False)
    fiscal_domain: Mapped[str] = mapped_column(String(40), nullable=False)
    reporting_cadence: Mapped[str | None] = mapped_column(String(40))
    canonical_url: Mapped[str | None] = mapped_column(Text)
    document_url: Mapped[str | None] = mapped_column(Text)
    retrieved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    document_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    source_status: Mapped[str] = mapped_column(String(40), nullable=False)
    extraction_status: Mapped[str] = mapped_column(String(40), nullable=False)
    verification_status: Mapped[EvidenceStatus] = mapped_column(
        _evidence_status("evidence_source_verification_status"), nullable=False
    )
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revision_detected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    supersedes_source_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("evidence_sources.id", ondelete="RESTRICT")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ClaimRevision(Base):
    """Immutable lineage describing why one fiscal claim replaces another."""

    __tablename__ = "claim_revisions"
    __table_args__ = (
        CheckConstraint(
            "previous_claim_gaia_id <> revised_claim_gaia_id",
            name="ck_claim_revision_distinct_claims",
        ),
        UniqueConstraint("revised_claim_gaia_id", name="uq_claim_revision_revised_claim"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    previous_claim_gaia_id: Mapped[str] = mapped_column(
        ForeignKey("fiscal_claims.gaia_id", ondelete="RESTRICT"), nullable=False
    )
    revised_claim_gaia_id: Mapped[str] = mapped_column(
        ForeignKey("fiscal_claims.gaia_id", ondelete="RESTRICT"), nullable=False
    )
    reason: Mapped[str] = mapped_column(String(80), nullable=False)
    value_delta: Mapped[Decimal | None] = mapped_column(Numeric(30, 6))
    value_delta_text: Mapped[str | None] = mapped_column(String(160))
    value_change_percent: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))
    value_change_percent_text: Mapped[str | None] = mapped_column(String(80))
    material_change: Mapped[bool | None] = mapped_column(Boolean)
    source_revision: Mapped[bool] = mapped_column(Boolean, nullable=False)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    methodology_version: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class EvidenceConflict(Base):
    """An explicit unresolved disagreement between authoritative fiscal claims."""

    __tablename__ = "evidence_conflicts"
    __table_args__ = (
        Index(
            "ix_evidence_conflicts_jurisdiction_metric",
            "state_id",
            "object_type",
            "fiscal_period",
            "metric",
        ),
    )

    conflict_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    state_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("states.state_id", ondelete="RESTRICT"), nullable=False
    )
    object_type: Mapped[str] = mapped_column(String(40), nullable=False)
    fiscal_period: Mapped[str] = mapped_column(String(32), nullable=False)
    metric: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[EvidenceConflictStatus] = mapped_column(
        _conflict_status("evidence_conflict_status"), nullable=False
    )
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolution_notes: Mapped[str | None] = mapped_column(Text)
    methodology_version: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class EvidenceConflictClaim(Base):
    __tablename__ = "evidence_conflict_claims"
    __table_args__ = (UniqueConstraint("conflict_id", "claim_gaia_id", name="uq_conflict_claim"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conflict_id: Mapped[str] = mapped_column(
        ForeignKey("evidence_conflicts.conflict_id", ondelete="CASCADE"), nullable=False
    )
    claim_gaia_id: Mapped[str] = mapped_column(
        ForeignKey("fiscal_claims.gaia_id", ondelete="RESTRICT"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


def _immutable_published(_mapper: Mapper[Any], _connection: Any, target: Any) -> None:
    if target.published_at is not None:
        raise ValueError(f"Published {target.__class__.__name__} records are immutable.")


def _immutable_evidence(_mapper: Mapper[Any], _connection: Any, target: Any) -> None:
    raise ValueError(f"Published {target.__class__.__name__} records are immutable.")


for _model in (FiscalClaim, FiscalProof, FiscalState):
    event.listen(_model, "before_update", _immutable_published)
    event.listen(_model, "before_delete", _immutable_published)

for _model in (
    EvidenceManifest,
    EvidenceVerification,
    EvidenceSource,
    ClaimRevision,
    EvidenceConflictClaim,
):
    event.listen(_model, "before_update", _immutable_evidence)
    event.listen(_model, "before_delete", _immutable_evidence)
