from __future__ import annotations

import hashlib
import re
import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from gaiafaac_api.database.customer_models import OrganizationInvite, OrganizationMembership
from gaiafaac_api.database.enums import PlanCode, SubscriptionStatus
from gaiafaac_api.database.models import Organization, Subscription, User
from gaiafaac_api.entitlements import Entitlements, entitlements_for

_ACTIVE_SUBSCRIPTION_STATUSES = {
    SubscriptionStatus.ACTIVE,
    SubscriptionStatus.TRIALING,
}


def normalized_email(value: str) -> str:
    return value.strip().lower()


def organization_slug(value: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-") or "organization"
    return f"{base[:72]}-{secrets.token_hex(3)}"


def active_subscription(session: Session, organization_id) -> Subscription | None:
    return session.scalar(
        select(Subscription)
        .where(
            Subscription.organization_id == organization_id,
            Subscription.status.in_(_ACTIVE_SUBSCRIPTION_STATUSES),
        )
        .order_by(Subscription.updated_at.desc())
    )


def current_plan(
    session: Session, organization_id
) -> tuple[str, Entitlements, Subscription | None]:
    subscription = active_subscription(session, organization_id)
    code = subscription.plan_code if subscription is not None else PlanCode.FREE.value
    return code, entitlements_for(code), subscription


def membership_for(session: Session, user: User) -> OrganizationMembership | None:
    if user.organization_id is None:
        return None
    return session.scalar(
        select(OrganizationMembership).where(
            OrganizationMembership.organization_id == user.organization_id,
            OrganizationMembership.user_id == user.id,
        )
    )


def organization_member_count(session: Session, organization_id) -> int:
    return (
        session.scalar(
            select(func.count())
            .select_from(OrganizationMembership)
            .where(OrganizationMembership.organization_id == organization_id)
        )
        or 0
    )


def create_invite(
    session: Session,
    *,
    organization_id,
    invited_by_user_id,
    email: str,
    full_name: str | None,
    role: str,
) -> tuple[OrganizationInvite, str]:
    raw = "gfi_" + secrets.token_urlsafe(36)
    row = OrganizationInvite(
        organization_id=organization_id,
        invited_by_user_id=invited_by_user_id,
        email=normalized_email(email),
        full_name=full_name.strip() if full_name else None,
        role=role,
        token_hash=hashlib.sha256(raw.encode("utf-8")).hexdigest(),
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row, raw


def invite_by_token(session: Session, raw: str) -> OrganizationInvite | None:
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    invite = session.scalar(
        select(OrganizationInvite).where(OrganizationInvite.token_hash == digest)
    )
    if invite is None or invite.accepted_at is not None or invite.expires_at <= datetime.now(UTC):
        return None
    return invite


def organization_for_user(session: Session, user: User) -> Organization | None:
    return session.get(Organization, user.organization_id) if user.organization_id else None
