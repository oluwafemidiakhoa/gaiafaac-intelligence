from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from gaiafaac_api.database.enums import EvidenceStatus
from gaiafaac_api.fiscal_ledger_schemas import JurisdictionIdentity, LedgerMeta


class TemporalFiscalClaim(BaseModel):
    gaia_id: str
    object_type: str
    fiscal_period: str
    metric: str
    value: str | None
    unit: str
    currency: str | None
    evidence_status: EvidenceStatus
    source_sha256: str
    source_publisher: str
    source_url: str | None
    effective_at: datetime
    published_at: datetime
    supersedes_gaia_id: str | None


class TemporalFiscalSnapshotData(BaseModel):
    jurisdiction: JurisdictionIdentity
    effective_as_of: datetime
    known_as_of: datetime
    domains: dict[str, list[TemporalFiscalClaim]]
    claim_count: int


class TemporalFiscalSnapshotEnvelope(BaseModel):
    data: TemporalFiscalSnapshotData
    evidence: dict[str, object]
    meta: LedgerMeta
