from __future__ import annotations

import logging
import smtplib
import uuid
from datetime import UTC, datetime
from email.message import EmailMessage
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.api.v1.routes.review import require_admin
from gaiafaac_api.commercial_schemas import (
    CommercialAnalytics,
    PilotLeadAccepted,
    PilotLeadAdminItem,
    PilotLeadCreate,
    PilotLeadUpdate,
)
from gaiafaac_api.config import get_settings
from gaiafaac_api.database.commercial_models import PilotLead
from gaiafaac_api.database.models import Organization
from gaiafaac_api.database.session import get_session
from gaiafaac_api.services.commercial_events import commercial_analytics, record_commercial_event

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
        # Do not persist IP address, user agent, device identifiers, or fingerprints.
        ip_address=None,
        user_agent=None,
        status_changed_at=datetime.now(UTC),
    )
    session.add(lead)
    session.flush()
    record_commercial_event(
        session,
        event_name="pilot_lead_submitted",
        subject_type="pilot_lead",
        subject_id=str(lead.id),
        metadata={"plan_interest": lead.plan_interest, "source": lead.source},
        commit=False,
    )
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


@router.patch(
    "/pilot-leads/{lead_id}",
    response_model=PilotLeadAdminItem,
    summary="Advance a commercial lead through the authorized CRM workflow",
    dependencies=[Depends(require_admin)],
)
def update_pilot_lead(
    lead_id: uuid.UUID,
    payload: PilotLeadUpdate,
    session: DatabaseSession,
) -> PilotLead:
    lead = session.get(PilotLead, lead_id)
    if lead is None:
        raise HTTPException(status_code=404, detail="Pilot lead not found.")

    changes = payload.model_dump(exclude_unset=True)
    if "converted_organization_id" in changes and changes["converted_organization_id"] is not None:
        if session.get(Organization, changes["converted_organization_id"]) is None:
            raise HTTPException(status_code=422, detail="Converted organization does not exist.")

    previous_status = lead.status
    for field, value in changes.items():
        setattr(lead, field, value)
    if "status" in changes and changes["status"] != previous_status:
        lead.status_changed_at = datetime.now(UTC)

    record_commercial_event(
        session,
        event_name="pilot_lead_stage_changed" if lead.status != previous_status else "pilot_lead_updated",
        organization_id=lead.converted_organization_id,
        subject_type="pilot_lead",
        subject_id=str(lead.id),
        metadata={
            "from_status": previous_status,
            "to_status": lead.status,
            "plan_interest": lead.plan_interest,
        },
        commit=False,
    )
    session.commit()
    session.refresh(lead)
    return lead


@router.get(
    "/analytics",
    response_model=CommercialAnalytics,
    summary="Get factual commercial analytics (admin only)",
    dependencies=[Depends(require_admin)],
)
def get_commercial_analytics(session: DatabaseSession) -> dict:
    return commercial_analytics(session)
