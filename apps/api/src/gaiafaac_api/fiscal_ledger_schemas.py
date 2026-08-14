from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from gaiafaac_api.database.enums import EvidenceStatus


class LedgerMeta(BaseModel):
    schema_version: Literal["1.0.0"] = "1.0.0"
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
