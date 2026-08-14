from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

AnalystIntent = Literal[
    "latest_changes",
    "top_net",
    "lowest_net",
    "highest_deduction_burden",
    "most_volatile",
    "momentum",
    "compare",
    "igr_latest",
    "igr_state",
    "igr_top",
    "igr_lowest",
    "igr_compare",
    "ledger_metric",
    "unsupported",
]
AnalystStatus = Literal["answered", "insufficient_data", "unsupported"]
EvidenceDomain = Literal["faac", "igr", "ledger"]


class GaiaAnalystEvidence(BaseModel):
    state_name: str | None
    state_slug: str | None
    label: str
    value: str
    metric: str
    reference_path: str | None
    reference_label: str | None
    evidence_domain: EvidenceDomain = "faac"
    period_label: str | None = None
    source_organization: str | None = None
    source_sha256: str | None = None
    gaia_object_id: str | None = None
    evidence_status: str | None = None
    relevant_date: str | None = None


class GaiaAnalystResponse(BaseModel):
    question: str
    year: int
    intent: AnalystIntent
    status: AnalystStatus
    answer: str
    coverage_label: str
    evidence: list[GaiaAnalystEvidence]
    caveat: str
    suggested_questions: list[str]
