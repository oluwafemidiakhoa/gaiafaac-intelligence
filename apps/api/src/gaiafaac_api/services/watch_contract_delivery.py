from __future__ import annotations

import hashlib
import hmac
import logging
import smtplib
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from email.message import EmailMessage

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from gaiafaac_api.config import Settings
from gaiafaac_api.database.customer_models import (
    CustomerNotificationPreference,
    OrganizationAlert,
    OrganizationMembership,
)
from gaiafaac_api.database.models import State, User
from gaiafaac_api.database.watch_contract_models import (
    FiscalWatchContract,
    FiscalWatchContractDelivery,
    FiscalWatchContractDeliveryAttempt,
    FiscalWatchContractMatch,
    FiscalWatchContractReview,
)
from gaiafaac_api.database.webhook_models import OrganizationWebhookEndpoint
from gaiafaac_api.ledger import canonical_json, canonical_sha256, canonicalize
from gaiafaac_api.services.account import current_plan
from gaiafaac_api.services.institutional_webhooks import (
    _post_https,
    derive_signing_secret,
    webhook_delivery_ready,
)

logger = logging.getLogger(__name__)

WATCH_WEBHOOK_SCHEMA_VERSION = "gaia-watch-contract-webhook-v1"
_RETRY_DELAYS = (
    timedelta(minutes=5),
    timedelta(minutes=30),
    timedelta(hours=2),
    timedelta(hours=12),
    timedelta(hours=24),
)


@dataclass(frozen=True)
class WatchDeliveryRunSummary:
    reviews_checked: int = 0
    deliveries_created: int = 0
    delivered: int = 0
    retrying: int = 0
    dead_letter: int = 0
    deferred: int = 0
    failed: int = 0


def _smtp_ready(settings: Settings) -> bool:
    return bool(
        settings.customer_alert_email_enabled
        and settings.smtp_host
        and settings.smtp_username
        and settings.smtp_password
        and settings.alert_from
    )


def _review_rows(session: Session, organization_id: uuid.UUID | None = None):
    statement = (
        select(
            FiscalWatchContractReview,
            FiscalWatchContractMatch,
            FiscalWatchContract,
            OrganizationAlert,
            State,
        )
        .join(
            FiscalWatchContractMatch,
            FiscalWatchContractMatch.id == FiscalWatchContractReview.match_id,
        )
        .join(
            FiscalWatchContract,
            FiscalWatchContract.id == FiscalWatchContractReview.contract_id,
        )
        .join(
            OrganizationAlert,
            OrganizationAlert.id == FiscalWatchContractMatch.organization_alert_id,
        )
        .join(State, State.id == OrganizationAlert.state_id)
    )
    if organization_id is not None:
        statement = statement.where(FiscalWatchContractReview.organization_id == organization_id)
    return session.execute(statement.order_by(FiscalWatchContractReview.created_at)).all()


def _watch_payload(
    delivery_id: uuid.UUID,
    review: FiscalWatchContractReview,
    match: FiscalWatchContractMatch,
    contract: FiscalWatchContract,
    alert: OrganizationAlert,
    state: State,
    settings: Settings,
) -> dict[str, object]:
    alert_payload = alert.payload if isinstance(alert.payload, dict) else {}
    headline = str(alert_payload.get("headline") or alert.event_type.replace("_", " "))
    detail = str(alert_payload.get("detail") or "Recorded governed fiscal event.")
    return canonicalize(
        {
            "id": str(delivery_id),
            "type": "watch_contract_match",
            "created_at": review.created_at,
            "data": {
                "review_id": str(review.id),
                "match_id": str(match.id),
                "contract_id": str(contract.id),
                "contract_name": contract.name,
                "decision_room_id": str(review.room_id),
                "jurisdiction": {
                    "code": f"NG-{state.code.upper()}",
                    "name": state.name,
                },
                "event_type": alert.event_type,
                "severity": str(alert.severity),
                "headline": headline,
                "detail": detail,
                "occurred_at": alert.occurred_at,
                "matched_at": match.matched_at,
                "review_due_at": review.due_at,
                "decision_review_url": (
                    f"{settings.customer_app_url.rstrip('/')}/decision-rooms/{review.room_id}/review"
                ),
            },
            "meta": {
                "schema_version": WATCH_WEBHOOK_SCHEMA_VERSION,
                "meaning": (
                    "A governed event matched an organization Watch Contract and opened an "
                    "operational review. This is not a credit rating, solvency assessment, "
                    "misconduct indicator, or prediction."
                ),
            },
        }
    )


def _email_payload(
    review: FiscalWatchContractReview,
    contract: FiscalWatchContract,
    alert: OrganizationAlert,
    state: State,
    settings: Settings,
) -> dict[str, str]:
    alert_payload = alert.payload if isinstance(alert.payload, dict) else {}
    headline = str(alert_payload.get("headline") or alert.event_type.replace("_", " "))
    detail = str(alert_payload.get("detail") or "Recorded governed fiscal event.")
    review_url = f"{settings.customer_app_url.rstrip('/')}/decision-rooms/{review.room_id}/review"
    subject = f"Gaia Watch — {state.name}: {headline}"
    body = (
        f"{headline}\n\n"
        f"Watch Contract: {contract.name}\n"
        f"Jurisdiction: {state.name} ({state.code})\n"
        f"Event type: {alert.event_type}\n"
        f"Severity: {alert.severity}\n"
        f"Occurred: {alert.occurred_at}\n"
        f"Operational review due: {review.due_at}\n\n"
        f"{detail}\n\n"
        f"Open Decision Review: {review_url}\n\n"
        "This notification records a deterministic match against a governed Watch Contract. "
        "It is not a credit rating, solvency assessment, misconduct indicator, or prediction.\n"
    )
    return {"subject": subject, "body": body}


def _existing_delivery(
    session: Session,
    review_id: uuid.UUID,
    channel: str,
    destination_key: str,
) -> FiscalWatchContractDelivery | None:
    return session.scalar(
        select(FiscalWatchContractDelivery).where(
            FiscalWatchContractDelivery.review_id == review_id,
            FiscalWatchContractDelivery.channel == channel,
            FiscalWatchContractDelivery.destination_key == destination_key,
        )
    )


def materialize_watch_deliveries(
    session: Session,
    settings: Settings,
    *,
    organization_id: uuid.UUID | None = None,
) -> tuple[int, int]:
    rows = _review_rows(session, organization_id)
    created = 0
    api_access_by_org: dict[uuid.UUID, bool] = {}

    for review, match, contract, alert, state in rows:
        memberships = session.execute(
            select(OrganizationMembership, User, CustomerNotificationPreference)
            .join(User, User.id == OrganizationMembership.user_id)
            .join(
                CustomerNotificationPreference,
                CustomerNotificationPreference.user_id == User.id,
            )
            .where(
                OrganizationMembership.organization_id == review.organization_id,
                User.is_active.is_(True),
                CustomerNotificationPreference.email_enabled.is_(True),
                CustomerNotificationPreference.include_fiscal_watch.is_(True),
            )
        ).all()
        for _membership, user, preference in memberships:
            if preference.email_enabled_at is None:
                continue
            enabled_at = preference.email_enabled_at
            if enabled_at.tzinfo is None:
                enabled_at = enabled_at.replace(tzinfo=UTC)
            review_created = review.created_at
            if review_created.tzinfo is None:
                review_created = review_created.replace(tzinfo=UTC)
            if review_created < enabled_at:
                continue
            destination_key = f"email:{user.id}"
            if _existing_delivery(session, review.id, "email", destination_key) is not None:
                continue
            payload = _email_payload(review, contract, alert, state, settings)
            session.add(
                FiscalWatchContractDelivery(
                    review_id=review.id,
                    match_id=match.id,
                    contract_id=contract.id,
                    organization_id=review.organization_id,
                    recipient_user_id=user.id,
                    channel="email",
                    destination_key=destination_key,
                    recipient_address=user.email,
                    status="pending",
                    payload_sha256=canonical_sha256(payload),
                    payload=payload,
                    details={"delivery_scope": "organization_member_opt_in"},
                )
            )
            created += 1

        api_access = api_access_by_org.get(review.organization_id)
        if api_access is None:
            _plan_code, entitlements, _subscription = current_plan(session, review.organization_id)
            api_access = entitlements.api_access
            api_access_by_org[review.organization_id] = api_access
        if not api_access:
            continue

        endpoints = list(
            session.scalars(
                select(OrganizationWebhookEndpoint).where(
                    OrganizationWebhookEndpoint.organization_id == review.organization_id,
                    OrganizationWebhookEndpoint.enabled.is_(True),
                )
            )
        )
        for endpoint in endpoints:
            if alert.event_type not in set(endpoint.event_types or []):
                continue
            if endpoint.jurisdiction_codes and state.code not in set(endpoint.jurisdiction_codes):
                continue
            endpoint_created = endpoint.created_at
            if endpoint_created.tzinfo is None:
                endpoint_created = endpoint_created.replace(tzinfo=UTC)
            review_created = review.created_at
            if review_created.tzinfo is None:
                review_created = review_created.replace(tzinfo=UTC)
            if review_created < endpoint_created:
                continue
            destination_key = f"webhook:{endpoint.id}"
            if _existing_delivery(session, review.id, "webhook", destination_key) is not None:
                continue
            delivery_id = uuid.uuid4()
            payload = _watch_payload(
                delivery_id,
                review,
                match,
                contract,
                alert,
                state,
                settings,
            )
            session.add(
                FiscalWatchContractDelivery(
                    id=delivery_id,
                    review_id=review.id,
                    match_id=match.id,
                    contract_id=contract.id,
                    organization_id=review.organization_id,
                    endpoint_id=endpoint.id,
                    channel="webhook",
                    destination_key=destination_key,
                    recipient_address=endpoint.url,
                    status="pending",
                    payload_sha256=canonical_sha256(payload),
                    payload=payload,
                    details={
                        "endpoint_name": endpoint.name,
                        "signing_secret_version": endpoint.secret_version,
                        "schema_version": WATCH_WEBHOOK_SCHEMA_VERSION,
                    },
                )
            )
            created += 1

    if created:
        session.commit()
    return len(rows), created


def _send_email(settings: Settings, delivery: FiscalWatchContractDelivery) -> tuple[bool, str | None]:
    payload = delivery.payload if isinstance(delivery.payload, dict) else {}
    recipient = delivery.recipient_address
    if not recipient:
        return False, "Email recipient is missing."
    message = EmailMessage()
    message["Subject"] = str(payload.get("subject") or "Gaia Watch notification")
    message["From"] = settings.alert_from
    message["To"] = recipient
    message.set_content(str(payload.get("body") or "Gaia Watch review requires attention."))
    try:
        with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port) as server:
            server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(message)
        return True, None
    except Exception as error:  # noqa: BLE001 - network failures are retryable evidence
        logger.warning("Watch email delivery failed: %s", error)
        return False, str(error)[:500]


def _signature(secret: str, timestamp: int, delivery_id: uuid.UUID, body: str) -> str:
    signed = f"{timestamp}.{delivery_id}.{body}".encode()
    digest = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    return f"v1={digest}"


def _record_attempt(
    session: Session,
    delivery: FiscalWatchContractDelivery,
    *,
    attempted_at: datetime,
    response_status: int | None = None,
    response_body_excerpt: str | None = None,
    error: str | None = None,
) -> None:
    session.add(
        FiscalWatchContractDeliveryAttempt(
            delivery_id=delivery.id,
            attempt_number=delivery.attempt_count,
            attempted_at=attempted_at,
            response_status=response_status,
            response_body_excerpt=(response_body_excerpt or "")[:1000] or None,
            error=(error or "")[:500] or None,
        )
    )


def _defer(delivery: FiscalWatchContractDelivery, reason: str) -> None:
    delivery.status = "deferred"
    delivery.last_error = reason[:500]
    delivery.next_attempt_at = None


def run_watch_delivery(
    session: Session,
    settings: Settings,
    *,
    organization_id: uuid.UUID | None = None,
    max_attempts: int = 5,
    max_deliveries: int = 500,
) -> WatchDeliveryRunSummary:
    reviews_checked, created = materialize_watch_deliveries(
        session,
        settings,
        organization_id=organization_id,
    )
    now = datetime.now(UTC)
    statement = select(FiscalWatchContractDelivery).where(
        FiscalWatchContractDelivery.channel.in_(("email", "webhook")),
        FiscalWatchContractDelivery.status.in_(("pending", "retrying", "deferred", "failed")),
        or_(
            FiscalWatchContractDelivery.next_attempt_at.is_(None),
            FiscalWatchContractDelivery.next_attempt_at <= now,
        ),
    )
    if organization_id is not None:
        statement = statement.where(FiscalWatchContractDelivery.organization_id == organization_id)
    deliveries = list(
        session.scalars(statement.order_by(FiscalWatchContractDelivery.created_at).limit(max_deliveries))
    )

    delivered = retrying = dead_letter = deferred = failed = 0
    for delivery in deliveries:
        if delivery.attempt_count >= max_attempts:
            delivery.status = "dead_letter"
            delivery.next_attempt_at = None
            delivery.last_error = "Watch delivery attempt limit reached."
            dead_letter += 1
            session.commit()
            continue

        if delivery.channel == "email":
            user = session.get(User, delivery.recipient_user_id) if delivery.recipient_user_id else None
            preference = (
                session.get(CustomerNotificationPreference, delivery.recipient_user_id)
                if delivery.recipient_user_id
                else None
            )
            membership = session.scalar(
                select(OrganizationMembership).where(
                    OrganizationMembership.organization_id == delivery.organization_id,
                    OrganizationMembership.user_id == delivery.recipient_user_id,
                )
            ) if delivery.recipient_user_id else None
            if (
                user is None
                or not user.is_active
                or membership is None
                or preference is None
                or not preference.email_enabled
                or not preference.include_fiscal_watch
            ):
                _defer(delivery, "Recipient is no longer eligible for Watch email delivery.")
                deferred += 1
                session.commit()
                continue
            if not _smtp_ready(settings):
                _defer(delivery, "Watch email delivery is disabled or SMTP is incomplete.")
                deferred += 1
                session.commit()
                continue

            attempted_at = datetime.now(UTC)
            delivery.attempt_count += 1
            delivery.last_attempt_at = attempted_at
            ok, error = _send_email(settings, delivery)
            delivery.last_error = error
            _record_attempt(session, delivery, attempted_at=attempted_at, error=error)
            if ok:
                delivery.status = "delivered"
                delivery.delivered_at = attempted_at
                delivery.next_attempt_at = None
                delivered += 1
            elif delivery.attempt_count >= max_attempts:
                delivery.status = "dead_letter"
                delivery.next_attempt_at = None
                dead_letter += 1
            else:
                delivery.status = "retrying"
                delivery.next_attempt_at = attempted_at + _RETRY_DELAYS[
                    min(delivery.attempt_count - 1, len(_RETRY_DELAYS) - 1)
                ]
                retrying += 1
                failed += 1
            session.commit()
            continue

        endpoint = session.get(OrganizationWebhookEndpoint, delivery.endpoint_id) if delivery.endpoint_id else None
        _plan_code, entitlements, _subscription = current_plan(session, delivery.organization_id)
        if endpoint is None or not endpoint.enabled or not entitlements.api_access:
            _defer(delivery, "Webhook endpoint is disabled, missing, or no longer entitled.")
            deferred += 1
            session.commit()
            continue
        if not webhook_delivery_ready(settings):
            _defer(delivery, "Institutional webhook delivery is disabled or signing is incomplete.")
            deferred += 1
            session.commit()
            continue

        body_text = canonical_json(delivery.payload or {})
        timestamp = int(datetime.now(UTC).timestamp())
        secret_version = int((delivery.details or {}).get("signing_secret_version") or endpoint.secret_version)
        secret = derive_signing_secret(
            settings,
            endpoint_id=endpoint.id,
            salt=endpoint.secret_salt,
            version=secret_version,
        )
        attempted_at = datetime.now(UTC)
        delivery.attempt_count += 1
        delivery.last_attempt_at = attempted_at
        response_status: int | None = None
        response_excerpt: str | None = None
        error: str | None = None
        try:
            result = _post_https(
                endpoint_url=endpoint.url,
                body=body_text.encode("utf-8"),
                headers={
                    "Gaia-Webhook-Id": str(delivery.id),
                    "Gaia-Webhook-Timestamp": str(timestamp),
                    "Gaia-Webhook-Signature": _signature(
                        secret,
                        timestamp,
                        delivery.id,
                        body_text,
                    ),
                    "Gaia-Webhook-Schema": WATCH_WEBHOOK_SCHEMA_VERSION,
                },
            )
            response_status = result.status
            response_excerpt = result.body_excerpt
            if not 200 <= result.status < 300:
                error = f"Webhook returned HTTP {result.status}."
        except Exception as exc:  # noqa: BLE001 - network failures are retryable evidence
            error = str(exc)[:500]

        delivery.response_status = response_status
        delivery.response_body_excerpt = (response_excerpt or "")[:1000] or None
        delivery.last_error = error
        _record_attempt(
            session,
            delivery,
            attempted_at=attempted_at,
            response_status=response_status,
            response_body_excerpt=response_excerpt,
            error=error,
        )
        if error is None:
            delivery.status = "delivered"
            delivery.delivered_at = attempted_at
            delivery.next_attempt_at = None
            delivered += 1
        elif delivery.attempt_count >= max_attempts:
            delivery.status = "dead_letter"
            delivery.next_attempt_at = None
            dead_letter += 1
            failed += 1
        else:
            delivery.status = "retrying"
            delivery.next_attempt_at = attempted_at + _RETRY_DELAYS[
                min(delivery.attempt_count - 1, len(_RETRY_DELAYS) - 1)
            ]
            retrying += 1
            failed += 1
        session.commit()

    return WatchDeliveryRunSummary(
        reviews_checked=reviews_checked,
        deliveries_created=created,
        delivered=delivered,
        retrying=retrying,
        dead_letter=dead_letter,
        deferred=deferred,
        failed=failed,
    )
