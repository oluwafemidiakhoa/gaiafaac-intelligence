"""Subscription tier and billing models for commercial monetization"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
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
    """Subscription lifecycle states"""

    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class TierName(str, Enum):
    """Predefined subscription tiers"""

    FREE = "free"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class SubscriptionTier(Base):
    """Subscription tier definition (Free, Professional, Enterprise)"""

    __tablename__ = "subscription_tiers"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    price_naira: Mapped[int] = mapped_column(Integer, nullable=False)  # 0, 50000, 500000
    requests_per_month: Mapped[int] = mapped_column(Integer, nullable=False)
    exports_per_month: Mapped[int] = mapped_column(Integer, nullable=False)
    features: Mapped[str] = mapped_column(String(500), nullable=False)  # JSON: ["watchlists", "alerts", "api"]
    description: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<SubscriptionTier {self.name} ₦{self.price_naira}/month>"


class OrganizationSubscription(Base):
    """Active subscription for an organization"""

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
    tier_name: Mapped[str] = mapped_column(String(50), nullable=False)  # Snapshot of tier name

    status: Mapped[str] = mapped_column(String(20), default=SubscriptionStatus.ACTIVE)
    paystack_subscription_id: Mapped[str | None] = mapped_column(String(100))
    paystack_authorization_code: Mapped[str | None] = mapped_column(String(200))

    # Billing period
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    renewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Usage tracking
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
        """Check if subscription is currently active"""
        return status == SubscriptionStatus.ACTIVE and self.expires_at > datetime.utcnow()

    def reset_monthly_usage(self) -> None:
        """Reset monthly API/export counters"""
        self.api_requests_used = 0
        self.exports_used = 0
        self.last_reset_at = datetime.utcnow(tz=None)

    def __repr__(self) -> str:
        return f"<OrganizationSubscription {self.organization_id} {self.tier_name} {self.status}>"


class PaymentRecord(Base):
    """Payment transaction record for audit trail"""

    __tablename__ = "payment_records"
    __table_args__ = (
        Index("ix_payment_records_org_created", "organization_id", "created_at"),
        Index("ix_payment_records_status_created", "status", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    subscription_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("organization_subscriptions.id", ondelete="SET NULL"), nullable=True
    )

    # Payment details
    paystack_transaction_id: Mapped[str | None] = mapped_column(String(100), unique=True)
    amount_naira: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # "success", "failed", "pending"

    # Invoice
    invoice_number: Mapped[str | None] = mapped_column(String(50), unique=True)
    description: Mapped[str | None] = mapped_column(String(200))

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    def __repr__(self) -> str:
        return f"<PaymentRecord ₦{self.amount_naira} {self.status}>"
