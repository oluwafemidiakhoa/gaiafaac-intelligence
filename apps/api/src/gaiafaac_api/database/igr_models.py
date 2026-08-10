from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import (
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
from gaiafaac_api.database.enums import ReportedUnit, VerificationStatus

MONEY = Numeric(24, 2)


class IgrPeriodType(StrEnum):
    ANNUAL = "annual"
    QUARTERLY = "quarterly"


def _enum_type(enum: type[StrEnum], name: str) -> Enum:
    return Enum(
        enum,
        name=name,
        native_enum=False,
        create_constraint=True,
        values_callable=lambda members: [member.value for member in members],
    )


class StateIgrRecord(Base):
    """A source-linked state internally generated revenue observation."""

    __tablename__ = "state_igr_records"
    __table_args__ = (
        UniqueConstraint(
            "state_id",
            "period_start",
            "period_end",
            name="uq_state_igr_state_period",
        ),
        CheckConstraint("period_start <= period_end", name="ck_state_igr_period_order"),
        CheckConstraint("igr_amount >= 0", name="ck_state_igr_amount_nonnegative"),
        CheckConstraint(
            "NOT (is_demo AND is_published)",
            name="ck_state_igr_demo_not_published",
        ),
        CheckConstraint(
            "(period_type = 'annual' AND quarter IS NULL) OR "
            "(period_type = 'quarterly' AND quarter BETWEEN 1 AND 4)",
            name="ck_state_igr_period_shape",
        ),
        Index("ix_state_igr_year_state", "fiscal_year", "state_id"),
        Index("ix_state_igr_period", "period_start", "period_end"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    state_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("states.state_id", ondelete="RESTRICT"), nullable=False, index=True
    )
    source_document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("source_documents.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    fiscal_year: Mapped[int] = mapped_column(Integer, nullable=False)
    period_type: Mapped[IgrPeriodType] = mapped_column(
        _enum_type(IgrPeriodType, "igr_period_type"), nullable=False
    )
    quarter: Mapped[int | None] = mapped_column(Integer)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    igr_amount: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    igr_amount_original: Mapped[str] = mapped_column(String(120), nullable=False)
    reported_unit: Mapped[ReportedUnit] = mapped_column(
        _enum_type(ReportedUnit, "igr_reported_unit"),
        nullable=False,
        default=ReportedUnit.UNSPECIFIED,
    )
    publication_date: Mapped[date | None] = mapped_column(Date)
    source_page: Mapped[int | None] = mapped_column(Integer)
    source_table: Mapped[str | None] = mapped_column(String(160))
    verification_status: Mapped[VerificationStatus] = mapped_column(
        _enum_type(VerificationStatus, "igr_verification_status"),
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
