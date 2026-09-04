from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

WatchContractStatus = Literal["active", "paused", "archived"]
WatchContractSeverity = Literal[
    "informational",
    "watch",
    "elevated",
    "notable",
    "material",
    "critical",
]


class FiscalWatchContractCreateRequest(BaseModel):
    room_id: uuid.UUID
    baseline_receipt_id: uuid.UUID | None = None
    name: str = Field(min_length=3, max_length=200)
    state_codes: list[str] = Field(default_factory=list, max_length=37)
    event_types: list[str] = Field(default_factory=list, max_length=30)
    minimum_severity: WatchContractSeverity = "watch"

    @field_validator("state_codes")
    @classmethod
    def normalize_state_codes(cls, value: list[str]) -> list[str]:
        normalized = sorted({item.strip().upper() for item in value if item.strip()})
        for code in normalized:
            if len(code) != 2 or not code.isalpha():
                raise ValueError("State codes must use two-letter jurisdiction codes.")
        return normalized

    @field_validator("event_types")
    @classmethod
    def normalize_event_types(cls, value: list[str]) -> list[str]:
        return sorted({item.strip() for item in value if item.strip()})


class FiscalWatchContractStatusUpdate(BaseModel):
    status: WatchContractStatus


class FiscalWatchContractResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    room_id: uuid.UUID
    baseline_receipt_id: uuid.UUID | None
    created_by_user_id: uuid.UUID | None
    name: str
    state_codes: list[str]
    event_types: list[str]
    minimum_severity: WatchContractSeverity
    status: WatchContractStatus
    last_evaluated_at: datetime | None
    created_at: datetime
    updated_at: datetime
    match_count: int = 0


class FiscalWatchContractMatchResponse(BaseModel):
    id: uuid.UUID
    contract_id: uuid.UUID
    room_id: uuid.UUID
    organization_alert_id: uuid.UUID
    state_code: str
    state_name: str
    event_type: str
    severity: str
    headline: str
    detail: str
    occurred_at: datetime
    matched_at: datetime


class FiscalWatchContractEvaluationResponse(BaseModel):
    contract: FiscalWatchContractResponse
    new_match_count: int
    total_match_count: int
    matches: list[FiscalWatchContractMatchResponse]
    note: str
