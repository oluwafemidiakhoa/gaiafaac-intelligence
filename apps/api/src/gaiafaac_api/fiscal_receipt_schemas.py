from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class FiscalReceiptEvidenceItem(BaseModel):
    reference_kind: str
    reference_id: str
    reference_uri: str | None
    source_sha256: str | None
    record_sha256: str
    captured_at: datetime


class FiscalReceiptResponse(BaseModel):
    id: uuid.UUID
    room_id: uuid.UUID
    organization_id: uuid.UUID
    created_by_user_id: uuid.UUID | None
    evidence_cutoff: datetime | None
    methodology_version: str
    receipt_sha256: str = Field(min_length=64, max_length=64)
    manifest: dict[str, Any]
    created_at: datetime


class FiscalReceiptSummary(BaseModel):
    id: uuid.UUID
    room_id: uuid.UUID
    evidence_cutoff: datetime | None
    methodology_version: str
    receipt_sha256: str = Field(min_length=64, max_length=64)
    evidence_count: int
    created_at: datetime


class FiscalReceiptVerification(BaseModel):
    id: uuid.UUID
    receipt_sha256: str = Field(min_length=64, max_length=64)
    methodology_version: str
    created_at: datetime
    evidence_cutoff: datetime | None
    jurisdictions: list[str]
    evidence_domains: list[str]
    evidence_count: int
    source_sha256s: list[str]
    evidence_record_sha256s: list[str]
    evidence_kinds: list[str]
    statement: str
    limitations: list[str]
