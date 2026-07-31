from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel


class PendingReviewItem(BaseModel):
    run_id: str
    reporting_label: str
    revenue_month: date
    source_organization: str
    status: str
    covered_states: int
    expected_states: int
    finding_count: int
    blocking_count: int
    created_at: datetime | None
