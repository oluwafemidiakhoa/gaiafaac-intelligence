from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class WebhookCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    url: str = Field(min_length=12, max_length=2000)
    event_types: list[str] = Field(min_length=1, max_length=20)
    jurisdiction_codes: list[str] = Field(default_factory=list, max_length=37)


class WebhookEndpointItem(BaseModel):
    id: uuid.UUID
    name: str
    url: str
    enabled: bool
    event_types: list[str]
    jurisdiction_codes: list[str]
    secret_version: int
    created_at: datetime
    disabled_at: datetime | None


class WebhookEndpointCreated(WebhookEndpointItem):
    signing_secret: str
    signing_note: str


class WebhookSecretRotated(BaseModel):
    endpoint_id: uuid.UUID
    secret_version: int
    signing_secret: str
    signing_note: str


class WebhookDeliveryItem(BaseModel):
    id: uuid.UUID
    endpoint_id: uuid.UUID
    fiscal_event_id: str
    status: Literal["pending", "retrying", "delivered", "dead_letter", "deferred"]
    attempt_count: int
    next_attempt_at: datetime | None
    last_attempt_at: datetime | None
    delivered_at: datetime | None
    response_status: int | None
    last_error: str | None
    payload_sha256: str
    created_at: datetime


class WebhookAttemptItem(BaseModel):
    id: uuid.UUID
    delivery_id: uuid.UUID
    attempt_number: int
    attempted_at: datetime
    response_status: int | None
    response_body_excerpt: str | None
    error: str | None
