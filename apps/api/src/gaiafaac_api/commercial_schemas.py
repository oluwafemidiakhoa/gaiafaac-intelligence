from __future__ import annotations

import re
import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

PilotPlan = Literal["analyst", "team", "api"]
PilotLeadStatus = Literal[
    "new",
    "contacted",
    "qualified",
    "pilot",
    "proposal",
    "won",
    "lost",
]
_EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


class PilotLeadCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    email: str = Field(min_length=5, max_length=320)
    organization: str | None = Field(default=None, max_length=200)
    role: str | None = Field(default=None, max_length=160)
    country: str | None = Field(default=None, max_length=120)
    plan_interest: PilotPlan
    use_case: str = Field(min_length=20, max_length=4000)
    states_or_periods: str | None = Field(default=None, max_length=2000)
    preferred_format: str | None = Field(default=None, max_length=80)
    expected_users: int | None = Field(default=None, ge=1, le=10000)
    website: str | None = Field(default=None, max_length=200)

    @field_validator(
        "name",
        "email",
        "organization",
        "role",
        "country",
        "use_case",
        "states_or_periods",
        "preferred_format",
        "website",
        mode="before",
    )
    @classmethod
    def strip_text(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = value.lower()
        if not _EMAIL_PATTERN.fullmatch(normalized):
            raise ValueError("Enter a valid email address.")
        return normalized


class PilotLeadAccepted(BaseModel):
    id: uuid.UUID
    status: Literal["received"] = "received"
    message: str = "Your pilot request has been received."


class PilotLeadAdminItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    email: str
    organization: str | None
    role: str | None
    country: str | None
    plan_interest: str
    use_case: str
    states_or_periods: str | None
    preferred_format: str | None
    expected_users: int | None
    status: str
    source: str
    owner_name: str | None = None
    next_action: str | None = None
    next_action_at: datetime | None = None
    closed_reason: str | None = None
    converted_organization_id: uuid.UUID | None = None
    status_changed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class PilotLeadUpdate(BaseModel):
    status: PilotLeadStatus | None = None
    owner_name: str | None = Field(default=None, max_length=200)
    next_action: str | None = Field(default=None, max_length=500)
    next_action_at: datetime | None = None
    closed_reason: str | None = Field(default=None, max_length=1000)
    converted_organization_id: uuid.UUID | None = None

    @field_validator("owner_name", "next_action", "closed_reason", mode="before")
    @classmethod
    def normalize_optional_text(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip() or None
        return value


class CommercialAnalytics(BaseModel):
    generated_at: datetime
    leads_total: int
    leads_by_status: dict[str, int]
    leads_by_plan: dict[str, int]
    active_subscriptions_total: int
    active_subscriptions_by_plan: dict[str, int]
    successful_payment_count: int
    successful_payment_revenue_naira: str
    events_last_30_days: dict[str, int]
    statement: str
