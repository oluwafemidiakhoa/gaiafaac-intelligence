from __future__ import annotations

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


RevisionResolution = Literal[
    "no_material_fiscal_change",
    "metadata_only_change",
    "requires_data_republication",
    "investigation_required",
]


class OagfRevisionCaseItem(BaseModel):
    id: str
    status: str
    detected_at: datetime
    title: str
    reporting_label: str | None
    revenue_month: date | None
    current_version: int
    previous_version: int
    current_sha256: str
    previous_sha256: str
    current_source_url: str
    previous_source_url: str
    resolution_code: str | None
    review_note: str | None
    reviewed_by: str | None
    reviewed_at: datetime | None


class ResolveOagfRevisionRequest(BaseModel):
    reviewer_id: UUID
    resolution_code: RevisionResolution
    attestation: bool
    note: str = Field(min_length=3, max_length=4000)


class ResolveOagfRevisionResponse(BaseModel):
    id: str
    status: str
    resolution_code: str
