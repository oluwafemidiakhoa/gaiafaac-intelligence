from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class FiscalDesignEvidence(BaseModel):
    evidence_domain: Literal["faac", "igr"]
    label: str
    value: str
    source_organization: str
    source_sha256: str
    reference_path: str


class FiscalDesignMetric(BaseModel):
    label: str
    value: str
    unit: str


class FiscalDesignCandidate(BaseModel):
    key: str
    title: str
    purpose: str
    status: Literal["available", "insufficient_data"]
    metrics: list[FiscalDesignMetric]
    note: str


class FiscalDesignResponse(BaseModel):
    design_version: str = "0.1"
    state_name: str
    state_slug: str
    state_code: str
    year: int
    latest_comparable_year: int | None
    objective: str
    coverage_label: str
    faac_months_published: int
    faac_complete_year: bool
    annual_igr_available: bool
    faac_shock_pct: str
    igr_shock_pct: str
    reserve_share_pct: str
    debt_change_pct: str = "0.00"
    debt_service_change_pct: str = "0.00"
    expenditure_change_pct: str = "0.00"
    capital_spending_change_pct: str = "0.00"
    inflation_assumption_pct: str = "0.00"
    scenario_gaia_id: str
    unsupported_dimensions: list[str]
    assumptions: list[str]
    evidence: list[FiscalDesignEvidence]
    candidates: list[FiscalDesignCandidate]
    disclaimer: str
