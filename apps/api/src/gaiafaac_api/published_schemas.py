from datetime import date, datetime

from pydantic import BaseModel


class PublishedSource(BaseModel):
    source_organization: str
    source_url: str | None
    original_filename: str
    sha256: str
    publication_date: date | None


class PublishedAllocation(BaseModel):
    state_name: str
    state_code: str
    state_slug: str
    geopolitical_zone: str
    gross_total: str | None
    total_deductions: str | None
    net_allocation: str | None
    reported_unit: str


class PublishedPeriod(BaseModel):
    id: str
    reporting_label: str
    revenue_month: date
    faac_meeting_date: date | None
    publication_date: date | None
    published_at: datetime | None


class PublishedOverviewResponse(BaseModel):
    period: PublishedPeriod
    source: PublishedSource
    covered_states: int
    expected_states: int
    total_gross: str | None
    total_deductions: str | None
    total_net: str | None
    allocations: list[PublishedAllocation]


class PublishedSourceItem(BaseModel):
    revenue_month: date
    reporting_label: str
    source_organization: str
    original_filename: str
    sha256: str
    source_url: str | None
    publication_date: date | None
    covered_states: int
    expected_states: int
