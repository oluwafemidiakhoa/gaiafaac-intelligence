from __future__ import annotations

import logging
import smtplib
import uuid
from email.message import EmailMessage
from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.api.v1.routes.review import require_admin
from gaiafaac_api.commercial_schemas import (
    PilotLeadAccepted,
    PilotLeadAdminItem,
    PilotLeadCreate,
)
from gaiafaac_api.config import get_settings
from gaiafaac_api.database.commercial_models import PilotLead
from gaiafaac_api.database.session import get_session

router = APIRouter(prefix="/commercial", tags=["commercial"])
DatabaseSession = Annotated[Session, Depends(get_session)]
logger = logging.getLogger(__name__)


def _notify_pilot_lead(lead: PilotLead) -> None:
    """Notify the internal team without making lead capture depend on SMTP."""
    settings = get_settings()
    if not all(
        [
            settings.smtp_host,
            settings.smtp_username,
            settings.smtp_password,
            settings.alert_from,
            settings.alert_to,
        ]
    ):
        logger.info("SMTP or ALERT_TO is incomplete; pilot lead notification skipped.")
        return

    message = EmailMessage()
    message["Subject"] = f"New Gaia Fiscal Watch request — {lead.organization or lead.name}"
    message["From"] = settings.alert_from
    message["To"] = settings.alert_to
    message.set_content(
        f"A new Fiscal Watch request was received.\n\n"
        f"Name: {lead.name}\n"
        f"Email: {lead.email}\n"
        f"Organization: {lead.organization or 'Not provided'}\n"
        f"Role: {lead.role or 'Not provided'}\n"
        f"Expected users: {lead.expected_users or 'Not provided'}\n"
        f"Jurisdictions / periods: {lead.states_or_periods or 'Not provided'}\n\n"
        f"Use case:\n{lead.use_case}\n\n"
        "Review the lead in Gaia Fiscal Intelligence before activating a customer workspace.\n"
    )
    try:
        with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port) as server:
            server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(message)
    except Exception as error:  # noqa: BLE001 - the stored lead remains the source of truth
        logger.warning("Pilot lead notification email failed: %s", error)


@router.post(
    "/pilot-leads",
    response_model=PilotLeadAccepted,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Request a Gaia Fiscal Intelligence commercial pilot",
)
def create_pilot_lead(
    payload: PilotLeadCreate,
    request: Request,
    session: DatabaseSession,
) -> PilotLeadAccepted:
    # Hidden honeypot field. Bots receive the same response but are not stored.
    if payload.website:
        return PilotLeadAccepted(id=uuid.uuid4())

    lead = PilotLead(
        name=payload.name,
        email=payload.email,
        organization=payload.organization or None,
        role=payload.role or None,
        country=payload.country or None,
        plan_interest=payload.plan_interest,
        use_case=payload.use_case,
        states_or_periods=payload.states_or_periods or None,
        preferred_format=payload.preferred_format or None,
        expected_users=payload.expected_users,
        source="website",
        ip_address=request.client.host if request.client else None,
        user_agent=(request.headers.get("user-agent") or "")[:500] or None,
    )
    session.add(lead)
    session.commit()
    session.refresh(lead)
    _notify_pilot_lead(lead)
    return PilotLeadAccepted(id=lead.id)


@router.get(
    "/pilot-leads",
    response_model=list[PilotLeadAdminItem],
    summary="List commercial pilot leads (admin only)",
    dependencies=[Depends(require_admin)],
)
def list_pilot_leads(session: DatabaseSession) -> list[PilotLead]:
    return list(session.scalars(select(PilotLead).order_by(PilotLead.created_at.desc())))
