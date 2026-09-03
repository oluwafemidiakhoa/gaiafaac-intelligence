from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class PendingIgrReviewItem(BaseModel):
    source_document_id: str
    fiscal_year: int
    source_organization: str
    processing_status: str
    covered_states: int
    expected_states: int
    approved: bool = False
    approved_by: str | None = None
    created_at: datetime | None


class IgrReviewSource(BaseModel):
    source_organization: str
    source_url: str | None
    original_filename: str
    sha256: str
    document_version: str


class IgrReviewRecordItem(BaseModel):
    state_name: str
    state_code: str
    igr_amount: str
    reported_unit: str
    verification_status: str
    is_published: bool


class IgrReviewApproval(BaseModel):
    actor_user_id: str | None
    actor_name: str | None
    created_at: datetime


class IgrReviewPacket(BaseModel):
    source_document_id: str
    fiscal_year: int
    source: IgrReviewSource
    covered_states: int
    expected_states: int
    records: list[IgrReviewRecordItem]
    approval: IgrReviewApproval | None = None
    published: bool = False


class IgrApproveRequest(BaseModel):
    reviewer_id: uuid.UUID
    attestation: bool


class IgrPublishRequest(BaseModel):
    publisher_id: uuid.UUID
    attestation: bool


class IgrReviewActionResponse(BaseModel):
    source_document_id: str
    fiscal_year: int
    records_affected: int
    published: bool
