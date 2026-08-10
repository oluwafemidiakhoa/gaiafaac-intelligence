from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class DecisionPacketMonth(BaseModel):
    revenue_month: date
    reporting_label: str
    gross_total: str | None
    total_deductions: str | None
    net_allocation: str | None
    reconciliation_status: str
    proof_id: str
    proof_path: str
    source_organization: str
    source_sha256: str
    human_verified: bool


class DecisionPacketWatchEvent(BaseModel):
    kind: str
    severity: str
    headline: str
    detail: str
    proof_path: str


class DecisionPacketResponse(BaseModel):
    packet_version: str = "1"
    state_name: str
    state_slug: str
    state_code: str
    geopolitical_zone: str
    year: int
    coverage_label: str
    months_published: int
    annual_gross: str | None
    annual_deductions: str | None
    annual_net: str | None
    deduction_burden_pct: float | None
    net_retention_pct: float | None
    momentum: str
    momentum_pct: float | None
    volatility: str
    volatility_cv_pct: float | None
    evidence_status: str
    watch_events: list[DecisionPacketWatchEvent]
    months: list[DecisionPacketMonth]
    disclaimer: str
