"""Utilities for billing and usage limit checks"""

import uuid

from fastapi import HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.subscription_models import (
    OrganizationSubscription,
    SubscriptionTier,
)
from gaiafaac_api.services.billing import BillingService


async def check_usage_limits(request: Request, session: Session) -> None:
    """Verify organization has not exceeded usage limits"""
    organization_id_str = request.headers.get("X-Organization-ID")
    if not organization_id_str:
        return

    try:
        organization_id = uuid.UUID(organization_id_str)
    except ValueError:
        return

    subscription = session.scalar(
        select(OrganizationSubscription).where(
            OrganizationSubscription.organization_id == organization_id
        )
    )

    if not subscription or subscription.status != "active":
        return

    tier = session.scalar(
        select(SubscriptionTier).where(SubscriptionTier.id == subscription.tier_id)
    )
    if not tier:
        return

    billing_service = BillingService(session)
    usage = billing_service.check_usage_limits(organization_id, subscription, tier)

    if usage["api_calls"]["exceeded"]:
        api_used = usage["api_calls"]["used"]
        api_limit = usage["api_calls"]["limit"]
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"API request limit exceeded. Used {api_used}/{api_limit}. "
            f"Upgrade your plan or wait until the next billing period.",
        )

    if usage["exports"]["exceeded"]:
        exports_used = usage["exports"]["used"]
        exports_limit = usage["exports"]["limit"]
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Export limit exceeded. Used {exports_used}/{exports_limit}. "
            f"Upgrade your plan or wait until the next billing period.",
        )
