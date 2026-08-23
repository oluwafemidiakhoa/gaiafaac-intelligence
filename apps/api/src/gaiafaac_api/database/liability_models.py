from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
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


class LiabilityMetric(StrEnum):
    CONTRACTOR_ARREARS = "contractor_arrears"
    PENSIONS_AND_GRATUITY_ARREARS = "pensions_and_gratuity_arrears"
    SALARY_ARREARS = "salary_arrears"
    OTHER_JUDGMENT_ARREARS = "other_judgment_arrears"
    TOTAL_DOMESTIC_ARREARS = "total_domestic_arrears"


def _enum_type(enum: type[StrEnum], name: str) -> Enum:
    return Enum(
        enum,
        name=name,
        native_enum=False,
        create_constraint=True,
        values_callable=lambda members: [member.value for member in members],
    )


class StateLiabilityRecord(Base):
    """A source-linked state liability observation awaiting governed review."""

    __tablename__ = "state_liability_records"
    __table_args__ = (
        UniqueConstraint(
            "source_document_id",
            "state_id",
            "metric",
            name="uq_state_liability_source_state_metric",
        ),
        CheckConstraint("fiscal_year >= 2000", name="ck_state_liability_fiscal_year"),
        CheckConstraint(
            "amount IS NULL OR amount >= 0",
            name="ck_state_liability_amount_nonnegative",
        ),
        CheckConstraint("length(currency) = 3", name="ck_state_liability_currency_length"),
        CheckConstraint(
            "NOT (is_demo AND is_published)",
            name="ck_state_liability_demo_not_published",
        ),
        Index("ix_state_liability_state_year", "state_id", "fiscal_year"),
        Index("ix_state_liability_period_metric", "fiscal_year", "metric"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    state_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("states.state_id", ondelete="RESTRICT"), nullable=False, index=True
    )
    source_document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("source_documents.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    fiscal_year: Mapped[int] = mapped_column(Integer, nullable=False)
    metric: Mapped[LiabilityMetric] = mapped_column(
        _enum_type(LiabilityMetric, "liability_metric"), nullable=False
    )
    amount: Mapped[Decimal | None] = mapped_column(MONEY)
    amount_text: Mapped[str] = mapped_column(String(120), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="NGN")
    source_page: Mapped[int] = mapped_column(Integer, nullable=False)
    source_table: Mapped[str] = mapped_column(String(200), nullable=False)
    extraction_method: Mapped[str] = mapped_column(String(120), nullable=False)
    verification_status: Mapped[VerificationStatus] = mapped_column(
        _enum_type(VerificationStatus, "liability_verification_status"),
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
