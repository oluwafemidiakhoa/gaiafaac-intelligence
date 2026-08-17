from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel

EvidenceClass = Literal["observed", "derived", "conflicted", "missing"]
ReconciliationStatus = Literal["reconciled", "conflicted", "incomplete", "unavailable"]
NationalSourceType = Literal[
    "canonical_national_evidence",
    "official_national_summary_evidence",
    "official_government_press_release",
]
NationalSourceAuthority = Literal["canonical", "official_secondary", "contextual"]
CanonicalSourceStatus = Literal["available", "missing", "superseded", "conflicted"]


class NationalObservedValue(BaseModel):
    value: str | None
    evidence_class: EvidenceClass


class NationalSource(BaseModel):
    source_organization: str
    source_url: str | None
    original_filename: str
    sha256: str
    publication_date: date | None
    document_version: str
    source_type: NationalSourceType
    source_authority: NationalSourceAuthority


class NationalReconciliation(BaseModel):
    status: ReconciliationStatus
    observed_total: str | None
    derived_total: str | None
    variance: str | None
    tolerance: str | None
    evidence_class: EvidenceClass
    basis: str
    note: str


class PublishedNationalDistribution(BaseModel):
    reporting_period_id: str
    reporting_label: str
    revenue_month: date
    disbursement_month: date
    allocation_period_month: date | None
    published_at: datetime | None
    verification_status: str
    reported_unit: str
    derivation_treatment: str
    states_scope: str
    canonical_source_status: CanonicalSourceStatus
    covered_jurisdictions: int
    expected_jurisdictions: int
    source: NationalSource
    net_distributable_amount: NationalObservedValue
    federal_amount: NationalObservedValue
    states_amount: NationalObservedValue
    local_governments_amount: NationalObservedValue
    derivation_amount: NationalObservedValue
    vat_amount: NationalObservedValue
    statutory_amount: NationalObservedValue
    component_reconciliation: NationalReconciliation
    jurisdiction_reconciliation: NationalReconciliation
