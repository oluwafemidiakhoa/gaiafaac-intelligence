from __future__ import annotations

import uuid
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
from gaiafaac_api.services.commercial_notify import send_pilot_lead_alert

router = APIRouter(prefix="/commercial", tags=["commercial"])
DatabaseSession = Annotated[Session, Depends(get_session)]


@router.post(
    "/pilot-leads",
    response_model=PilotLeadAccepted,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Request a GaiaFAAC commercial pilot",
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
    send_pilot_lead_alert(get_settings(), lead=lead)
    return PilotLeadAccepted(id=lead.id)


@router.get(
    "/pilot-leads",
    response_model=list[PilotLeadAdminItem],
    summary="List commercial pilot leads (admin only)",
    dependencies=[Depends(require_admin)],
)
def list_pilot_leads(session: DatabaseSession) -> list[PilotLead]:
    return list(session.scalars(select(PilotLead).order_by(PilotLead.created_at.desc())))
