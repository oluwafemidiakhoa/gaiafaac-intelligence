from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=200)
    email: str = Field(min_length=5, max_length=320)
    password: str = Field(min_length=12, max_length=200)
    organization_name: str = Field(min_length=2, max_length=200)


class LoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=320)
    password: str = Field(min_length=1, max_length=200)


class SessionResponse(BaseModel):
    token: str
    expires_at: datetime


class AccountProfile(BaseModel):
    user_id: uuid.UUID
    full_name: str
    email: str
    organization_id: uuid.UUID
    organization_name: str
    membership_role: Literal["owner", "admin", "member"]
    plan_code: str
    subscription_status: str | None
    historical_access: bool
    downloads: bool
    api_access: bool
    max_users: int


class CheckoutRequest(BaseModel):
    plan_code: Literal["analyst", "team", "api"]


class RedirectResponse(BaseModel):
    url: str


class InviteRequest(BaseModel):
    email: str = Field(min_length=5, max_length=320)
    full_name: str | None = Field(default=None, max_length=200)
    role: Literal["admin", "member"] = "member"


class InviteAcceptedRequest(BaseModel):
    token: str = Field(min_length=20, max_length=500)
    full_name: str = Field(min_length=2, max_length=200)
    password: str = Field(min_length=12, max_length=200)


class MemberItem(BaseModel):
    user_id: uuid.UUID
    full_name: str
    email: str
    role: str


class InviteItem(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str | None
    role: str
    expires_at: datetime


class ApiKeyCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)


class ApiKeyCreated(BaseModel):
    id: uuid.UUID
    name: str
    key_prefix: str
    api_key: str


class ApiKeyItem(BaseModel):
    id: uuid.UUID
    name: str
    key_prefix: str
    last_used_at: datetime | None
    revoked_at: datetime | None
