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
from gaiafaac_api.database.enums import EvidenceStatus


def _evidence_status(name: str) -> Enum:
    return Enum(
        EvidenceStatus,
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


def _immutable_published(_mapper: Mapper[Any], _connection: Any, target: Any) -> None:
    if target.published_at is not None:
        raise ValueError(f"Published {target.__class__.__name__} records are immutable.")


def _immutable_evidence(_mapper: Mapper[Any], _connection: Any, target: Any) -> None:
    raise ValueError(f"Published {target.__class__.__name__} records are immutable.")


for _model in (FiscalClaim, FiscalProof, FiscalState):
    event.listen(_model, "before_update", _immutable_published)
    event.listen(_model, "before_delete", _immutable_published)

for _model in (EvidenceManifest, EvidenceVerification):
    event.listen(_model, "before_update", _immutable_evidence)
    event.listen(_model, "before_delete", _immutable_evidence)
