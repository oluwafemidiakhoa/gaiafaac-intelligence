from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class DecisionReviewTrigger(BaseModel):
    match_id: uuid.UUID
    contract_id: uuid.UUID
    contract_name: str
    state_code: str
    state_name: str
    event_type: str
    severity: str
    headline: str
    detail: str
    occurred_at: datetime
    matched_at: datetime


class DecisionReviewState(BaseModel):
    room_id: uuid.UUID
    review_required: bool
    review_trigger_match_id: uuid.UUID | None
    review_required_at: datetime | None
    last_reviewed_at: datetime | None
    reviewed_by_user_id: uuid.UUID | None
    latest_receipt_id: uuid.UUID | None
    latest_receipt_sha256: str | None = Field(default=None, min_length=64, max_length=64)
    latest_receipt_created_at: datetime | None
    predecessor_receipt_id: uuid.UUID | None
    triggering_match_id: uuid.UUID | None
    trigger: DecisionReviewTrigger | None = None
