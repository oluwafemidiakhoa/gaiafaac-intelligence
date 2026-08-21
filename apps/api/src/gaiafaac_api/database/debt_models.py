from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from gaiafaac_api.database.base import Base
from gaiafaac_api.database.enums import VerificationStatus

MONEY = Numeric(24, 2)


class DebtKind(StrEnum):
    DOMESTIC = "domestic"
    EXTERNAL = "external"


def _enum_type(enum: type[StrEnum], name: str) -> Enum:
    return Enum(
        enum,
        name=name,
        native_enum=False,
        create_constraint=True,
        values_callable=lambda members: [member.value for member in members],
    )


class StateDebtRecord(Base):
    """A source-linked DMO state/FCT debt observation awaiting governed review."""

    __tablename__ = "state_debt_records"
    __table_args__ = (
        UniqueConstraint(
            "source_document_id",
            "state_id",
            name="uq_state_debt_source_state",
        ),
        CheckConstraint("debt_amount >= 0", name="ck_state_debt_amount_nonnegative"),
        CheckConstraint("length(currency) = 3", name="ck_state_debt_currency_length"),
        CheckConstraint(
            "NOT (is_demo AND is_published)",
            name="ck_state_debt_demo_not_published",
        ),
        Index("ix_state_debt_period_kind", "as_of_date", "debt_kind"),
        Index("ix_state_debt_state_kind", "state_id", "debt_kind", "as_of_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    state_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("states.state_id", ondelete="RESTRICT"), nullable=False, index=True
    )
    source_document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("source_documents.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    debt_kind: Mapped[DebtKind] = mapped_column(_enum_type(DebtKind, "debt_kind"), nullable=False)
    as_of_date: Mapped[date] = mapped_column(Date, nullable=False)
    debt_amount: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    debt_amount_original: Mapped[str] = mapped_column(String(120), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    components: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    source_page: Mapped[int | None] = mapped_column(Integer)
    source_table: Mapped[str | None] = mapped_column(String(160))
    verification_status: Mapped[VerificationStatus] = mapped_column(
        _enum_type(VerificationStatus, "debt_verification_status"),
        nullable=False,
        default=VerificationStatus.PENDING,
    )
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_demo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
