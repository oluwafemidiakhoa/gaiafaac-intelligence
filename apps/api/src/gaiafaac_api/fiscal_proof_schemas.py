from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel

ReconciliationStatus = Literal["reconciled", "not_applicable", "mismatch"]


class FiscalProofFinancials(BaseModel):
    gross_total: str | None
    total_deductions: str | None
    net_allocation: str | None
    reported_unit: str
    reconciliation_status: ReconciliationStatus
    reconciliation_delta: str | None


class FiscalProofSource(BaseModel):
    source_organization: str
    source_url: str | None
    original_filename: str
    sha256: str
    publication_date: date | None
    document_version: str


class FiscalProofVerification(BaseModel):
    allocation_status: str
    period_status: str
    source_status: str
    reviewed_at: datetime | None
    published_at: datetime | None
    human_verified: bool


class FiscalProofResponse(BaseModel):
    proof_version: Literal["1"] = "1"
    proof_id: str
    proof_digest_sha256: str
    claim: str
    state_name: str
    state_slug: str
    state_code: str
    geopolitical_zone: str
    revenue_month: date
    reporting_label: str
    financials: FiscalProofFinancials
    source: FiscalProofSource
    verification: FiscalProofVerification
    disclaimer: str
