from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from gaiafaac_api.database.enums import EvidenceStatus
from gaiafaac_api.fiscal_ledger_schemas import JurisdictionIdentity, LedgerMeta


class FiscalClaimSource(BaseModel):
    publisher: str
    document_url: str | None
    document_sha256: str
    page: int | None
    table: str | None


class FiscalClaimSummary(BaseModel):
    gaia_id: str
    object_type: str
    jurisdiction: JurisdictionIdentity
    fiscal_period: str
    metric: str
    value: str | None
    unit: str
    currency: str | None
    evidence_status: EvidenceStatus
    effective_at: datetime
    published_at: datetime
    supersedes_gaia_id: str | None
    superseded_by_gaia_id: str | None
    source: FiscalClaimSource


class FiscalClaimEnvelope(BaseModel):
    data: list[FiscalClaimSummary]
    evidence: dict[str, Any]
    meta: LedgerMeta


class FiscalClaimQuery(BaseModel):
    jurisdiction: str | None = None
    fiscal_domain: str | None = None
    fiscal_period: str | None = None
    metric: str | None = None
    include_superseded: bool = False
    limit: int = Field(default=100, ge=1, le=200)
