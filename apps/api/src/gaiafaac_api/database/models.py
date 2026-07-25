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
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from gaiafaac_api.database.base import Base
from gaiafaac_api.database.enums import (
    ComponentType,
    ExtractionStatus,
    ForecastMethod,
    InsightStatus,
    ProcessingStatus,
    ReportedUnit,
    SourceStatus,
    SubscriptionStatus,
    UserRole,
    ValidationSeverity,
    VerificationStatus,
)

MONEY = Numeric(24, 2)
PRECISE_NUMBER = Numeric(30, 10)
CONFIDENCE = Numeric(5, 4)


def enum_type(enum: type[StrEnum], name: str) -> Enum:
    return Enum(
        enum,
        name=name,
        native_enum=False,
        create_constraint=True,
        values_callable=lambda members: [member.value for member in members],
    )


class IdMixin:
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class PublishableMixin:
    is_demo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Organization(IdMixin, TimestampMixin, Base):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)


class User(IdMixin, TimestampMixin, Base):
    __tablename__ = "users"

    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("organizations.id", ondelete="SET NULL")
    )
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        enum_type(UserRole, "user_role"), nullable=False, default=UserRole.VIEWER
    )
    password_hash: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class State(IdMixin, TimestampMixin, Base):
    __tablename__ = "states"

    id: Mapped[uuid.UUID] = mapped_column(
        "state_id", Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    code: Mapped[str] = mapped_column(String(2), nullable=False, unique=True)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    geopolitical_zone: Mapped[str] = mapped_column(String(30), nullable=False)
    capital: Mapped[str] = mapped_column(String(100), nullable=False)
    is_fct: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class ReportingPeriod(IdMixin, TimestampMixin, PublishableMixin, Base):
    __tablename__ = "reporting_periods"
    __table_args__ = (
        UniqueConstraint(
            "revenue_month", "reporting_label", name="uq_reporting_period_month_label"
        ),
        CheckConstraint(
            "NOT (is_demo AND is_published)", name="ck_reporting_period_demo_not_published"
        ),
    )

    revenue_month: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    faac_meeting_date: Mapped[date | None] = mapped_column(Date)
    publication_date: Mapped[date | None] = mapped_column(Date)
    reporting_label: Mapped[str] = mapped_column(String(160), nullable=False)
    source_status: Mapped[SourceStatus] = mapped_column(
        enum_type(SourceStatus, "reporting_period_source_status"),
        nullable=False,
        default=SourceStatus.PENDING,
    )
    verification_status: Mapped[VerificationStatus] = mapped_column(
        enum_type(VerificationStatus, "verification_status"),
        nullable=False,
        default=VerificationStatus.PENDING,
    )


class SourceDocument(IdMixin, TimestampMixin, Base):
    __tablename__ = "source_documents"
    __table_args__ = (
        CheckConstraint("length(sha256) = 64", name="ck_source_document_sha256_length"),
        Index("ix_source_documents_publication_date", "publication_date"),
    )

    reporting_period_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("reporting_periods.id", ondelete="SET NULL")
    )
    source_organization: Mapped[str] = mapped_column(String(200), nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    mime_type: Mapped[str] = mapped_column(String(120), nullable=False)
    publication_date: Mapped[date | None] = mapped_column(Date)
    downloaded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    processing_status: Mapped[ProcessingStatus] = mapped_column(
        enum_type(ProcessingStatus, "processing_status"),
        nullable=False,
        default=ProcessingStatus.REGISTERED,
    )
    source_status: Mapped[SourceStatus] = mapped_column(
        enum_type(SourceStatus, "source_status"),
        nullable=False,
        default=SourceStatus.REGISTERED,
    )
    document_version: Mapped[str] = mapped_column(String(80), nullable=False, default="1")
    supersedes_document_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("source_documents.id", ondelete="SET NULL")
    )
    is_demo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class NationalDistribution(IdMixin, TimestampMixin, PublishableMixin, Base):
    __tablename__ = "national_distributions"
    __table_args__ = (
        UniqueConstraint(
            "reporting_period_id", "source_document_id", name="uq_national_distribution_source"
        ),
        CheckConstraint(
            "NOT (is_demo AND is_published)", name="ck_national_distribution_demo_not_published"
        ),
    )

    reporting_period_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("reporting_periods.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    source_document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("source_documents.id", ondelete="RESTRICT"), nullable=False
    )
    gross_amount: Mapped[Decimal | None] = mapped_column(MONEY)
    deductions_amount: Mapped[Decimal | None] = mapped_column(MONEY)
    net_distributable_amount: Mapped[Decimal | None] = mapped_column(MONEY)
    federal_amount: Mapped[Decimal | None] = mapped_column(MONEY)
    states_amount: Mapped[Decimal | None] = mapped_column(MONEY)
    local_governments_amount: Mapped[Decimal | None] = mapped_column(MONEY)
    vat_amount: Mapped[Decimal | None] = mapped_column(MONEY)
    statutory_amount: Mapped[Decimal | None] = mapped_column(MONEY)
    derivation_amount: Mapped[Decimal | None] = mapped_column(MONEY)
    gross_amount_original: Mapped[str | None] = mapped_column(String(120))
    deductions_amount_original: Mapped[str | None] = mapped_column(String(120))
    net_amount_original: Mapped[str | None] = mapped_column(String(120))
    reported_unit: Mapped[ReportedUnit] = mapped_column(
        enum_type(ReportedUnit, "reported_unit"),
        nullable=False,
        default=ReportedUnit.UNSPECIFIED,
    )
    verification_status: Mapped[VerificationStatus] = mapped_column(
        enum_type(VerificationStatus, "national_verification_status"),
        nullable=False,
        default=VerificationStatus.PENDING,
    )


class StateAllocation(IdMixin, TimestampMixin, PublishableMixin, Base):
    __tablename__ = "state_allocations"
    __table_args__ = (
        UniqueConstraint(
            "reporting_period_id", "state_id", name="uq_state_allocation_period_state"
        ),
        CheckConstraint(
            "NOT (is_demo AND is_published)", name="ck_state_allocation_demo_not_published"
        ),
        CheckConstraint(
            "extraction_confidence IS NULL "
            "OR (extraction_confidence >= 0 AND extraction_confidence <= 1)",
            name="ck_state_allocation_confidence_range",
        ),
    )

    reporting_period_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("reporting_periods.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    state_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("states.state_id", ondelete="RESTRICT"), nullable=False, index=True
    )
    source_document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("source_documents.id", ondelete="RESTRICT"), nullable=False
    )
    gross_total: Mapped[Decimal | None] = mapped_column(MONEY)
    total_deductions: Mapped[Decimal | None] = mapped_column(MONEY)
    net_allocation: Mapped[Decimal | None] = mapped_column(MONEY)
    gross_total_original: Mapped[str | None] = mapped_column(String(120))
    total_deductions_original: Mapped[str | None] = mapped_column(String(120))
    net_allocation_original: Mapped[str | None] = mapped_column(String(120))
    reported_unit: Mapped[ReportedUnit] = mapped_column(
        enum_type(ReportedUnit, "allocation_reported_unit"),
        nullable=False,
        default=ReportedUnit.UNSPECIFIED,
    )
    verification_status: Mapped[VerificationStatus] = mapped_column(
        enum_type(VerificationStatus, "allocation_verification_status"),
        nullable=False,
        default=VerificationStatus.PENDING,
    )
    extraction_confidence: Mapped[Decimal | None] = mapped_column(CONFIDENCE)
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class StateAllocationComponent(IdMixin, TimestampMixin, Base):
    __tablename__ = "state_allocation_components"

    state_allocation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("state_allocations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    component_type: Mapped[ComponentType] = mapped_column(
        enum_type(ComponentType, "component_type"), nullable=False
    )
    component_name: Mapped[str] = mapped_column(String(160), nullable=False)
    gross_amount: Mapped[Decimal | None] = mapped_column(MONEY)
    deduction_amount: Mapped[Decimal | None] = mapped_column(MONEY)
    net_amount: Mapped[Decimal | None] = mapped_column(MONEY)
    gross_amount_original: Mapped[str | None] = mapped_column(String(120))
    deduction_amount_original: Mapped[str | None] = mapped_column(String(120))
    net_amount_original: Mapped[str | None] = mapped_column(String(120))
    reported_unit: Mapped[ReportedUnit] = mapped_column(
        enum_type(ReportedUnit, "component_reported_unit"),
        nullable=False,
        default=ReportedUnit.UNSPECIFIED,
    )
    source_page: Mapped[int | None]
    source_table: Mapped[str | None] = mapped_column(String(160))


class StateIndicator(IdMixin, TimestampMixin, Base):
    __tablename__ = "state_indicators"
    __table_args__ = (
        UniqueConstraint(
            "reporting_period_id",
            "state_id",
            "indicator_type",
            "indicator_name",
            name="uq_state_indicator_period_state_name",
        ),
    )

    reporting_period_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("reporting_periods.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    state_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("states.state_id", ondelete="RESTRICT"), nullable=False, index=True
    )
    source_document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("source_documents.id", ondelete="RESTRICT"), nullable=False
    )
    indicator_type: Mapped[str] = mapped_column(String(80), nullable=False)
    indicator_name: Mapped[str] = mapped_column(String(160), nullable=False)
    value: Mapped[Decimal] = mapped_column(PRECISE_NUMBER, nullable=False)
    unit: Mapped[str] = mapped_column(String(80), nullable=False)
    methodology: Mapped[str | None] = mapped_column(Text)
    verification_status: Mapped[VerificationStatus] = mapped_column(
        enum_type(VerificationStatus, "indicator_verification_status"),
        nullable=False,
        default=VerificationStatus.PENDING,
    )


class ExtractionRun(IdMixin, TimestampMixin, Base):
    __tablename__ = "extraction_runs"

    source_document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("source_documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[ExtractionStatus] = mapped_column(
        enum_type(ExtractionStatus, "extraction_status"),
        nullable=False,
        default=ExtractionStatus.QUEUED,
    )
    extractor_name: Mapped[str] = mapped_column(String(160), nullable=False)
    extractor_version: Mapped[str] = mapped_column(String(80), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    records_extracted: Mapped[int] = mapped_column(nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text)
    configuration: Mapped[dict[str, Any] | None] = mapped_column(JSON)


class ValidationResult(IdMixin, Base):
    __tablename__ = "validation_results"
    __table_args__ = (
        Index("ix_validation_results_rule_code", "rule_code"),
        CheckConstraint(
            "state_allocation_id IS NOT NULL OR reporting_period_id IS NOT NULL",
            name="ck_validation_result_has_subject",
        ),
    )

    extraction_run_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("extraction_runs.id", ondelete="CASCADE")
    )
    reporting_period_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("reporting_periods.id", ondelete="CASCADE")
    )
    state_allocation_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("state_allocations.id", ondelete="CASCADE")
    )
    rule_code: Mapped[str] = mapped_column(String(100), nullable=False)
    outcome: Mapped[VerificationStatus] = mapped_column(
        enum_type(VerificationStatus, "validation_outcome"), nullable=False
    )
    severity: Mapped[ValidationSeverity] = mapped_column(
        enum_type(ValidationSeverity, "validation_severity"), nullable=False
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    tolerance: Mapped[Decimal | None] = mapped_column(MONEY)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class Forecast(IdMixin, TimestampMixin, PublishableMixin, Base):
    __tablename__ = "forecasts"
    __table_args__ = (
        CheckConstraint("lower_bound <= point_estimate", name="ck_forecast_lower_bound"),
        CheckConstraint("point_estimate <= upper_bound", name="ck_forecast_upper_bound"),
        CheckConstraint("NOT (is_demo AND is_published)", name="ck_forecast_demo_not_published"),
    )

    state_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("states.state_id", ondelete="RESTRICT"), index=True
    )
    target_period: Mapped[date] = mapped_column(Date, nullable=False)
    method: Mapped[ForecastMethod] = mapped_column(
        enum_type(ForecastMethod, "forecast_method"), nullable=False
    )
    point_estimate: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    lower_bound: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    upper_bound: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    training_start: Mapped[date] = mapped_column(Date, nullable=False)
    training_end: Mapped[date] = mapped_column(Date, nullable=False)
    metrics: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    verification_status: Mapped[VerificationStatus] = mapped_column(
        enum_type(VerificationStatus, "forecast_verification_status"),
        nullable=False,
        default=VerificationStatus.PENDING,
    )
    source_document_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("source_documents.id", ondelete="SET NULL")
    )


class GeneratedInsight(IdMixin, TimestampMixin, PublishableMixin, Base):
    __tablename__ = "generated_insights"
    __table_args__ = (
        CheckConstraint(
            "NOT (is_demo AND is_published)", name="ck_generated_insight_demo_not_published"
        ),
    )

    reporting_period_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("reporting_periods.id", ondelete="SET NULL")
    )
    state_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("states.state_id", ondelete="SET NULL")
    )
    source_document_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("source_documents.id", ondelete="SET NULL")
    )
    insight_type: Mapped[str] = mapped_column(String(100), nullable=False)
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)
    methodology: Mapped[str | None] = mapped_column(Text)
    model_name: Mapped[str | None] = mapped_column(String(160))
    grounding: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    verification_status: Mapped[VerificationStatus] = mapped_column(
        enum_type(VerificationStatus, "insight_verification_status"),
        nullable=False,
        default=VerificationStatus.PENDING,
    )
    status: Mapped[InsightStatus] = mapped_column(
        enum_type(InsightStatus, "insight_status"),
        nullable=False,
        default=InsightStatus.DRAFT,
    )


class Subscription(IdMixin, TimestampMixin, Base):
    __tablename__ = "subscriptions"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[SubscriptionStatus] = mapped_column(
        enum_type(SubscriptionStatus, "subscription_status"), nullable=False
    )
    plan_code: Mapped[str] = mapped_column(String(80), nullable=False)
    external_customer_id: Mapped[str | None] = mapped_column(String(160), unique=True)
    external_subscription_id: Mapped[str | None] = mapped_column(String(160), unique=True)
    current_period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AuditLog(IdMixin, Base):
    __tablename__ = "audit_logs"
    __table_args__ = (Index("ix_audit_logs_entity", "entity_type", "entity_id"),)

    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(120), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    request_id: Mapped[str | None] = mapped_column(String(120))
    ip_address: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )
