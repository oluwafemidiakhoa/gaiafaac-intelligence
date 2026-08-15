from __future__ import annotations

import csv
import io
import smtplib
import uuid
from datetime import UTC, date, datetime
from email.message import EmailMessage

from fastapi import APIRouter, HTTPException, Response, status
from openpyxl import Workbook
from sqlalchemy import select

from gaiafaac_api.account_schemas import (
    AccountProfile,
    ApiKeyCreateRequest,
    ApiKeyCreated,
    ApiKeyItem,
    InviteAcceptedRequest,
    InviteItem,
    InviteRequest,
    LoginRequest,
    MemberItem,
    RegisterRequest,
    SessionResponse,
)
from gaiafaac_api.config import get_settings
from gaiafaac_api.customer_auth import CurrentCustomer, DatabaseSession
from gaiafaac_api.database.customer_models import OrganizationInvite, OrganizationMembership
from gaiafaac_api.database.enums import UserRole
from gaiafaac_api.database.models import ApiKey, Organization, ReportingPeriod, User
from gaiafaac_api.services.account import (
    create_invite,
    current_plan,
    invite_by_token,
    membership_for,
    normalized_email,
    organization_for_user,
    organization_member_count,
    organization_slug,
)
from gaiafaac_api.services.api_keys import generate_api_key
from gaiafaac_api.services.customer_sessions import (
    create_customer_session,
    revoke_customer_session,
)
from gaiafaac_api.services.passwords import hash_password, verify_password
from gaiafaac_api.services.published_data import get_published_overview

router = APIRouter(prefix="/account", tags=["customer account"])


def _profile(session: DatabaseSession, user: User) -> AccountProfile:
    organization = organization_for_user(session, user)
    membership = membership_for(session, user)
    if organization is None or membership is None:
        raise HTTPException(status_code=409, detail="Customer organization is not configured.")
    plan_code, entitlements, subscription = current_plan(session, organization.id)
    return AccountProfile(
        user_id=user.id,
        full_name=user.full_name,
        email=user.email,
        organization_id=organization.id,
        organization_name=organization.name,
        membership_role=membership.role,
        plan_code=plan_code,
        subscription_status=subscription.status.value if subscription is not None else None,
        historical_access=entitlements.historical_access,
        downloads=entitlements.downloads,
        api_access=entitlements.api_access,
        max_users=entitlements.max_users,
    )


def _require_org_admin(session: DatabaseSession, user: User) -> OrganizationMembership:
    membership = membership_for(session, user)
    if membership is None or membership.role not in {"owner", "admin"}:
        raise HTTPException(status_code=403, detail="Organization administrator access required.")
    return membership


def _require_entitlement(session: DatabaseSession, user: User, attribute: str):
    if user.organization_id is None:
        raise HTTPException(status_code=403, detail="No customer organization is attached.")
    _code, entitlements, _subscription = current_plan(session, user.organization_id)
    if not getattr(entitlements, attribute):
        raise HTTPException(status_code=403, detail="Your current plan does not include this feature.")
    return entitlements


@router.post("/register", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, session: DatabaseSession) -> SessionResponse:
    email = normalized_email(payload.email)
    if session.scalar(select(User).where(User.email == email)) is not None:
        raise HTTPException(status_code=409, detail="An account already exists for this email.")

    organization = Organization(
        name=payload.organization_name.strip(),
        slug=organization_slug(payload.organization_name),
    )
    session.add(organization)
    session.flush()
    try:
        password_hash = hash_password(payload.password)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    user = User(
        organization_id=organization.id,
        email=email,
        full_name=payload.full_name.strip(),
        role=UserRole.VIEWER,
        password_hash=password_hash,
        is_active=True,
    )
    session.add(user)
    session.flush()
    session.add(
        OrganizationMembership(
            organization_id=organization.id,
            user_id=user.id,
            role="owner",
        )
    )
    session.commit()
    row, raw = create_customer_session(session, user)
    return SessionResponse(token=raw, expires_at=row.expires_at)


@router.post("/login", response_model=SessionResponse)
def login(payload: LoginRequest, session: DatabaseSession) -> SessionResponse:
    user = session.scalar(select(User).where(User.email == normalized_email(payload.email)))
    if user is None or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    membership = membership_for(session, user)
    if membership is None:
        raise HTTPException(status_code=403, detail="This account is not a customer account.")
    row, raw = create_customer_session(session, user)
    return SessionResponse(token=raw, expires_at=row.expires_at)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    session: DatabaseSession,
    authorization: str | None = None,
) -> Response:
    # The web tier also clears its HttpOnly cookie. Revocation is best effort here.
    if authorization:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() == "bearer" and token:
            revoke_customer_session(session, token.strip())
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=AccountProfile)
def me(session: DatabaseSession, user: CurrentCustomer) -> AccountProfile:
    return _profile(session, user)


@router.get("/team/members", response_model=list[MemberItem])
def team_members(session: DatabaseSession, user: CurrentCustomer) -> list[MemberItem]:
    _require_org_admin(session, user)
    if user.organization_id is None:
        return []
    rows = session.execute(
        select(OrganizationMembership, User)
        .join(User, User.id == OrganizationMembership.user_id)
        .where(OrganizationMembership.organization_id == user.organization_id)
        .order_by(User.full_name)
    ).all()
    return [
        MemberItem(user_id=member.id, full_name=member.full_name, email=member.email, role=membership.role)
        for membership, member in rows
    ]


@router.get("/team/invites", response_model=list[InviteItem])
def team_invites(session: DatabaseSession, user: CurrentCustomer) -> list[InviteItem]:
    _require_org_admin(session, user)
    if user.organization_id is None:
        return []
    rows = session.scalars(
        select(OrganizationInvite)
        .where(
            OrganizationInvite.organization_id == user.organization_id,
            OrganizationInvite.accepted_at.is_(None),
            OrganizationInvite.expires_at > datetime.now(UTC),
        )
        .order_by(OrganizationInvite.created_at.desc())
    ).all()
    return [
        InviteItem(id=row.id, email=row.email, full_name=row.full_name, role=row.role, expires_at=row.expires_at)
        for row in rows
    ]


@router.post("/team/invites", response_model=InviteItem, status_code=status.HTTP_201_CREATED)
def invite_member(
    payload: InviteRequest,
    session: DatabaseSession,
    user: CurrentCustomer,
) -> InviteItem:
    _require_org_admin(session, user)
    if user.organization_id is None:
        raise HTTPException(status_code=409, detail="Organization is not configured.")
    _plan, entitlements, _subscription = current_plan(session, user.organization_id)
    if entitlements.max_users <= 1:
        raise HTTPException(status_code=403, detail="Upgrade to a team-capable plan to invite members.")

    email = normalized_email(payload.email)
    existing = session.scalar(
        select(User).where(User.email == email, User.organization_id == user.organization_id)
    )
    if existing is not None:
        raise HTTPException(status_code=409, detail="This person is already a member.")
    live_invites = session.scalars(
        select(OrganizationInvite).where(
            OrganizationInvite.organization_id == user.organization_id,
            OrganizationInvite.accepted_at.is_(None),
            OrganizationInvite.expires_at > datetime.now(UTC),
        )
    ).all()
    if organization_member_count(session, user.organization_id) + len(live_invites) >= entitlements.max_users:
        raise HTTPException(status_code=409, detail="Your plan's member limit has been reached.")

    settings = get_settings()
    if not all(
        [settings.smtp_host, settings.smtp_username, settings.smtp_password, settings.alert_from]
    ):
        raise HTTPException(status_code=503, detail="Customer invitation email is not configured.")

    invite, raw = create_invite(
        session,
        organization_id=user.organization_id,
        invited_by_user_id=user.id,
        email=email,
        full_name=payload.full_name,
        role=payload.role,
    )
    organization = session.get(Organization, user.organization_id)
    invite_url = f"{settings.customer_app_url.rstrip('/')}/account/accept-invite?token={raw}"
    message = EmailMessage()
    message["Subject"] = f"You're invited to {organization.name if organization else 'GaiaFAAC'}"
    message["From"] = settings.alert_from
    message["To"] = email
    message.set_content(
        f"{user.full_name} invited you to a GaiaFAAC organization.\n\n"
        f"Accept the invitation: {invite_url}\n\n"
        "This link expires in 7 days."
    )
    try:
        with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port) as server:
            server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(message)
    except Exception as error:  # noqa: BLE001
        session.delete(invite)
        session.commit()
        raise HTTPException(status_code=502, detail="Invitation email could not be sent.") from error

    return InviteItem(
        id=invite.id,
        email=invite.email,
        full_name=invite.full_name,
        role=invite.role,
        expires_at=invite.expires_at,
    )


@router.post("/team/accept-invite", response_model=SessionResponse)
def accept_invite(payload: InviteAcceptedRequest, session: DatabaseSession) -> SessionResponse:
    invite = invite_by_token(session, payload.token)
    if invite is None:
        raise HTTPException(status_code=404, detail="Invitation is invalid or expired.")
    user = session.scalar(select(User).where(User.email == invite.email))
    if user is None:
        try:
            password_hash = hash_password(payload.password)
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        user = User(
            organization_id=invite.organization_id,
            email=invite.email,
            full_name=payload.full_name.strip(),
            role=UserRole.VIEWER,
            password_hash=password_hash,
            is_active=True,
        )
        session.add(user)
        session.flush()
    else:
        if not verify_password(payload.password, user.password_hash):
            raise HTTPException(
                status_code=409,
                detail="This email already has an account. Enter its current password to accept the invitation.",
            )
        if user.organization_id not in {None, invite.organization_id}:
            raise HTTPException(status_code=409, detail="This account already belongs to another organization.")
        user.organization_id = invite.organization_id
        user.full_name = payload.full_name.strip()

    membership = session.scalar(
        select(OrganizationMembership).where(
            OrganizationMembership.organization_id == invite.organization_id,
            OrganizationMembership.user_id == user.id,
        )
    )
    if membership is None:
        session.add(
            OrganizationMembership(
                organization_id=invite.organization_id,
                user_id=user.id,
                role=invite.role,
            )
        )
    invite.accepted_at = datetime.now(UTC)
    session.commit()
    row, raw = create_customer_session(session, user)
    return SessionResponse(token=raw, expires_at=row.expires_at)


@router.delete("/team/members/{member_user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(
    member_user_id: uuid.UUID,
    session: DatabaseSession,
    user: CurrentCustomer,
) -> Response:
    _require_org_admin(session, user)
    if user.organization_id is None or member_user_id == user.id:
        raise HTTPException(status_code=409, detail="You cannot remove this member.")
    membership = session.scalar(
        select(OrganizationMembership).where(
            OrganizationMembership.organization_id == user.organization_id,
            OrganizationMembership.user_id == member_user_id,
        )
    )
    if membership is None:
        raise HTTPException(status_code=404, detail="Member not found.")
    if membership.role == "owner":
        raise HTTPException(status_code=409, detail="The organization owner cannot be removed.")
    member = session.get(User, member_user_id)
    session.delete(membership)
    if member is not None:
        member.organization_id = None
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/api-keys", response_model=list[ApiKeyItem])
def list_api_keys(session: DatabaseSession, user: CurrentCustomer) -> list[ApiKeyItem]:
    _require_entitlement(session, user, "api_access")
    if user.organization_id is None:
        return []
    rows = session.scalars(
        select(ApiKey)
        .where(ApiKey.organization_id == user.organization_id)
        .order_by(ApiKey.created_at.desc())
    ).all()
    return [
        ApiKeyItem(
            id=row.id,
            name=row.name,
            key_prefix=row.key_prefix,
            last_used_at=row.last_used_at,
            revoked_at=row.revoked_at,
        )
        for row in rows
    ]


@router.post("/api-keys", response_model=ApiKeyCreated, status_code=status.HTTP_201_CREATED)
def create_api_key(
    payload: ApiKeyCreateRequest,
    session: DatabaseSession,
    user: CurrentCustomer,
) -> ApiKeyCreated:
    _require_org_admin(session, user)
    _require_entitlement(session, user, "api_access")
    if user.organization_id is None:
        raise HTTPException(status_code=409, detail="Organization is not configured.")
    key, raw = generate_api_key(
        session,
        organization_id=user.organization_id,
        name=payload.name.strip(),
        plan_code="api",
    )
    session.commit()
    return ApiKeyCreated(id=key.id, name=key.name, key_prefix=key.key_prefix, api_key=raw)


@router.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_api_key(
    key_id: uuid.UUID,
    session: DatabaseSession,
    user: CurrentCustomer,
) -> Response:
    _require_org_admin(session, user)
    if user.organization_id is None:
        raise HTTPException(status_code=404, detail="API key not found.")
    key = session.scalar(
        select(ApiKey).where(ApiKey.id == key_id, ApiKey.organization_id == user.organization_id)
    )
    if key is None:
        raise HTTPException(status_code=404, detail="API key not found.")
    key.revoked_at = datetime.now(UTC)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _published_month(session: DatabaseSession, month: date):
    period = session.scalar(
        select(ReportingPeriod).where(
            ReportingPeriod.revenue_month == month,
            ReportingPeriod.is_published.is_(True),
            ReportingPeriod.is_demo.is_(False),
        )
    )
    overview = get_published_overview(session, period) if period is not None else None
    if overview is None:
        raise HTTPException(status_code=404, detail="No published month for that date.")
    return overview


@router.get("/exports/allocations.csv")
def export_allocations_csv(
    month: date,
    session: DatabaseSession,
    user: CurrentCustomer,
) -> Response:
    _require_entitlement(session, user, "downloads")
    overview = _published_month(session, month)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "revenue_month",
            "state_name",
            "state_code",
            "gross_total",
            "total_deductions",
            "net_allocation",
            "reported_unit",
            "source_organization",
            "source_sha256",
        ]
    )
    for allocation in overview.allocations:
        writer.writerow(
            [
                overview.period.revenue_month.isoformat(),
                allocation.state_name,
                allocation.state_code,
                allocation.gross_total or "",
                allocation.total_deductions or "",
                allocation.net_allocation or "",
                allocation.reported_unit,
                overview.source.source_organization,
                overview.source.sha256,
            ]
        )
    filename = f"gaiafaac-{month.isoformat()}-allocations.csv"
    return Response(
        content=output.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/exports/allocations.xlsx")
def export_allocations_xlsx(
    month: date,
    session: DatabaseSession,
    user: CurrentCustomer,
) -> Response:
    _require_entitlement(session, user, "downloads")
    overview = _published_month(session, month)
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Allocations"
    sheet.append(
        [
            "Revenue month",
            "State",
            "Code",
            "Gross total",
            "Total deductions",
            "Net allocation",
            "Reported unit",
            "Source organization",
            "Source SHA-256",
        ]
    )
    for allocation in overview.allocations:
        sheet.append(
            [
                overview.period.revenue_month.isoformat(),
                allocation.state_name,
                allocation.state_code,
                allocation.gross_total,
                allocation.total_deductions,
                allocation.net_allocation,
                allocation.reported_unit,
                overview.source.source_organization,
                overview.source.sha256,
            ]
        )
    source = workbook.create_sheet("Source")
    source.append(["Reporting label", overview.period.reporting_label])
    source.append(["Organization", overview.source.source_organization])
    source.append(["Original filename", overview.source.original_filename])
    source.append(["SHA-256", overview.source.sha256])
    source.append(["Source URL", overview.source.source_url or ""])
    buffer = io.BytesIO()
    workbook.save(buffer)
    filename = f"gaiafaac-{month.isoformat()}-allocations.xlsx"
    return Response(
        content=buffer.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
