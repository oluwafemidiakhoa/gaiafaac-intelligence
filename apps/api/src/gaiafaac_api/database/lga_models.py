from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from gaiafaac_api.database.base import Base
from gaiafaac_api.database.enums import ReportedUnit, VerificationStatus
from gaiafaac_api.database.models import (
    MONEY,
    IdMixin,
    PublishableMixin,
    TimestampMixin,
    enum_type,
)


class LocalGovernment(IdMixin, TimestampMixin, Base):
    """A governed Nigerian local-government jurisdiction.

    Names are retained as the official OAGF report presents them. ``slug`` is
    state-scoped because local-government names are not assumed globally unique.
    The FCT's six Area Councils are represented in this same jurisdiction layer
    because OAGF Table IV enumerates them alongside the 768 state LGAs.
    """

    __tablename__ = "local_governments"
    __table_args__ = (
        UniqueConstraint("state_id", "slug", name="uq_local_government_state_slug"),
        UniqueConstraint("state_id", "official_name", name="uq_local_government_state_name"),
        Index("ix_local_governments_state_name", "state_id", "official_name"),
    )

    state_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("states.state_id", ondelete="RESTRICT"), nullable=False, index=True
    )
    official_name: Mapped[str] = mapped_column(String(160), nullable=False)
    slug: Mapped[str] = mapped_column(String(180), nullable=False)


class LocalGovernmentAllocation(IdMixin, TimestampMixin, PublishableMixin, Base):
    """One observed OAGF Table IV allocation for a local government and month."""

    __tablename__ = "local_government_allocations"
    __table_args__ = (
        UniqueConstraint(
            "reporting_period_id",
            "local_government_id",
            name="uq_lga_allocation_period_local_government",
        ),
        CheckConstraint(
            "NOT (is_demo AND is_published)", name="ck_lga_allocation_demo_not_published"
        ),
        Index("ix_lga_allocations_period_published", "reporting_period_id", "is_published"),
    )

    reporting_period_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("reporting_periods.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    local_government_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("local_governments.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    source_document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("source_documents.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    extraction_run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("extraction_runs.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    net_statutory_allocation: Mapped[Decimal | None] = mapped_column(MONEY)
    deduction_amount: Mapped[Decimal | None] = mapped_column(MONEY)
    ecology_share: Mapped[Decimal | None] = mapped_column(MONEY)
    ecology_transfer: Mapped[Decimal | None] = mapped_column(MONEY)
    net_ecology_share: Mapped[Decimal | None] = mapped_column(MONEY)
    vat_amount: Mapped[Decimal | None] = mapped_column(MONEY)
    total_net_allocation: Mapped[Decimal] = mapped_column(MONEY, nullable=False)

    net_statutory_original: Mapped[str | None] = mapped_column(String(120))
    deduction_original: Mapped[str | None] = mapped_column(String(120))
    ecology_share_original: Mapped[str | None] = mapped_column(String(120))
    ecology_transfer_original: Mapped[str | None] = mapped_column(String(120))
    net_ecology_original: Mapped[str | None] = mapped_column(String(120))
    vat_original: Mapped[str | None] = mapped_column(String(120))
    total_net_original: Mapped[str] = mapped_column(String(120), nullable=False)

    reported_unit: Mapped[ReportedUnit] = mapped_column(
        enum_type(ReportedUnit, "lga_allocation_reported_unit"),
        nullable=False,
        default=ReportedUnit.NAIRA,
    )
    source_page: Mapped[int | None]
    source_table: Mapped[str] = mapped_column(String(80), nullable=False, default="Table IV")
    verification_status: Mapped[VerificationStatus] = mapped_column(
        enum_type(VerificationStatus, "lga_allocation_verification_status"),
        nullable=False,
        default=VerificationStatus.REQUIRES_REVIEW,
    )
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class LocalGovernmentReview(IdMixin, TimestampMixin, Base):
    """Batch-level human approval state for one Table IV extraction run."""

    __tablename__ = "local_government_reviews"
    __table_args__ = (
        UniqueConstraint("extraction_run_id", name="uq_lga_review_extraction_run"),
        Index("ix_lga_review_period", "reporting_period_id"),
    )

    reporting_period_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("reporting_periods.id", ondelete="RESTRICT"), nullable=False
    )
    source_document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("source_documents.id", ondelete="RESTRICT"), nullable=False
    )
    extraction_run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("extraction_runs.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="requires_review")
    record_count: Mapped[int] = mapped_column(nullable=False)
    blocking_count: Mapped[int] = mapped_column(nullable=False, default=0)
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    published_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
