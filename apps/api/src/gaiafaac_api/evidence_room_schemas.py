from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

EvidenceReferenceKind = Literal[
    "organization_alert",
    "fiscal_proof",
    "decision_packet",
    "source",
    "fiscal_event",
]


class EvidenceRoomCreateRequest(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str | None = Field(default=None, max_length=5000)


class EvidenceRoomStatusUpdate(BaseModel):
    status: Literal["open", "closed", "archived"]


class EvidenceReferenceCreateRequest(BaseModel):
    reference_kind: EvidenceReferenceKind
    reference_id: str = Field(min_length=1, max_length=240)
    state_slug: str | None = Field(default=None, max_length=100)
    revenue_month: date | None = None
    year: int | None = Field(default=None, ge=2000, le=2100)


class EvidenceRoomNoteCreateRequest(BaseModel):
    body: str = Field(min_length=1, max_length=20000)


class EvidenceRoomNoteUpdateRequest(BaseModel):
    body: str = Field(min_length=1, max_length=20000)


class EvidenceRoomEvidenceResponse(BaseModel):
    id: uuid.UUID
    reference_kind: EvidenceReferenceKind
    reference_id: str
    reference_uri: str | None
    source_sha256: str | None
    record_sha256: str
    snapshot: dict[str, Any]
    captured_by_user_id: uuid.UUID | None
    captured_at: datetime


class EvidenceRoomNoteResponse(BaseModel):
    id: uuid.UUID
    author_user_id: uuid.UUID | None
    body: str
    created_at: datetime
    updated_at: datetime


class EvidenceRoomSummary(BaseModel):
    id: uuid.UUID
    title: str
    description: str | None
    status: Literal["open", "closed", "archived"]
    created_by_user_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
    evidence_count: int = 0
    note_count: int = 0


class EvidenceRoomDetail(EvidenceRoomSummary):
    evidence: list[EvidenceRoomEvidenceResponse]
    notes: list[EvidenceRoomNoteResponse]
