from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

ProjectReceiptIntegrityStatus = Literal["verified", "integrity_failure"]
ProjectReceiptRevisionStatus = Literal[
    "no_known_revision",
    "review_recommended",
    "source_registry_partial",
    "integrity_failure",
]


class ProjectReceiptVerification(BaseModel):
    purchase_id: uuid.UUID
    document_id: str = Field(min_length=8, max_length=80)
    artifact_sha256: str = Field(min_length=64, max_length=64)
    product_code: str
    product_label: str
    artifact_schema: str | None = None
    evidence_captured_at: str | None = None
    issued_at: datetime | None = None
    jurisdictions: list[str]
    source_sha256s: list[str]
    source_count: int
    integrity_status: ProjectReceiptIntegrityStatus
    revision_status: ProjectReceiptRevisionStatus
    revised_source_sha256s: list[str]
    unknown_source_sha256s: list[str]
    statement: str
    limitations: list[str]
