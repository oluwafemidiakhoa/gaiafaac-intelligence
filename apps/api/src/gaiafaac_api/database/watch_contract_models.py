from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
    event,
    func,
)
from sqlalchemy.orm import Mapped, Mapper, mapped_column

from gaiafaac_api.database.base import Base


class FiscalWatchContract(Base):
    """Organization monitoring mandate tied to a Decision Room and baseline receipt."""

    __tablename__ = "fiscal_watch_contracts"
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'paused', 'archived')",
            name="ck_fiscal_watch_contract_status",
        ),
        CheckConstraint(
            "minimum_severity IN ('informational', 'watch', 'elevated', 'notable', 'material', 'critical')",
            name="ck_fiscal_watch_contract_minimum_severity",
        ),
        CheckConstraint(
            "escalation_after_minutes >= 15 AND escalation_after_minutes <= 10080",
            name="ck_fiscal_watch_contract_escalation_window",
        ),
        Index("ix_fiscal_watch_contracts_org_status", "organization_id", "status"),
        Index("ix_fiscal_watch_contracts_room_created", "room_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    room_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("evidence_rooms.id", ondelete="CASCADE"), nullable=False, index=True
    )
    baseline_receipt_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("fiscal_receipts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    state_codes: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    event_types: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    minimum_severity: Mapped[str] = mapped_column(String(24), nullable=False, default="watch")
    escalation_after_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1440, server_default="1440"
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    last_evaluated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class FiscalWatchContractMatch(Base):
    """Immutable evidence that one governed organization alert matched a contract."""

    __tablename__ = "fiscal_watch_contract_matches"
    __table_args__ = (
        UniqueConstraint("contract_id", "organization_alert_id", name="uq_watch_contract_match"),
        Index("ix_watch_contract_matches_contract_matched", "contract_id", "matched_at"),
        Index("ix_watch_contract_matches_room_matched", "room_id", "matched_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("fiscal_watch_contracts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    room_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("evidence_rooms.id", ondelete="CASCADE"), nullable=False, index=True
    )
    organization_alert_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organization_alerts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    matched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class FiscalWatchContractReview(Base):
    """Mutable organization workflow created for one immutable Watch Contract match."""

    __tablename__ = "fiscal_watch_contract_reviews"
    __table_args__ = (
        CheckConstraint(
            "status IN ('open', 'acknowledged', 'resolved')",
            name="ck_fiscal_watch_contract_review_status",
        ),
        UniqueConstraint("match_id", name="uq_fiscal_watch_contract_review_match"),
        Index(
            "ix_fiscal_watch_contract_reviews_org_status_due",
            "organization_id",
            "status",
            "due_at",
        ),
        Index(
            "ix_fiscal_watch_contract_reviews_contract_created",
            "contract_id",
            "created_at",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    match_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("fiscal_watch_contract_matches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    contract_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("fiscal_watch_contracts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    room_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("evidence_rooms.id", ondelete="CASCADE"), nullable=False, index=True
    )
    assigned_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open")
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    escalated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    acknowledged_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolved_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    resolution_note: Mapped[str | None] = mapped_column(String(5000))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class FiscalWatchContractDelivery(Base):
    """Durable delivery state for one operational review and one destination."""

    __tablename__ = "fiscal_watch_contract_deliveries"
    __table_args__ = (
        CheckConstraint(
            "channel IN ('in_app', 'email', 'webhook')",
            name="ck_fiscal_watch_contract_delivery_channel",
        ),
        CheckConstraint(
            "status IN ('pending', 'delivered', 'retrying', 'dead_letter', 'deferred', 'failed')",
            name="ck_fiscal_watch_contract_delivery_status",
        ),
        UniqueConstraint(
            "review_id",
            "channel",
            "destination_key",
            name="uq_fiscal_watch_contract_delivery_destination",
        ),
        Index(
            "ix_fiscal_watch_contract_deliveries_org_created",
            "organization_id",
            "created_at",
        ),
        Index(
            "ix_fiscal_watch_contract_deliveries_status_next",
            "status",
            "next_attempt_at",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    review_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("fiscal_watch_contract_reviews.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    match_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("fiscal_watch_contract_matches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    contract_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("fiscal_watch_contracts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    recipient_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    endpoint_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("organization_webhook_endpoints.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    channel: Mapped[str] = mapped_column(String(24), nullable=False, default="in_app")
    destination_key: Mapped[str] = mapped_column(
        String(200), nullable=False, default="organization_watch_inbox"
    )
    recipient_address: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="delivered")
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    next_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    response_status: Mapped[int | None] = mapped_column(Integer)
    response_body_excerpt: Mapped[str | None] = mapped_column(String(1000))
    last_error: Mapped[str | None] = mapped_column(String(500))
    payload_sha256: Mapped[str | None] = mapped_column(String(64))
    payload: Mapped[dict | None] = mapped_column(JSON)
    details: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class FiscalWatchContractDeliveryAttempt(Base):
    """Append-only record of one actual outbound Watch delivery attempt."""

    __tablename__ = "fiscal_watch_contract_delivery_attempts"
    __table_args__ = (
        UniqueConstraint(
            "delivery_id",
            "attempt_number",
            name="uq_fiscal_watch_contract_delivery_attempt_number",
        ),
        Index(
            "ix_fiscal_watch_contract_delivery_attempts_delivery",
            "delivery_id",
            "attempt_number",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    delivery_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("fiscal_watch_contract_deliveries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    attempted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    response_status: Mapped[int | None] = mapped_column(Integer)
    response_body_excerpt: Mapped[str | None] = mapped_column(String(1000))
    error: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


def _immutable_attempt(_mapper: Mapper[Any], _connection: Any, _target: Any) -> None:
    raise ValueError("Watch delivery attempt records are immutable.")


event.listen(FiscalWatchContractDeliveryAttempt, "before_update", _immutable_attempt)
event.listen(FiscalWatchContractDeliveryAttempt, "before_delete", _immutable_attempt)
