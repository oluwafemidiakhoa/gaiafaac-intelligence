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
WatchContractReviewStatus = Literal["open", "acknowledged", "resolved"]
WatchContractDeliveryChannel = Literal["in_app", "email", "webhook"]
WatchContractDeliveryStatus = Literal[
    "pending",
    "delivered",
    "retrying",
    "dead_letter",
    "deferred",
    "failed",
]


class FiscalWatchContractCreateRequest(BaseModel):
    room_id: uuid.UUID
    baseline_receipt_id: uuid.UUID | None = None
    name: str = Field(min_length=3, max_length=200)
    state_codes: list[str] = Field(default_factory=list, max_length=37)
    event_types: list[str] = Field(default_factory=list, max_length=30)
    minimum_severity: WatchContractSeverity = "watch"
    escalation_after_minutes: int = Field(default=1440, ge=15, le=10080)

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
    escalation_after_minutes: int
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


class FiscalWatchContractDeliveryAttemptResponse(BaseModel):
    id: uuid.UUID
    delivery_id: uuid.UUID
    attempt_number: int
    attempted_at: datetime
    response_status: int | None
    response_body_excerpt: str | None
    error: str | None


class FiscalWatchContractDeliveryResponse(BaseModel):
    id: uuid.UUID
    review_id: uuid.UUID
    match_id: uuid.UUID
    contract_id: uuid.UUID
    recipient_user_id: uuid.UUID | None
    endpoint_id: uuid.UUID | None
    channel: WatchContractDeliveryChannel
    destination_key: str
    recipient_address: str | None
    status: WatchContractDeliveryStatus
    attempt_count: int
    next_attempt_at: datetime | None
    last_attempt_at: datetime | None
    response_status: int | None
    response_body_excerpt: str | None
    last_error: str | None
    payload_sha256: str | None
    details: dict
    delivered_at: datetime | None
    created_at: datetime
    updated_at: datetime
    attempts: list[FiscalWatchContractDeliveryAttemptResponse] = Field(default_factory=list)


class FiscalWatchContractReviewResponse(BaseModel):
    id: uuid.UUID
    match_id: uuid.UUID
    contract_id: uuid.UUID
    room_id: uuid.UUID
    assigned_user_id: uuid.UUID | None
    status: WatchContractReviewStatus
    due_at: datetime
    escalated_at: datetime | None
    acknowledged_at: datetime | None
    acknowledged_by_user_id: uuid.UUID | None
    resolved_at: datetime | None
    resolved_by_user_id: uuid.UUID | None
    resolution_note: str | None
    created_at: datetime
    updated_at: datetime
    contract_name: str
    state_code: str
    state_name: str
    event_type: str
    severity: str
    headline: str
    detail: str
    occurred_at: datetime
    deliveries: list[FiscalWatchContractDeliveryResponse] = Field(default_factory=list)


class FiscalWatchContractReviewAssignRequest(BaseModel):
    assigned_user_id: uuid.UUID | None = None


class FiscalWatchContractReviewResolveRequest(BaseModel):
    resolution_note: str = Field(min_length=3, max_length=5000)


class FiscalWatchContractEscalationResponse(BaseModel):
    escalated_count: int
    reviews: list[FiscalWatchContractReviewResponse]


class FiscalWatchDeliveryRunResponse(BaseModel):
    reviews_checked: int
    deliveries_created: int
    delivered: int
    retrying: int
    dead_letter: int
    deferred: int
    failed: int


class FiscalWatchContractEvaluationResponse(BaseModel):
    contract: FiscalWatchContractResponse
    new_match_count: int
    total_match_count: int
    matches: list[FiscalWatchContractMatchResponse]
    operational_review_count: int = 0
    note: str
