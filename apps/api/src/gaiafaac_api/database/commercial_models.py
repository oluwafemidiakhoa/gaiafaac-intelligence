from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Index, Integer, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from gaiafaac_api.database.base import Base


class PilotLead(Base):
    """A prospective commercial customer captured through the public pilot form."""

    __tablename__ = "pilot_leads"
    __table_args__ = (
        Index("ix_pilot_leads_status_created", "status", "created_at"),
        Index("ix_pilot_leads_email", "email"),
        Index("ix_pilot_leads_next_action", "status", "next_action_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    organization: Mapped[str | None] = mapped_column(String(200))
    role: Mapped[str | None] = mapped_column(String(160))
    country: Mapped[str | None] = mapped_column(String(120))
    plan_interest: Mapped[str] = mapped_column(String(40), nullable=False)
    use_case: Mapped[str] = mapped_column(Text, nullable=False)
    states_or_periods: Mapped[str | None] = mapped_column(Text)
    preferred_format: Mapped[str | None] = mapped_column(String(80))
    expected_users: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="new")
    source: Mapped[str] = mapped_column(String(80), nullable=False, default="website")

    # Legacy request metadata is retained for historical rows but new intake no longer
    # populates these fields. Commercial analytics intentionally never reads them.
    ip_address: Mapped[str | None] = mapped_column(String(64))
    user_agent: Mapped[str | None] = mapped_column(String(500))

    owner_name: Mapped[str | None] = mapped_column(String(200))
    next_action: Mapped[str | None] = mapped_column(String(500))
    next_action_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    closed_reason: Mapped[str | None] = mapped_column(String(1000))
    status_changed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    converted_organization_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class CommercialEvent(Base):
    """First-party server-side commercial event with no fingerprinting metadata."""

    __tablename__ = "commercial_events"
    __table_args__ = (
        Index("ix_commercial_events_name_occurred", "event_name", "occurred_at"),
        Index("ix_commercial_events_org_occurred", "organization_id", "occurred_at"),
        Index("ix_commercial_events_subject", "subject_type", "subject_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    event_name: Mapped[str] = mapped_column(String(80), nullable=False)
    subject_type: Mapped[str | None] = mapped_column(String(80))
    subject_id: Mapped[str | None] = mapped_column(String(160))
    source: Mapped[str] = mapped_column(String(80), nullable=False, default="server")
    event_metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
