from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel


class PendingDmoReviewItem(BaseModel):
    source_document_id: str
    debt_kind: str
    as_of_date: date
    source_organization: str
    processing_status: str
    covered_states: int
    expected_states: int
    approved: bool = False
    approved_by: str | None = None
    created_at: datetime | None


class DmoReviewSource(BaseModel):
    source_organization: str
    source_url: str | None
    original_filename: str
    sha256: str
    document_version: str


class DmoReviewRecordItem(BaseModel):
    state_name: str
    state_code: str
    debt_amount: str
    currency: str
    verification_status: str
    is_published: bool


class DmoReviewApproval(BaseModel):
    actor_user_id: str | None
    actor_name: str | None
    created_at: datetime


class DmoReviewPacket(BaseModel):
    source_document_id: str
    debt_kind: str
    as_of_date: date
    source: DmoReviewSource
    covered_states: int
    expected_states: int
    records: list[DmoReviewRecordItem]
    approval: DmoReviewApproval | None = None
    published: bool = False


class DmoApproveRequest(BaseModel):
    reviewer_id: uuid.UUID
    attestation: bool


class DmoPublishRequest(BaseModel):
    publisher_id: uuid.UUID
    attestation: bool


class DmoReviewActionResponse(BaseModel):
    source_document_id: str
    debt_kind: str
    as_of_date: date
    records_affected: int
    published: bool
