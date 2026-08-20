from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from gaiafaac_api.database.base import Base


class OrganizationWebhookEndpoint(Base):
    """Organization-scoped subscription to immutable Gaia Fiscal Events."""

    __tablename__ = "organization_webhook_endpoints"
    __table_args__ = (
        Index("ix_org_webhook_endpoints_org_enabled", "organization_id", "enabled"),
        Index("ix_org_webhook_endpoints_org_created", "organization_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    event_types: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    jurisdiction_codes: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    secret_salt: Mapped[str] = mapped_column(String(64), nullable=False)
    secret_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    disabled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class OrganizationWebhookDelivery(Base):
    """Auditable delivery state for one endpoint and one immutable Fiscal Event."""

    __tablename__ = "organization_webhook_deliveries"
    __table_args__ = (
        UniqueConstraint(
            "endpoint_id", "fiscal_event_id", name="uq_org_webhook_delivery_endpoint_event"
        ),
        CheckConstraint(
            "status IN ('pending', 'retrying', 'delivered', 'dead_letter', 'deferred')",
            name="ck_org_webhook_delivery_status",
        ),
        CheckConstraint("length(payload_sha256) = 64", name="ck_org_webhook_payload_hash"),
        Index("ix_org_webhook_deliveries_endpoint_status", "endpoint_id", "status"),
        Index("ix_org_webhook_deliveries_org_created", "organization_id", "created_at"),
        Index("ix_org_webhook_deliveries_next_attempt", "status", "next_attempt_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    endpoint_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organization_webhook_endpoints.id", ondelete="CASCADE"), nullable=False
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    fiscal_event_id: Mapped[str] = mapped_column(
        ForeignKey("fiscal_events.event_id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="pending")
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    next_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    response_status: Mapped[int | None] = mapped_column(Integer)
    response_body_excerpt: Mapped[str | None] = mapped_column(String(1000))
    last_error: Mapped[str | None] = mapped_column(String(500))
    signing_secret_version: Mapped[int] = mapped_column(Integer, nullable=False)
    payload_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
