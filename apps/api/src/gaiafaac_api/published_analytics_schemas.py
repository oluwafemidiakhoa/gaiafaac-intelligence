from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class TrendPoint(BaseModel):
    revenue_month: date
    reporting_label: str
    total_net: str
    covered_states: int


class RankedState(BaseModel):
    state_name: str
    state_slug: str
    state_code: str
    geopolitical_zone: str
    net_allocation: str


class MonthMover(BaseModel):
    state_name: str
    state_slug: str
    previous_net: str
    current_net: str
    change: str
    pct_change: float


class PublishedAnalytics(BaseModel):
    months_published: int
    national_trend: list[TrendPoint]
    latest_period_label: str | None
    top_states: list[RankedState]
    biggest_movers: list[MonthMover]
    note: str
