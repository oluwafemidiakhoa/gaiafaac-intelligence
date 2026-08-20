from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class WatchlistCreateRequest(BaseModel):
    state_code: str = Field(min_length=2, max_length=2)


class WatchlistItem(BaseModel):
    id: uuid.UUID
    state_name: str
    state_code: str
    state_slug: str
    geopolitical_zone: str
    created_at: datetime


class WatchlistAlert(BaseModel):
    id: uuid.UUID
    event_key: str
    source_kind: Literal["fiscal_watch", "fiscal_event", "publication"]
    event_type: str
    severity: str
    state_name: str
    state_slug: str
    state_code: str
    occurred_at: datetime
    headline: str
    detail: str
    link_path: str
    evidence_ids: list[str] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)
    read_at: datetime | None
    is_read: bool


class WatchlistAlertsResponse(BaseModel):
    year: int
    watchlist_count: int
    alert_count: int
    unread_count: int
    alerts: list[WatchlistAlert]
    note: str


class NotificationPreferenceUpdate(BaseModel):
    email_enabled: bool
    include_fiscal_watch: bool = True
    include_fiscal_events: bool = True


class NotificationPreferenceResponse(BaseModel):
    email_enabled: bool
    include_fiscal_watch: bool
    include_fiscal_events: bool
    email_enabled_at: datetime | None
    delivery_available: bool
    delivery_note: str
