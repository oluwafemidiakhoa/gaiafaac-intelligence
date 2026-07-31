from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

logger = logging.getLogger(__name__)


def send_review_alert(
    settings,
    *,
    reporting_label: str,
    records_extracted: int,
    blocking_finding_count: int,
    queue_url: str,
) -> bool:
    """Email an alert that a month is queued for review. Never raises."""
    if not all(
        [
            settings.smtp_host,
            settings.smtp_username,
            settings.smtp_password,
            settings.alert_from,
            settings.alert_to,
        ]
    ):
        logger.info("SMTP not configured; skipping alert for %s", reporting_label)
        return False

    message = EmailMessage()
    message["Subject"] = f"New OAGF month ready for review — {reporting_label}"
    message["From"] = settings.alert_from
    message["To"] = settings.alert_to
    message.set_content(
        f"{reporting_label}\n\n"
        f"Records extracted: {records_extracted}\n"
        f"Blocking findings: {blocking_finding_count}\n"
        f"Status: requires_review (nothing is published automatically)\n\n"
        f"Review and approve: {queue_url}\n"
    )
    try:
        with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port) as server:
            server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(message)
        return True
    except Exception as error:  # noqa: BLE001 - a failed email must not break collection
        logger.warning("Review alert email failed for %s: %s", reporting_label, error)
        return False
