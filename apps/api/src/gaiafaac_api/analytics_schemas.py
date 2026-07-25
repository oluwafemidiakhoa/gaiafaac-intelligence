from datetime import date
from typing import Literal

from pydantic import BaseModel

DEMO_DATA_LABEL = "DEMO DATA - NOT REAL FAAC DATA"
_LABEL = Literal["DEMO DATA - NOT REAL FAAC DATA"]


class RankingRow(BaseModel):
    state_name: str
    state_code: str
    state_slug: str
    geopolitical_zone: str
    net_allocation: str | None
    rank: int
    rank_change: int | None


class RankingsResponse(BaseModel):
    data_label: _LABEL = DEMO_DATA_LABEL
    scope_note: str
    reporting_label: str
    revenue_month: date
    rankings: list[RankingRow]


class VolatilityRow(BaseModel):
    state_name: str
    state_code: str
    state_slug: str
    coefficient_of_variation: str


class VolatilityResponse(BaseModel):
    data_label: _LABEL = DEMO_DATA_LABEL
    scope_note: str
    window_periods: int
    rows: list[VolatilityRow]


class DependencyRow(BaseModel):
    state_name: str
    state_code: str
    state_slug: str
    shares: dict[str, str]
    concentration_hhi: str | None


class DependencyResponse(BaseModel):
    data_label: _LABEL = DEMO_DATA_LABEL
    scope_note: str
    reporting_label: str
    rows: list[DependencyRow]


class ForecastRow(BaseModel):
    state_name: str
    state_code: str
    state_slug: str
    method: str
    target_period: date
    point_estimate: str
    lower_bound: str
    upper_bound: str
    training_start: date
    training_end: date
    is_estimate: Literal[True] = True


class ForecastsResponse(BaseModel):
    data_label: _LABEL = DEMO_DATA_LABEL
    scope_note: str
    forecasts: list[ForecastRow]
