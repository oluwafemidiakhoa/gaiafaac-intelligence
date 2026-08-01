from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

PilotPlan = Literal["analyst", "team", "api"]


class PilotLeadCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    email: EmailStr
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
    created_at: datetime
