from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


class WatchlistCreateRequest(BaseModel):
    state_code: str = Field(min_length=2, max_length=2)


class WatchlistItem(BaseModel):
    id: uuid.UUID
    state_name: str
    state_code: str
    state_slug: str
    geopolitical_zone: str
    created_at: datetime


class WatchlistAlert(BaseModel):
    event_key: str
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


class WatchlistAlertsResponse(BaseModel):
    year: int
    latest_revenue_month: date | None
    previous_revenue_month: date | None
    watched_states: int
    event_count: int
    events: list[WatchlistAlert]
    note: str
