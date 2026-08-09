from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

MomentumLabel = Literal["Improving", "Stable", "Weakening", "Insufficient data"]
VolatilityLabel = Literal["Low", "Moderate", "High", "Insufficient data"]
EvidenceLabel = Literal["Verified", "Partial", "Review required"]


class FiscalPulseState(BaseModel):
    state_name: str
    state_slug: str
    state_code: str
    geopolitical_zone: str
    months_published: int
    months_with_net: int
    months_with_complete_financials: int
    annual_gross: str | None
    annual_deductions: str | None
    annual_net: str | None
    deduction_burden_pct: float | None
    net_retention_pct: float | None
    momentum: MomentumLabel
    momentum_pct: float | None
    volatility: VolatilityLabel
    volatility_cv_pct: float | None
    evidence_status: EvidenceLabel


class FiscalPulseResponse(BaseModel):
    year: int
    months_published: int
    latest_period_label: str | None
    total_net: str | None
    states: list[FiscalPulseState]
    note: str
