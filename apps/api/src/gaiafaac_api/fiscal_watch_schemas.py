from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel


class FiscalWatchEvent(BaseModel):
    kind: Literal["negative_net", "large_monthly_move", "high_deduction_burden"]
    severity: Literal["watch", "elevated"]
    state_name: str
    state_slug: str
    state_code: str
    revenue_month: date
    headline: str
    detail: str
    current_net: str | None
    previous_net: str | None
    change_pct: float | None
    deduction_burden_pct: float | None
    proof_path: str


class FiscalWatchResponse(BaseModel):
    year: int
    latest_revenue_month: date | None
    previous_revenue_month: date | None
    event_count: int
    events: list[FiscalWatchEvent]
    note: str
