from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Index, Integer, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from gaiafaac_api.database.base import Base


class PilotLead(Base):
    """A prospective commercial customer captured through the public pilot form."""

    __tablename__ = "pilot_leads"
    __table_args__ = (
        Index("ix_pilot_leads_status_created", "status", "created_at"),
        Index("ix_pilot_leads_email", "email"),
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
    ip_address: Mapped[str | None] = mapped_column(String(64))
    user_agent: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
