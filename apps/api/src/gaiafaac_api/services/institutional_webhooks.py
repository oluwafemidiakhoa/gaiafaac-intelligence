from __future__ import annotations

import hashlib
import hmac
import http.client
import ipaddress
import json
import secrets
import socket
import ssl
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from urllib.parse import urlsplit

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from gaiafaac_api.config import Settings
from gaiafaac_api.database.ledger_models import FiscalEvent
from gaiafaac_api.database.models import State
from gaiafaac_api.database.webhook_models import (
    OrganizationWebhookDelivery,
    OrganizationWebhookEndpoint,
)
from gaiafaac_api.ledger import canonical_json, canonical_sha256, canonicalize
from gaiafaac_api.services.account import current_plan
from gaiafaac_api.services.fiscal_institutional import LIFECYCLE_EVENT_TYPES

WEBHOOK_SCHEMA_VERSION = "gaia-fiscal-webhook-v1"
_SIGNATURE_VERSION = "v1"
_RETRY_DELAYS = (
    timedelta(minutes=5),
    timedelta(minutes=30),
    timedelta(hours=2),
    timedelta(hours=12),
    timedelta(hours=24),
)


@dataclass(frozen=True)
class WebhookRunSummary:
    endpoints_checked: int = 0
    deliveries_created: int = 0
    delivered: int = 0
    retrying: int = 0
    dead_letter: int = 0
    deferred: int = 0


@dataclass(frozen=True)
class WebhookHttpResult:
    status: int
    body_excerpt: str


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def webhook_configuration_ready(settings: Settings) -> bool:
    return bool(settings.institutional_webhook_master_secret)


def webhook_delivery_ready(settings: Settings) -> bool:
    return settings.institutional_webhook_enabled and webhook_configuration_ready(settings)


def validate_webhook_url(value: str) -> str:
    raw = value.strip()
    parsed = urlsplit(raw)
    if parsed.scheme.lower() != "https":
        raise ValueError("Webhook endpoints must use HTTPS.")
    if not parsed.hostname:
        raise ValueError("Webhook endpoint hostname is required.")
    if parsed.username or parsed.password:
        raise ValueError("Webhook endpoint credentials are not allowed in the URL.")
    if parsed.fragment:
        raise ValueError("Webhook endpoint fragments are not allowed.")
    if parsed.port not in {None, 443}:
        raise ValueError("Webhook endpoints must use HTTPS port 443.")
    hostname = parsed.hostname.rstrip(".").lower()
    if hostname == "localhost" or hostname.endswith(".localhost"):
        raise ValueError("Webhook endpoint must use a globally routable hostname.")
    try:
        literal = ipaddress.ip_address(hostname)
    except ValueError:
        literal = None
    if literal is not None and not literal.is_global:
        raise ValueError("Webhook endpoint IP address is not globally routable.")
    _resolve_public_addresses(hostname)
    return raw


def _resolve_public_addresses(hostname: str) -> list[str]:
    try:
        records = socket.getaddrinfo(hostname, 443, type=socket.SOCK_STREAM)
    except OSError as error:
        raise ValueError("Webhook hostname could not be resolved.") from error
    addresses: list[str] = []
    for record in records:
        address = record[4][0]
        try:
            parsed = ipaddress.ip_address(address)
        except ValueError:
            continue
        if not parsed.is_global:
            raise ValueError("Webhook hostname resolves to a non-public network address.")
        if address not in addresses:
            addresses.append(address)
    if not addresses:
        raise ValueError("Webhook hostname did not resolve to a globally routable address.")
    return addresses


def derive_signing_secret(
    settings: Settings,
    *,
    endpoint_id: uuid.UUID,
    salt: str,
    version: int,
) -> str:
    master = settings.institutional_webhook_master_secret
    if not master:
        raise ValueError("Institutional webhook signing is not configured.")
    seed = f"{endpoint_id}:{salt}:{version}".encode()
    digest = hmac.new(master.encode(), seed, hashlib.sha256).hexdigest()
    return f"gwhsec_{digest}"


def _event_types(values: list[str]) -> list[str]:
    normalized = sorted({value.strip().lower() for value in values if value.strip()})
    unsupported = [value for value in normalized if value not in LIFECYCLE_EVENT_TYPES]
    if unsupported:
        raise ValueError(f"Unsupported webhook event type: {unsupported[0]}.")
    if not normalized:
        raise ValueError("At least one fiscal event type is required.")
    return normalized


def _jurisdictions(values: list[str]) -> list[str]:
    return sorted(
        {
            value.strip().upper().removeprefix("NG-")
            for value in values
            if value.strip()
        }
    )


def create_endpoint(
    session: Session,
    settings: Settings,
    *,
    organization_id: uuid.UUID,
    created_by_user_id: uuid.UUID,
    name: str,
    url: str,
    event_types: list[str],
    jurisdiction_codes: list[str],
) -> tuple[OrganizationWebhookEndpoint, str]:
    if not webhook_configuration_ready(settings):
        raise ValueError("Institutional webhook signing is not configured.")
    codes = _jurisdictions(jurisdiction_codes)
    if codes:
        known = set(session.scalars(select(State.code).where(State.code.in_(codes))))
        missing = [code for code in codes if code not in known]
        if missing:
            raise LookupError(f"Unknown jurisdiction code: {missing[0]}.")
    endpoint = OrganizationWebhookEndpoint(
        organization_id=organization_id,
        created_by_user_id=created_by_user_id,
        name=name.strip(),
        url=validate_webhook_url(url),
        enabled=True,
        event_types=_event_types(event_types),
        jurisdiction_codes=codes,
        secret_salt=secrets.token_hex(32),
        secret_version=1,
    )
    session.add(endpoint)
    session.commit()
    session.refresh(endpoint)
    secret = derive_signing_secret(
        settings,
        endpoint_id=endpoint.id,
        salt=endpoint.secret_salt,
        version=endpoint.secret_version,
    )
    return endpoint, secret


def rotate_endpoint_secret(
    session: Session,
    settings: Settings,
    endpoint: OrganizationWebhookEndpoint,
) -> str:
    endpoint.secret_version += 1
    pending = list(
        session.scalars(
            select(OrganizationWebhookDelivery).where(
                OrganizationWebhookDelivery.endpoint_id == endpoint.id,
                OrganizationWebhookDelivery.status.in_(("pending", "retrying", "deferred")),
            )
        )
    )
    for delivery in pending:
        delivery.signing_secret_version = endpoint.secret_version
    session.commit()
    return derive_signing_secret(
        settings,
        endpoint_id=endpoint.id,
        salt=endpoint.secret_salt,
        version=endpoint.secret_version,
    )


def set_endpoint_enabled(
    session: Session,
    endpoint: OrganizationWebhookEndpoint,
    *,
    enabled: bool,
) -> None:
    endpoint.enabled = enabled
    endpoint.disabled_at = None if enabled else datetime.now(UTC)
    session.commit()


def _event_payload(
    *,
    delivery_id: uuid.UUID,
    event: FiscalEvent,
    state: State,
) -> dict[str, object]:
    return canonicalize(
        {
            "id": str(delivery_id),
            "type": event.event_type,
            "created_at": _utc(event.detected_at),
            "data": {
                "event_id": event.event_id,
                "jurisdiction": {
                    "code": f"NG-{state.code.upper()}",
                    "name": state.name,
                },
                "event_type": event.event_type,
                "severity": event.severity,
                "effective_at": _utc(event.effective_at),
                "detected_at": _utc(event.detected_at),
                "evidence_status": event.evidence_status,
                "evidence_ids": list(event.evidence_ids),
                "calculation": dict(event.calculation),
                "explanation": event.explanation,
                "fiscal_state_id": event.fiscal_state_id,
                "methodology_version": event.methodology_version,
            },
            "meta": {
                "schema_version": WEBHOOK_SCHEMA_VERSION,
                "meaning": (
                    "Deterministic fiscal evidence lifecycle event. No causal, misconduct, "
                    "credit, solvency, or predictive inference is implied."
                ),
            },
        }
    )


def enqueue_endpoint_events(session: Session, endpoint: OrganizationWebhookEndpoint) -> int:
    query = (
        select(FiscalEvent, State)
        .join(State, State.id == FiscalEvent.state_id)
        .where(
            FiscalEvent.event_type.in_(endpoint.event_types),
            FiscalEvent.detected_at >= endpoint.created_at,
        )
        .order_by(FiscalEvent.detected_at, FiscalEvent.event_id)
    )
    if endpoint.jurisdiction_codes:
        query = query.where(State.code.in_(endpoint.jurisdiction_codes))
    rows = session.execute(query).all()
    created = 0
    for event, state in rows:
        exists = session.scalar(
            select(OrganizationWebhookDelivery.id).where(
                OrganizationWebhookDelivery.endpoint_id == endpoint.id,
                OrganizationWebhookDelivery.fiscal_event_id == event.event_id,
            )
        )
        if exists is not None:
            continue
        delivery_id = uuid.uuid4()
        payload = _event_payload(delivery_id=delivery_id, event=event, state=state)
        session.add(
            OrganizationWebhookDelivery(
                id=delivery_id,
                endpoint_id=endpoint.id,
                organization_id=endpoint.organization_id,
                fiscal_event_id=event.event_id,
                status="pending",
                attempt_count=0,
                signing_secret_version=endpoint.secret_version,
                payload_sha256=canonical_sha256(payload),
                payload=payload,
            )
        )
        created += 1
    if created:
        session.commit()
    return created


def _signature(secret: str, timestamp: int, delivery_id: uuid.UUID, body: str) -> str:
    signed = f"{timestamp}.{delivery_id}.{body}".encode()
    digest = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    return f"{_SIGNATURE_VERSION}={digest}"


def _post_https(
    *,
    endpoint_url: str,
    body: bytes,
    headers: dict[str, str],
    timeout: float = 10.0,
) -> WebhookHttpResult:
    parsed = urlsplit(validate_webhook_url(endpoint_url))
    hostname = parsed.hostname
    if hostname is None:
        raise ValueError("Webhook endpoint hostname is required.")
    addresses = _resolve_public_addresses(hostname)
    path = parsed.path or "/"
    if parsed.query:
        path = f"{path}?{parsed.query}"
    request_headers = {
        "Host": hostname,
        "Content-Type": "application/json; charset=utf-8",
        "Content-Length": str(len(body)),
        "Connection": "close",
        "User-Agent": "GaiaFiscal-Webhooks/1.0",
        **headers,
    }
    header_text = "".join(f"{key}: {value}\r\n" for key, value in request_headers.items())
    request = f"POST {path} HTTP/1.1\r\n{header_text}\r\n".encode("ascii") + body
    context = ssl.create_default_context()
    last_error: OSError | ssl.SSLError | None = None
    for address in addresses:
        raw_socket = None
        tls_socket = None
        try:
            raw_socket = socket.create_connection((address, 443), timeout=timeout)
            tls_socket = context.wrap_socket(raw_socket, server_hostname=hostname)
            tls_socket.settimeout(timeout)
            tls_socket.sendall(request)
            response = http.client.HTTPResponse(tls_socket)
            response.begin()
            excerpt = response.read(1000).decode("utf-8", errors="replace")
            return WebhookHttpResult(status=response.status, body_excerpt=excerpt)
        except (OSError, ssl.SSLError) as error:
            last_error = error
        finally:
            if tls_socket is not None:
                tls_socket.close()
            elif raw_socket is not None:
                raw_socket.close()
    raise ConnectionError(str(last_error or "Webhook connection failed."))


def _defer_organization_deliveries(
    session: Session,
    organization_id: uuid.UUID,
    reason: str,
) -> int:
    deliveries = list(
        session.scalars(
            select(OrganizationWebhookDelivery).where(
                OrganizationWebhookDelivery.organization_id == organization_id,
                OrganizationWebhookDelivery.status.in_(("pending", "retrying", "deferred")),
            )
        )
    )
    for delivery in deliveries:
        delivery.status = "deferred"
        delivery.last_error = reason[:500]
        delivery.next_attempt_at = None
    if deliveries:
        session.commit()
    return len(deliveries)


def run_webhook_delivery(
    session: Session,
    settings: Settings,
    *,
    max_attempts: int = 5,
    max_deliveries: int = 500,
) -> WebhookRunSummary:
    endpoints = list(
        session.scalars(
            select(OrganizationWebhookEndpoint)
            .where(OrganizationWebhookEndpoint.enabled.is_(True))
            .order_by(OrganizationWebhookEndpoint.created_at)
        )
    )
    created = delivered = retrying = dead_letter = deferred = 0
    checked_orgs: set[uuid.UUID] = set()
    eligible_endpoints: list[OrganizationWebhookEndpoint] = []
    for endpoint in endpoints:
        if endpoint.organization_id not in checked_orgs:
            _code, entitlements, _subscription = current_plan(session, endpoint.organization_id)
            checked_orgs.add(endpoint.organization_id)
            if not entitlements.api_access:
                deferred += _defer_organization_deliveries(
                    session,
                    endpoint.organization_id,
                    "Organization plan no longer includes institutional webhook delivery.",
                )
                continue
        else:
            _code, entitlements, _subscription = current_plan(session, endpoint.organization_id)
            if not entitlements.api_access:
                continue
        eligible_endpoints.append(endpoint)
        created += enqueue_endpoint_events(session, endpoint)

    now = datetime.now(UTC)
    due = list(
        session.scalars(
            select(OrganizationWebhookDelivery)
            .where(
                OrganizationWebhookDelivery.status.in_(("pending", "retrying", "deferred")),
                or_(
                    OrganizationWebhookDelivery.next_attempt_at.is_(None),
                    OrganizationWebhookDelivery.next_attempt_at <= now,
                ),
            )
            .order_by(OrganizationWebhookDelivery.created_at)
            .limit(max_deliveries)
        )
    )
    eligible_ids = {endpoint.id for endpoint in eligible_endpoints}
    for delivery in due:
        endpoint = session.get(OrganizationWebhookEndpoint, delivery.endpoint_id)
        if endpoint is None or not endpoint.enabled or endpoint.id not in eligible_ids:
            if delivery.status != "deferred":
                delivery.status = "deferred"
                delivery.last_error = "Webhook endpoint is disabled or no longer entitled."
                delivery.next_attempt_at = None
                deferred += 1
                session.commit()
            continue
        if not webhook_delivery_ready(settings):
            delivery.status = "deferred"
            delivery.last_error = "Institutional webhook delivery is disabled by the operator."
            delivery.next_attempt_at = None
            deferred += 1
            session.commit()
            continue
        if canonical_sha256(delivery.payload) != delivery.payload_sha256:
            delivery.status = "dead_letter"
            delivery.last_error = "Stored webhook payload failed integrity verification."
            delivery.next_attempt_at = None
            dead_letter += 1
            session.commit()
            continue

        body_text = canonical_json(delivery.payload)
        timestamp = int(datetime.now(UTC).timestamp())
        secret = derive_signing_secret(
            settings,
            endpoint_id=endpoint.id,
            salt=endpoint.secret_salt,
            version=delivery.signing_secret_version,
        )
        headers = {
            "Gaia-Webhook-Id": str(delivery.id),
            "Gaia-Webhook-Timestamp": str(timestamp),
            "Gaia-Webhook-Signature": _signature(secret, timestamp, delivery.id, body_text),
            "Gaia-Webhook-Secret-Version": str(delivery.signing_secret_version),
            "Gaia-Webhook-Event": str(delivery.payload.get("type", "fiscal_event")),
        }
        attempt_at = datetime.now(UTC)
        delivery.attempt_count += 1
        delivery.last_attempt_at = attempt_at
        try:
            result = _post_https(
                endpoint_url=endpoint.url,
                body=body_text.encode("utf-8"),
                headers=headers,
            )
            delivery.response_status = result.status
            delivery.response_body_excerpt = result.body_excerpt
            delivery.last_error = None
            if 200 <= result.status < 300:
                delivery.status = "delivered"
                delivery.delivered_at = attempt_at
                delivery.next_attempt_at = None
                delivered += 1
            else:
                raise ConnectionError(f"Webhook returned HTTP {result.status}.")
        except (ConnectionError, OSError, ValueError) as error:
            delivery.last_error = str(error)[:500]
            if delivery.attempt_count >= max_attempts:
                delivery.status = "dead_letter"
                delivery.next_attempt_at = None
                dead_letter += 1
            else:
                delivery.status = "retrying"
                delay = _RETRY_DELAYS[min(delivery.attempt_count - 1, len(_RETRY_DELAYS) - 1)]
                delivery.next_attempt_at = attempt_at + delay
                retrying += 1
        session.commit()

    return WebhookRunSummary(
        endpoints_checked=len(endpoints),
        deliveries_created=created,
        delivered=delivered,
        retrying=retrying,
        dead_letter=dead_letter,
        deferred=deferred,
    )
