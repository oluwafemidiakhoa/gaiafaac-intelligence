from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


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


class FiscalDesignPersistRequest(BaseModel):
    """Inputs Gaia must recompute before persisting a scenario in a Decision Room."""

    state_slug: str = Field(min_length=2, max_length=100)
    year: int = Field(ge=2000, le=2100)
    faac_shock_pct: Decimal = Field(default=Decimal("-20"), ge=-100, le=100)
    igr_shock_pct: Decimal = Field(default=Decimal("0"), ge=-100, le=100)
    reserve_share_pct: Decimal = Field(default=Decimal("10"), ge=0, le=100)
    debt_change_pct: Decimal = Field(default=Decimal("0"), ge=-100, le=100)
    debt_service_change_pct: Decimal = Field(default=Decimal("0"), ge=-100, le=100)
    expenditure_change_pct: Decimal = Field(default=Decimal("0"), ge=-100, le=100)
    capital_spending_change_pct: Decimal = Field(default=Decimal("0"), ge=-100, le=100)
    inflation_assumption_pct: Decimal = Field(default=Decimal("0"), ge=-99, le=100)
