from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from gaiafaac_api.config import Settings
from gaiafaac_api.database.commercial_models import PilotLead

logger = logging.getLogger(__name__)


def send_pilot_lead_alert(settings: Settings, *, lead: PilotLead) -> bool:
    """Email an alert that a commercial pilot lead was submitted. Never raises."""
    if not all(
        [
            settings.smtp_host,
            settings.smtp_username,
            settings.smtp_password,
            settings.alert_from,
            settings.alert_to,
        ]
    ):
        logger.info("SMTP not configured; skipping pilot lead alert for %s", lead.email)
        return False

    admin_url = f"{settings.customer_app_url.rstrip('/')}/admin/leads"
    expected_users = lead.expected_users if lead.expected_users is not None else "(not given)"
    message = EmailMessage()
    message["Subject"] = f"New pilot lead — {lead.organization or lead.name} ({lead.plan_interest})"
    message["From"] = settings.alert_from
    message["To"] = settings.alert_to
    message.set_content(
        f"Name: {lead.name}\n"
        f"Email: {lead.email}\n"
        f"Organization: {lead.organization or '(not given)'}\n"
        f"Role: {lead.role or '(not given)'}\n"
        f"Country: {lead.country or '(not given)'}\n"
        f"Plan interest: {lead.plan_interest}\n"
        f"Expected users: {expected_users}\n"
        f"Preferred format: {lead.preferred_format or '(not given)'}\n"
        f"States/periods: {lead.states_or_periods or '(not given)'}\n\n"
        f"Use case:\n{lead.use_case}\n\n"
        f"Review all leads: {admin_url}\n"
    )
    try:
        with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port) as server:
            server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(message)
        return True
    except Exception as error:  # noqa: BLE001 - a failed email must not break lead capture
        logger.warning("Pilot lead alert email failed for %s: %s", lead.email, error)
        return False
