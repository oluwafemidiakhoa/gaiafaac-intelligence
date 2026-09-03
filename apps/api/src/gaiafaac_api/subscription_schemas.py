"""Pydantic schemas for subscription management and monetization"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class SubscriptionTierInfo(BaseModel):
    """Public subscription tier information"""

    id: uuid.UUID
    name: str
    price_naira: int
    requests_per_month: int
    exports_per_month: int
    features: list[str]
    description: str | None

    class Config:
        from_attributes = True


class SubscriptionTierResponse(SubscriptionTierInfo):
    """Detailed subscription tier for admin"""

    created_at: datetime


class PricingPageResponse(BaseModel):
    """Response for /pricing endpoint"""

    tiers: list[SubscriptionTierInfo]
    currency: str = "NGN"
    features_legend: dict[str, str] = {
        "watchlists": "Create state/LGA watchlists",
        "alerts": "Email alerts on fiscal changes",
        "api_access": "Programmatic API access",
        "csv_export": "Download data as CSV/JSON",
        "custom_reports": "Custom PDF reports",
        "webhooks": "Event webhooks for integration",
        "sla": "99.9% uptime guarantee",
        "dedicated_support": "Priority email/phone support",
    }


class SubscriptionCheckoutRequest(BaseModel):
    """Request to start subscription checkout"""

    tier_name: Literal["free", "professional", "enterprise"]
    email: str = Field(min_length=5, max_length=320)
    organization_name: str | None = Field(default=None, max_length=200)
    full_name: str = Field(min_length=2, max_length=200)


class PaystackCheckoutResponse(BaseModel):
    """Response with Paystack payment link"""

    checkout_url: str
    transaction_id: str
    amount_naira: int
    tier_name: str
    expires_at: datetime


class SubscriptionStatus(BaseModel):
    """Current subscription status for organization"""

    organization_id: uuid.UUID
    tier_name: str
    price_naira: int
    status: str  # "active", "past_due", "cancelled"
    started_at: datetime
    expires_at: datetime
    api_requests_used: int
    api_requests_limit: int
    exports_used: int
    exports_limit: int
    days_until_renewal: int

    class Config:
        from_attributes = True


class PaymentHistoryItem(BaseModel):
    """Payment transaction record"""

    id: uuid.UUID
    amount_naira: Decimal
    status: str
    invoice_number: str | None
    created_at: datetime
    completed_at: datetime | None

    class Config:
        from_attributes = True


class BillingDashboardResponse(BaseModel):
    """Complete billing dashboard"""

    subscription: SubscriptionStatus | None
    payment_history: list[PaymentHistoryItem]
    next_payment_date: datetime | None
    total_paid_naira: Decimal


class UpgradeDowngradeRequest(BaseModel):
    """Request to change subscription tier"""

    new_tier_name: Literal["free", "professional", "enterprise"]
    effective_date: Literal["immediately", "next_billing_period"] = "next_billing_period"


class CancelSubscriptionRequest(BaseModel):
    """Request to cancel subscription"""

    reason: str | None = Field(default=None, max_length=500)
    feedback: str | None = Field(default=None, max_length=1000)


class SubscriptionCancelledResponse(BaseModel):
    """Response after subscription cancellation"""

    cancelled_at: datetime
    data_retention_until: datetime
    refund_status: str | None
    message: str


class DecisionPacketRequest(BaseModel):
    """Request to generate a Decision Packet PDF"""

    state_ids: list[uuid.UUID] | None = None  # None = all states
    include_historical_data: bool = False
    period_start: str | None = None  # "2024-01" format
    period_end: str | None = None  # "2024-09" format
    document_title: str | None = Field(default=None, max_length=200)


class DecisionPacketResponse(BaseModel):
    """Response with Decision Packet download link"""

    packet_id: uuid.UUID
    download_url: str
    size_bytes: int
    generated_at: datetime
    expires_at: datetime


class ApiKeyCreateRequest(BaseModel):
    """Request to create API key"""

    name: str = Field(min_length=2, max_length=120)


class ApiKeyCreated(BaseModel):
    """Response with new API key (shown only once)"""

    id: uuid.UUID
    name: str
    key_prefix: str  # First 8 chars: "gaia_sk_xxxxxxxx"
    api_key: str  # Full key shown only once
    created_at: datetime


class ApiKeyItem(BaseModel):
    """List item for existing API key"""

    id: uuid.UUID
    name: str
    key_prefix: str
    last_used_at: datetime | None
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


class ApiKeyRevokeRequest(BaseModel):
    """Request to revoke API key"""

    api_key_id: uuid.UUID


class ApiUsageMetrics(BaseModel):
    """API usage metrics"""

    current_month_requests: int
    current_month_limit: int
    requests_remaining: int
    reset_date: datetime
    current_month_exports: int
    current_month_export_limit: int
    exports_remaining: int
