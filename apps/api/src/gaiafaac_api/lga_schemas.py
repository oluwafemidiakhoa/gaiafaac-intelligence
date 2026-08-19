from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel


class PublishedLgaSource(BaseModel):
    organization: str
    source_url: str | None
    original_filename: str
    sha256: str
    publication_date: date | None
    document_version: str


class PublishedLgaAllocation(BaseModel):
    reporting_period_id: uuid.UUID
    reporting_label: str
    revenue_month: date
    disbursement_month: date
    allocation_period_month: date | None
    published_at: datetime | None
    state_name: str
    state_code: str
    state_slug: str
    local_government_name: str
    local_government_slug: str
    net_statutory_allocation: str | None
    deduction_amount: str | None
    ecology_share: str | None
    ecology_transfer: str | None
    net_ecology_share: str | None
    vat_amount: str | None
    total_net_allocation: str
    reported_unit: str
    source_page: int | None
    source_table: str
    verification_status: str
    source: PublishedLgaSource


class PublishedLgaStateResponse(BaseModel):
    state_name: str
    state_code: str
    state_slug: str
    local_government_count: int
    local_governments: list[PublishedLgaAllocation]
    note: str


class PublishedLgaDetailResponse(BaseModel):
    state_name: str
    state_code: str
    state_slug: str
    local_government_name: str
    local_government_slug: str
    record_count: int
    allocations: list[PublishedLgaAllocation]
    note: str
