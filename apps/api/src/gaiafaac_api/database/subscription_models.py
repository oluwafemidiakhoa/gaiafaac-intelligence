"""Legacy billing support models plus the payment audit ledger.

Canonical customer entitlement lives in ``database.models.Subscription``. New payment
records link to that canonical subscription through ``canonical_subscription_id``.
The older tier/subscription/usage/invoice tables remain readable for historical
compatibility while runtime entitlement and revenue reporting use the canonical model.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import (
    DateTime,
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


class SubscriptionStatus(str, Enum):
    """Legacy subscription lifecycle states."""

    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class TierName(str, Enum):
    """Legacy predefined subscription tiers."""

    FREE = "free"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class SubscriptionTier(Base):
    """Legacy tier definition retained for historical compatibility."""

    __tablename__ = "subscription_tiers"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    price_naira: Mapped[int] = mapped_column(Integer, nullable=False)
    requests_per_month: Mapped[int] = mapped_column(Integer, nullable=False)
    exports_per_month: Mapped[int] = mapped_column(Integer, nullable=False)
    features: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<SubscriptionTier {self.name} ₦{self.price_naira}/month>"


class OrganizationSubscription(Base):
    """Legacy organization subscription retained only for historical compatibility."""

    __tablename__ = "organization_subscriptions"
    __table_args__ = (
        Index("ix_organization_subscriptions_org_expires", "organization_id", "expires_at"),
        UniqueConstraint("organization_id", name="uq_organization_subscriptions_org"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tier_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("subscription_tiers.id", ondelete="RESTRICT"), nullable=False
    )
    tier_name: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=SubscriptionStatus.ACTIVE)
    paystack_subscription_id: Mapped[str | None] = mapped_column(String(100))
    paystack_authorization_code: Mapped[str | None] = mapped_column(String(200))
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    renewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    api_requests_used: Mapped[int] = mapped_column(Integer, default=0)
    exports_used: Mapped[int] = mapped_column(Integer, default=0)
    last_reset_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    def is_active(self) -> bool:
        return self.status == SubscriptionStatus.ACTIVE and self.expires_at > datetime.utcnow()

    def reset_monthly_usage(self) -> None:
        self.api_requests_used = 0
        self.exports_used = 0
        self.last_reset_at = datetime.utcnow(tz=None)

    def __repr__(self) -> str:
        return f"<OrganizationSubscription {self.organization_id} {self.tier_name} {self.status}>"


class PaymentRecord(Base):
    """Payment transaction audit record tied to canonical subscription when available."""

    __tablename__ = "payment_records"
    __table_args__ = (
        Index("ix_payment_records_org_created", "organization_id", "created_at"),
        Index("ix_payment_records_status_created", "status", "created_at"),
        Index("ix_payment_records_canonical_subscription", "canonical_subscription_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Deprecated legacy relation. Existing historical rows are preserved.
    subscription_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("organization_subscriptions.id", ondelete="SET NULL"), nullable=True
    )
    canonical_subscription_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("subscriptions.id", ondelete="SET NULL"), nullable=True
    )
    paystack_transaction_id: Mapped[str | None] = mapped_column(String(100), unique=True)
    amount_naira: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    invoice_number: Mapped[str | None] = mapped_column(String(50), unique=True)
    description: Mapped[str | None] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    def __repr__(self) -> str:
        return f"<PaymentRecord ₦{self.amount_naira} {self.status}>"


class UsageLog(Base):
    """Legacy usage log retained for historical compatibility."""

    __tablename__ = "usage_logs"
    __table_args__ = (
        Index("ix_usage_logs_org_created", "organization_id", "created_at"),
        Index("ix_usage_logs_subscription_created", "subscription_id", "created_at"),
        Index("ix_usage_logs_event_type", "event_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    subscription_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organization_subscriptions.id", ondelete="CASCADE"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    endpoint: Mapped[str | None] = mapped_column(String(200))
    method: Mapped[str | None] = mapped_column(String(10))
    response_status: Mapped[int | None] = mapped_column(Integer)
    user_id: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<UsageLog {self.event_type} {self.organization_id}>"


class BillingEvent(Base):
    """Legacy billing event retained for historical invoice compatibility."""

    __tablename__ = "billing_events"
    __table_args__ = (
        Index("ix_billing_events_org_created", "organization_id", "created_at"),
        Index("ix_billing_events_event_type", "event_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    subscription_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organization_subscriptions.id", ondelete="CASCADE"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    amount_naira: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    is_invoiced: Mapped[bool] = mapped_column(default=False)
    invoice_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("invoices.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<BillingEvent {self.event_type} ₦{self.amount_naira}>"


class Invoice(Base):
    """Legacy formal invoice record retained for historical compatibility."""

    __tablename__ = "invoices"
    __table_args__ = (
        Index("ix_invoices_org_created", "organization_id", "created_at"),
        Index("ix_invoices_status", "status"),
        UniqueConstraint("invoice_number", name="uq_invoices_number"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    subscription_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organization_subscriptions.id", ondelete="CASCADE"), nullable=False
    )
    invoice_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    subtotal_naira: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    tax_naira: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    total_naira: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    paid_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    line_items: Mapped[str | None] = mapped_column(String(2000))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    def __repr__(self) -> str:
        return f"<Invoice {self.invoice_number} ₦{self.total_naira} {self.status}>"
