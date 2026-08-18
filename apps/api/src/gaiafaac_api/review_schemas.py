from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field


class PendingReviewItem(BaseModel):
    run_id: str
    reporting_label: str
    revenue_month: date
    source_organization: str
    status: str
    covered_states: int
    expected_states: int
    finding_count: int
    blocking_count: int
    approved: bool = False
    approved_by: str | None = None
    created_at: datetime | None


class ReviewSource(BaseModel):
    source_organization: str
    source_url: str | None
    original_filename: str
    sha256: str
    publication_date: date | None
    document_version: str


class ReviewAllocationItem(BaseModel):
    state_name: str
    state_code: str
    gross_total: str | None
    total_deductions: str | None
    net_allocation: str | None
    reported_unit: str
    verification_status: str
    extraction_confidence: str | None


class ReviewFindingItem(BaseModel):
    rule_code: str
    severity: str
    message: str
    details: dict[str, Any] | None
    outcome: str


class ReviewApproval(BaseModel):
    actor_user_id: str | None
    actor_name: str | None
    created_at: datetime
    note: str | None = None


class ReviewPacket(BaseModel):
    run_id: str
    reporting_label: str
    revenue_month: date
    status: str
    source: ReviewSource
    covered_states: int
    expected_states: int
    finding_count: int
    blocking_count: int
    allocations: list[ReviewAllocationItem]
    findings: list[ReviewFindingItem]
    approval: ReviewApproval | None = None


class ApproveReviewRequest(BaseModel):
    reviewer_id: uuid.UUID
    attestation: bool
    note: str | None = Field(default=None, max_length=2000)


class RejectReviewRequest(BaseModel):
    reviewer_id: uuid.UUID
    reason: str = Field(min_length=3, max_length=2000)


class PublishReviewRequest(BaseModel):
    publisher_id: uuid.UUID
    attestation: bool


class ReviewActionResponse(BaseModel):
    run_id: str
    status: str
    allocations_affected: int
    published: bool
