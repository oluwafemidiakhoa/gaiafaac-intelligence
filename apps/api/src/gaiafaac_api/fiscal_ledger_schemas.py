from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from gaiafaac_api.database.enums import (
    EvidenceConflictStatus,
    EvidenceStatus,
    FiscalEventSeverity,
)


class LedgerMeta(BaseModel):
    schema_version: str = "1.0.0"
    methodology_version: str


class JurisdictionIdentity(BaseModel):
    country: Literal["NG"] = "NG"
    code: str
    name: str


class EvidenceManifestResponse(BaseModel):
    manifest_version: str
    schema_version: str
    canonicalization_version: str
    hash_algorithm: Literal["sha256"] = "sha256"
    payload_sha256: str = Field(pattern=r"^[a-fA-F0-9]{64}$")
    payload: dict[str, Any]


class ProofSource(BaseModel):
    publisher: str
    document_url: str | None
    document_sha256: str
    publication_date: str | None
    page: int | None
    table: str | None


class ProofVerification(BaseModel):
    status: EvidenceStatus
    source_verified: bool
    reconciled: bool | None
    human_reviewed: bool
    published: bool
    verified_at: datetime | None
    note: str


class FiscalProofData(BaseModel):
    gaia_id: str
    object_type: str
    jurisdiction: JurisdictionIdentity
    fiscal_period: str
    metric: str
    value: str | None
    unit: str
    currency: str | None
    effective_at: datetime
    methodology_version: str
    supersedes_gaia_id: str | None
    superseded_by_gaia_id: str | None
    source: ProofSource
    verification: ProofVerification
    published_at: datetime


class FiscalProofEvidence(BaseModel):
    manifest: EvidenceManifestResponse
    disclaimer: str
    revisions: list[EvidenceRevisionResponse] = Field(default_factory=list)
    conflicts: list[EvidenceConflictResponse] = Field(default_factory=list)
    history: list[EvidenceHistoryEntry] = Field(default_factory=list)


class FiscalProofEnvelope(BaseModel):
    data: FiscalProofData
    evidence: FiscalProofEvidence
    meta: LedgerMeta


class FiscalStateData(BaseModel):
    fiscal_state_id: str
    jurisdiction: JurisdictionIdentity
    effective_at: datetime
    fiscal_period: str
    ledger_status: EvidenceStatus
    evidence_coverage: str | None
    evidence_coverage_status: Literal["calculated", "insufficient_evidence"]
    domains: dict[str, Any]
    evidence_integrity: dict[str, Any]
    events: list[dict[str, Any]]
    sources: list[dict[str, Any]]
    previous_state_id: str | None
    published_at: datetime


class FiscalStateEvidence(BaseModel):
    manifest: EvidenceManifestResponse
    conflicts: list[EvidenceConflictResponse] = Field(default_factory=list)


class FiscalStateEnvelope(BaseModel):
    data: FiscalStateData
    evidence: FiscalStateEvidence
    meta: LedgerMeta


class FiscalArtifactVerificationResponse(BaseModel):
    status: Literal["verified", "mismatch"]
    artifact_integrity: Literal["verified", "failed"]
    embedded_sha256: str
    computed_sha256: str
    manifest_version: str
    source_provenance_recorded: bool | None
    reconciliation_recorded: bool | None
    human_review_recorded: bool | None
    meaning: str


class EvidenceRevisionResponse(BaseModel):
    previous_claim_gaia_id: str
    revised_claim_gaia_id: str
    reason: str
    value_delta: str | None
    value_change_percent: str | None
    material_change: bool | None
    source_revision: bool
    detected_at: datetime
    methodology_version: str


class EvidenceConflictParticipant(BaseModel):
    claim_gaia_id: str
    publisher: str
    value: str | None
    unit: str
    currency: str | None
    source_sha256: str


class EvidenceConflictResponse(BaseModel):
    conflict_id: str
    status: EvidenceConflictStatus
    object_type: str
    fiscal_period: str
    metric: str
    explanation: str
    detected_at: datetime
    participants: list[EvidenceConflictParticipant]


class EvidenceSourceResponse(BaseModel):
    source_id: str
    publisher: str
    source_type: str
    jurisdiction: str
    fiscal_domain: str
    reporting_cadence: str | None
    canonical_url: str | None
    document_url: str | None
    retrieved_at: datetime | None
    document_sha256: str
    source_status: str
    extraction_status: str
    verification_status: EvidenceStatus
    last_checked_at: datetime | None
    revision_detected: bool
    supersedes_source_id: str | None


class EvidenceSourceRegistryEnvelope(BaseModel):
    data: list[EvidenceSourceResponse]
    evidence: dict[str, Any]
    meta: LedgerMeta


class EvidenceHistoryEntry(BaseModel):
    entry_type: Literal[
        "source_detected",
        "human_verified",
        "published",
        "source_revised",
        "claim_superseded",
    ]
    occurred_at: datetime
    label: str
    evidence_ids: list[str] = Field(default_factory=list)


class FiscalEventData(BaseModel):
    event_id: str
    jurisdiction: JurisdictionIdentity
    event_type: str
    severity: FiscalEventSeverity
    effective_at: datetime
    detected_at: datetime
    evidence_status: EvidenceStatus
    evidence_ids: list[str]
    calculation: dict[str, Any]
    explanation: str
    fiscal_state_id: str | None
    methodology_version: str


class FiscalEventStreamEvidence(BaseModel):
    record_count: int
    meaning: str


class FiscalEventStreamEnvelope(BaseModel):
    data: list[FiscalEventData]
    evidence: FiscalEventStreamEvidence
    meta: LedgerMeta


class FiscalCertificateData(BaseModel):
    gaia_id: str
    jurisdiction: JurisdictionIdentity
    fiscal_period: str
    fiscal_state_id: str
    ledger_status: EvidenceStatus
    evidence_coverage: str | None
    evidence_integrity: dict[str, Any]
    verified_domains: list[str]
    partial_domains: list[str]
    unavailable_domains: list[str]
    proof_gaia_ids: list[str]
    issued_at: datetime


class FiscalCertificateEvidence(BaseModel):
    manifest: EvidenceManifestResponse
    disclaimer: str


class FiscalCertificateEnvelope(BaseModel):
    data: FiscalCertificateData
    evidence: FiscalCertificateEvidence
    meta: LedgerMeta


FiscalProofEvidence.model_rebuild()
FiscalStateEvidence.model_rebuild()
