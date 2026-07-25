from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

from gaiafaac_api.database.enums import SourceStatus, VerificationStatus

DEMO_DATA_LABEL = "DEMO DATA - NOT REAL FAAC DATA"


class DemoPeriod(BaseModel):
    id: str
    reporting_label: str
    revenue_month: date
    faac_meeting_date: date | None
    publication_date: date | None
    verification_status: VerificationStatus
    is_published: Literal[False]


class DemoAllocation(BaseModel):
    state_name: str
    state_code: str
    state_slug: str
    geopolitical_zone: str
    gross_total: str | None
    total_deductions: str | None
    net_allocation: str | None
    reported_unit: str
    verification_status: VerificationStatus
    source_document_id: str
    is_published: Literal[False]


class DemoComponent(BaseModel):
    component_type: str
    component_name: str
    gross_amount: str | None
    deduction_amount: str | None
    net_amount: str | None
    reported_unit: str


class DemoOverviewResponse(BaseModel):
    data_label: Literal["DEMO DATA - NOT REAL FAAC DATA"] = DEMO_DATA_LABEL
    scope_note: str
    period: DemoPeriod
    covered_states: int
    expected_states: int
    sample_gross_total: str | None
    sample_deductions_total: str | None
    sample_net_total: str | None
    allocations: list[DemoAllocation]


class DemoStateSummary(BaseModel):
    name: str
    code: str
    slug: str
    geopolitical_zone: str
    capital: str
    has_demo_allocation: bool
    demo_net_allocation: str | None
    verification_status: VerificationStatus | None


class DemoStatesResponse(BaseModel):
    data_label: Literal["DEMO DATA - NOT REAL FAAC DATA"] = DEMO_DATA_LABEL
    period: DemoPeriod
    states: list[DemoStateSummary]


class DemoStateDetailResponse(BaseModel):
    data_label: Literal["DEMO DATA - NOT REAL FAAC DATA"] = DEMO_DATA_LABEL
    period: DemoPeriod
    state: DemoStateSummary
    allocation: DemoAllocation | None
    components: list[DemoComponent] = Field(default_factory=list)
    unavailable_note: str | None = None


class DemoComparisonResponse(BaseModel):
    data_label: Literal["DEMO DATA - NOT REAL FAAC DATA"] = DEMO_DATA_LABEL
    scope_note: str
    period: DemoPeriod
    states: list[DemoStateDetailResponse]


class DemoSource(BaseModel):
    id: str
    source_organization: str
    source_url: str | None
    original_filename: str
    sha256: str
    mime_type: str
    publication_date: date | None
    downloaded_at: datetime | None
    document_version: str
    source_status: SourceStatus
    is_demo: Literal[True]


class DemoSourcesResponse(BaseModel):
    data_label: Literal["DEMO DATA - NOT REAL FAAC DATA"] = DEMO_DATA_LABEL
    sources: list[DemoSource]
