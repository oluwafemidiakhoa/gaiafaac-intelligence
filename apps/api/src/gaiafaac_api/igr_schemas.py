from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel


class PublishedIgrSource(BaseModel):
    organization: str
    source_url: str | None
    sha256: str
    publication_date: date | None


class PublishedIgrRecord(BaseModel):
    state_name: str
    state_slug: str
    state_code: str
    fiscal_year: int
    period_type: Literal["annual", "quarterly"]
    quarter: int | None
    period_start: date
    period_end: date
    igr_amount: str
    reported_unit: str
    source_page: int | None
    source_table: str | None
    verification_status: str
    source: PublishedIgrSource


class PublishedIgrResponse(BaseModel):
    year: int
    state_slug: str | None
    record_count: int
    records: list[PublishedIgrRecord]
    note: str
