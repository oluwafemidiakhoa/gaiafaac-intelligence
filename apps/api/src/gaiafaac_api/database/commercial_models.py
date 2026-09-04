from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Uuid,
    event,
    select,
    update,
    func,
)
from sqlalchemy.engine import Connection
from sqlalchemy.orm import Mapped, Mapper, mapped_column

from gaiafaac_api.database.base import Base
from gaiafaac_api.database.models import Subscription
from gaiafaac_api.database.subscription_models import PaymentRecord


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

    # Retained only for compatibility with historical rows. New intake intentionally
    # does not collect network/device metadata.
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


def _capture_successful_payment(
    _mapper: Mapper[Any],
    connection: Connection,
    target: PaymentRecord,
) -> None:
    """Attach new revenue to canonical entitlement and emit one factual conversion event."""

    if target.status != "success" or not target.paystack_transaction_id:
        return

    canonical_id = connection.scalar(
        select(Subscription.id).where(
            Subscription.organization_id == target.organization_id,
            Subscription.external_subscription_id == target.paystack_transaction_id,
        )
    )
    if canonical_id is not None and target.canonical_subscription_id != canonical_id:
        connection.execute(
            update(PaymentRecord)
            .where(PaymentRecord.id == target.id)
            .values(canonical_subscription_id=canonical_id)
        )

    subject_id = str(target.id)
    existing = connection.scalar(
        select(CommercialEvent.id).where(
            CommercialEvent.event_name == "payment_confirmed",
            CommercialEvent.subject_type == "payment_record",
            CommercialEvent.subject_id == subject_id,
        )
    )
    if existing is not None:
        return

    connection.execute(
        CommercialEvent.__table__.insert().values(
            id=uuid.uuid4(),
            organization_id=target.organization_id,
            event_name="payment_confirmed",
            subject_type="payment_record",
            subject_id=subject_id,
            source="server",
            event_metadata={
                "amount_naira": str(target.amount_naira),
                "invoice_number": target.invoice_number,
                "payment_reference": target.paystack_transaction_id,
            },
        )
    )


event.listen(PaymentRecord, "after_insert", _capture_successful_payment)
event.listen(PaymentRecord, "after_update", _capture_successful_payment)
