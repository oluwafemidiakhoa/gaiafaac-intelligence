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


class BudgetMetric(StrEnum):
    RECURRENT_REVENUE = "recurrent_revenue"
    FAAC_REVENUE = "faac_revenue"
    INDEPENDENT_REVENUE = "independent_revenue"
    RECURRENT_EXPENDITURE = "recurrent_expenditure"
    PERSONNEL_COST = "personnel_cost"
    OTHER_NON_DEBT_RECURRENT = "other_non_debt_recurrent"
    BUDGETED_DEBT_SERVICE = "budgeted_debt_service"
    TRANSFER_TO_CAPITAL_ACCOUNT = "transfer_to_capital_account"
    OTHER_RECEIPTS = "other_receipts"
    AID_AND_GRANTS = "aid_and_grants"
    CAPITAL_DEVELOPMENT_FUND_RECEIPTS = "capital_development_fund_receipts"
    CAPITAL_EXPENDITURE = "capital_expenditure"
    TOTAL_REVENUE = "total_revenue"
    TOTAL_EXPENDITURE = "total_expenditure"


def _enum_type(enum: type[StrEnum], name: str) -> Enum:
    return Enum(
        enum,
        name=name,
        native_enum=False,
        create_constraint=True,
        values_callable=lambda members: [member.value for member in members],
    )


class StateBudgetRecord(Base):
    """A source-linked approved-budget observation awaiting governed review."""

    __tablename__ = "state_budget_records"
    __table_args__ = (
        UniqueConstraint(
            "source_document_id",
            "state_id",
            "metric",
            name="uq_state_budget_source_state_metric",
        ),
        CheckConstraint("fiscal_year >= 2000", name="ck_state_budget_fiscal_year"),
        CheckConstraint("amount >= 0", name="ck_state_budget_amount_nonnegative"),
        CheckConstraint("length(currency) = 3", name="ck_state_budget_currency_length"),
        CheckConstraint(
            "NOT (is_demo AND is_published)",
            name="ck_state_budget_demo_not_published",
        ),
        Index("ix_state_budget_period_metric", "fiscal_year", "metric"),
        Index("ix_state_budget_state_year", "state_id", "fiscal_year"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    state_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("states.state_id", ondelete="RESTRICT"), nullable=False, index=True
    )
    source_document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("source_documents.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    fiscal_year: Mapped[int] = mapped_column(Integer, nullable=False)
    metric: Mapped[BudgetMetric] = mapped_column(
        _enum_type(BudgetMetric, "budget_metric"), nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    amount_original: Mapped[str] = mapped_column(String(120), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="NGN")
    source_page: Mapped[int | None] = mapped_column(Integer)
    source_table: Mapped[str | None] = mapped_column(String(200))
    extraction_method: Mapped[str] = mapped_column(String(120), nullable=False)
    verification_status: Mapped[VerificationStatus] = mapped_column(
        _enum_type(VerificationStatus, "budget_verification_status"),
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
