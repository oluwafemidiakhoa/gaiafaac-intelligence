from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

logger = logging.getLogger(__name__)


def send_national_review_alert(
    settings,
    *,
    reporting_label: str,
    run_id: str,
    finding_count: int,
    blocking_finding_count: int,
    queue_url: str,
) -> bool:
    """Email a national-review alert. Notification failure never breaks collection."""
    if not all(
        [
            settings.smtp_host,
            settings.smtp_username,
            settings.smtp_password,
            settings.alert_from,
            settings.alert_to,
        ]
    ):
        logger.info("SMTP not configured; skipping national alert for %s", reporting_label)
        return False

    message = EmailMessage()
    message["Subject"] = f"National FAAC evidence ready for review - {reporting_label}"
    message["From"] = settings.alert_from
    message["To"] = settings.alert_to
    message.set_content(
        f"{reporting_label}\n\n"
        f"Run: {run_id}\n"
        f"Validation findings: {finding_count}\n"
        f"Blocking findings: {blocking_finding_count}\n"
        "Status: requires_review (nothing is published automatically)\n\n"
        f"Review: {queue_url}\n"
    )
    try:
        with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port) as server:
            server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(message)
        return True
    except Exception as error:  # noqa: BLE001 - email is non-critical
        logger.warning("National review alert failed for %s: %s", reporting_label, error)
        return False
