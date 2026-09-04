from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

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
