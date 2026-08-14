from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from gaiafaac_api.database.enums import EvidenceStatus
from gaiafaac_api.fiscal_ledger_schemas import JurisdictionIdentity, LedgerMeta


class DerivedFiscalMetric(BaseModel):
    key: str
    status: Literal["calculated", "insufficient_evidence"]
    value: str | None
    unit: str
    label: str
    fiscal_period: str | None
    evidence_ids: list[str]
    explanation: str


class FiscalIndexReadiness(BaseModel):
    index_name: Literal["Gaia Fiscal Resilience"] = "Gaia Fiscal Resilience"
    status: Literal["not_calculated"] = "not_calculated"
    score: None = None
    reason: str
    required_coverage: str
    observed_coverage: str | None
    missing_components: list[str]


class JurisdictionIntelligenceData(BaseModel):
    fiscal_state_id: str
    jurisdiction: JurisdictionIdentity
    fiscal_period: str
    effective_at: datetime
    ledger_status: EvidenceStatus
    metrics: list[DerivedFiscalMetric]
    resilience: FiscalIndexReadiness


class IntelligenceEvidence(BaseModel):
    evidence_coverage: str | None
    evidence_integrity: dict[str, object]
    source_count: int
    meaning: str


class JurisdictionIntelligenceEnvelope(BaseModel):
    data: JurisdictionIntelligenceData
    evidence: IntelligenceEvidence
    meta: LedgerMeta


class FiscalComparisonData(BaseModel):
    jurisdictions: list[JurisdictionIntelligenceData] = Field(max_length=6)
    comparable_fiscal_period: str | None


class FiscalComparisonEnvelope(BaseModel):
    data: FiscalComparisonData
    evidence: dict[str, object]
    meta: LedgerMeta
