from __future__ import annotations

import logging
import smtplib
from dataclasses import dataclass
from datetime import UTC, datetime
from email.message import EmailMessage

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.config import Settings
from gaiafaac_api.database.customer_models import (
    CustomerAlert,
    CustomerAlertDelivery,
    CustomerNotificationPreference,
)
from gaiafaac_api.database.models import State, User
from gaiafaac_api.services.watchlists import sync_watchlist_alerts
from gaiafaac_api.watchlist_schemas import (
    NotificationPreferenceResponse,
    NotificationPreferenceUpdate,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DeliveryRunSummary:
    users_checked: int = 0
    alerts_eligible: int = 0
    sent: int = 0
    failed: int = 0
    deferred: int = 0
    skipped_sent: int = 0


def _smtp_ready(settings: Settings) -> bool:
    return bool(
        settings.smtp_host
        and settings.smtp_username
        and settings.smtp_password
        and settings.alert_from
    )


def delivery_available(settings: Settings) -> bool:
    return settings.customer_alert_email_enabled and _smtp_ready(settings)


def get_notification_preference(
    session: Session, user: User, settings: Settings
) -> NotificationPreferenceResponse:
    preference = session.get(CustomerNotificationPreference, user.id)
    return NotificationPreferenceResponse(
        email_enabled=preference.email_enabled if preference is not None else False,
        include_fiscal_watch=(preference.include_fiscal_watch if preference is not None else True),
        include_fiscal_events=(
            preference.include_fiscal_events if preference is not None else True
        ),
        email_enabled_at=preference.email_enabled_at if preference is not None else None,
        delivery_available=delivery_available(settings),
        delivery_note=(
            "Customer alert email delivery is available. Enabling email opts this account into "
            "outbound messages for the selected governed alert classes."
            if delivery_available(settings)
            else "Customer alert email delivery is currently disabled by the operator or SMTP "
            "is not fully configured. Inbox alerts remain available."
        ),
    )


def update_notification_preference(
    session: Session,
    user: User,
    payload: NotificationPreferenceUpdate,
    settings: Settings,
) -> NotificationPreferenceResponse:
    preference = session.get(CustomerNotificationPreference, user.id)
    now = datetime.now(UTC)
    if preference is None:
        preference = CustomerNotificationPreference(user_id=user.id)
        session.add(preference)

    previously_enabled = preference.email_enabled
    preference.email_enabled = payload.email_enabled
    preference.include_fiscal_watch = payload.include_fiscal_watch
    preference.include_fiscal_events = payload.include_fiscal_events
    if payload.email_enabled and not previously_enabled:
        preference.email_enabled_at = now
    elif not payload.email_enabled:
        preference.email_enabled_at = None
    session.commit()
    session.refresh(preference)
    return get_notification_preference(session, user, settings)


def _eligible(preference: CustomerNotificationPreference, alert: CustomerAlert) -> bool:
    if alert.source_kind == "fiscal_watch":
        return preference.include_fiscal_watch
    if alert.source_kind == "fiscal_event":
        return preference.include_fiscal_events
    return False


def _email_message(
    settings: Settings,
    *,
    user: User,
    state: State,
    alert: CustomerAlert,
) -> EmailMessage:
    payload = alert.payload if isinstance(alert.payload, dict) else {}
    headline = str(payload.get("headline") or alert.event_type.replace("_", " "))
    detail = str(payload.get("detail") or "Recorded governed fiscal event.")
    link_path = str(payload.get("link_path") or "/watchlist")
    app_url = settings.customer_app_url.rstrip("/")
    evidence_ids = payload.get("evidence_ids")
    evidence_line = ""
    if isinstance(evidence_ids, list) and evidence_ids:
        evidence_line = f"Evidence IDs: {' · '.join(str(item) for item in evidence_ids)}\n"

    message = EmailMessage()
    message["Subject"] = f"Gaia alert — {state.name}: {headline}"
    message["From"] = settings.alert_from
    message["To"] = user.email
    message.set_content(
        f"{headline}\n\n"
        f"Jurisdiction: {state.name} ({state.code})\n"
        f"Event type: {alert.event_type}\n"
        f"Severity: {alert.severity}\n"
        f"Occurred: {alert.occurred_at}\n\n"
        f"{detail}\n\n"
        f"{evidence_line}"
        f"Inspect in Gaia: {app_url}{link_path}\n\n"
        "This notification is derived from GaiaFAAC's governed evidence and deterministic "
        "event rules. It is not a credit rating, solvency assessment, corruption indicator, "
        "or prediction.\n"
    )
    return message


def _send_email(settings: Settings, message: EmailMessage) -> tuple[bool, str | None]:
    try:
        with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port) as server:
            server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(message)
        return True, None
    except Exception as error:  # noqa: BLE001 - delivery failures must remain retryable
        logger.warning("Customer alert email delivery failed: %s", error)
        return False, str(error)[:500]


def deliver_customer_alerts(
    session: Session,
    settings: Settings,
    *,
    year: int,
    max_attempts: int = 5,
) -> DeliveryRunSummary:
    preferences = list(
        session.scalars(
            select(CustomerNotificationPreference).where(
                CustomerNotificationPreference.email_enabled.is_(True)
            )
        )
    )
    sent = failed = deferred = skipped_sent = alerts_eligible = 0
    year_start = datetime(year, 1, 1, tzinfo=UTC)
    year_end = datetime(year + 1, 1, 1, tzinfo=UTC)

    for preference in preferences:
        user = session.get(User, preference.user_id)
        if user is None or not user.is_active:
            continue
        email_cutoff = preference.email_enabled_at
        if email_cutoff is None:
            continue
        sync_watchlist_alerts(session, user, year)
        alerts = list(
            session.scalars(
                select(CustomerAlert)
                .where(
                    CustomerAlert.user_id == user.id,
                    CustomerAlert.occurred_at >= year_start,
                    CustomerAlert.occurred_at < year_end,
                    CustomerAlert.occurred_at >= email_cutoff,
                    CustomerAlert.created_at >= email_cutoff,
                )
                .order_by(CustomerAlert.occurred_at, CustomerAlert.created_at)
            )
        )
        for alert in alerts:
            if not _eligible(preference, alert):
                continue
            alerts_eligible += 1
            delivery = session.scalar(
                select(CustomerAlertDelivery).where(
                    CustomerAlertDelivery.alert_id == alert.id,
                    CustomerAlertDelivery.channel == "email",
                )
            )
            if delivery is None:
                delivery = CustomerAlertDelivery(
                    alert_id=alert.id,
                    user_id=user.id,
                    channel="email",
                    status="pending",
                )
                session.add(delivery)
                session.flush()
            if delivery.status == "sent":
                skipped_sent += 1
                continue
            if delivery.attempt_count >= max_attempts:
                continue

            now = datetime.now(UTC)
            if not delivery_available(settings):
                delivery.status = "deferred"
                delivery.last_error = (
                    "Customer alert email delivery is disabled or SMTP is incomplete."
                )
                delivery.last_attempt_at = now
                deferred += 1
                session.commit()
                continue

            state = session.get(State, alert.state_id)
            if state is None:
                delivery.status = "failed"
                delivery.attempt_count += 1
                delivery.last_attempt_at = now
                delivery.last_error = "Alert jurisdiction lineage is incomplete."
                failed += 1
                session.commit()
                continue

            ok, error = _send_email(
                settings,
                _email_message(settings, user=user, state=state, alert=alert),
            )
            delivery.attempt_count += 1
            delivery.last_attempt_at = now
            delivery.last_error = error
            if ok:
                delivery.status = "sent"
                delivery.delivered_at = now
                sent += 1
            else:
                delivery.status = "failed"
                failed += 1
            session.commit()

    return DeliveryRunSummary(
        users_checked=len(preferences),
        alerts_eligible=alerts_eligible,
        sent=sent,
        failed=failed,
        deferred=deferred,
        skipped_sent=skipped_sent,
    )