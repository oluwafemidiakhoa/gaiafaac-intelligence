from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from gaiafaac_api.config import get_settings
from gaiafaac_api.customer_auth import CurrentCustomer, DatabaseSession
from gaiafaac_api.database.webhook_models import (
    OrganizationWebhookAttempt,
    OrganizationWebhookDelivery,
    OrganizationWebhookEndpoint,
)
from gaiafaac_api.services.account import current_plan, membership_for
from gaiafaac_api.services.institutional_webhooks import (
    create_endpoint,
    rotate_endpoint_secret,
    set_endpoint_enabled,
)
from gaiafaac_api.webhook_schemas import (
    WebhookAttemptItem,
    WebhookCreateRequest,
    WebhookDeliveryItem,
    WebhookEndpointCreated,
    WebhookEndpointItem,
    WebhookSecretRotated,
)

router = APIRouter(prefix="/account/webhooks", tags=["institutional webhooks"])


def _require_webhook_admin(session: DatabaseSession, user: CurrentCustomer) -> uuid.UUID:
    membership = membership_for(session, user)
    if (
        user.organization_id is None
        or membership is None
        or membership.role not in {"owner", "admin"}
    ):
        raise HTTPException(status_code=403, detail="Organization administrator access required.")
    _code, entitlements, _subscription = current_plan(session, user.organization_id)
    if not entitlements.api_access:
        raise HTTPException(
            status_code=403,
            detail="Your current plan does not include institutional webhook delivery.",
        )
    return user.organization_id


def _endpoint_item(endpoint: OrganizationWebhookEndpoint) -> WebhookEndpointItem:
    return WebhookEndpointItem(
        id=endpoint.id,
        name=endpoint.name,
        url=endpoint.url,
        enabled=endpoint.enabled,
        event_types=list(endpoint.event_types),
        jurisdiction_codes=list(endpoint.jurisdiction_codes),
        secret_version=endpoint.secret_version,
        created_at=endpoint.created_at,
        disabled_at=endpoint.disabled_at,
    )


def _owned_endpoint(
    session: DatabaseSession,
    organization_id: uuid.UUID,
    endpoint_id: uuid.UUID,
) -> OrganizationWebhookEndpoint:
    endpoint = session.scalar(
        select(OrganizationWebhookEndpoint).where(
            OrganizationWebhookEndpoint.id == endpoint_id,
            OrganizationWebhookEndpoint.organization_id == organization_id,
        )
    )
    if endpoint is None:
        raise HTTPException(status_code=404, detail="Webhook endpoint not found.")
    return endpoint


def _owned_delivery(
    session: DatabaseSession,
    organization_id: uuid.UUID,
    delivery_id: uuid.UUID,
) -> OrganizationWebhookDelivery:
    delivery = session.scalar(
        select(OrganizationWebhookDelivery).where(
            OrganizationWebhookDelivery.id == delivery_id,
            OrganizationWebhookDelivery.organization_id == organization_id,
        )
    )
    if delivery is None:
        raise HTTPException(status_code=404, detail="Webhook delivery not found.")
    return delivery


@router.get("", response_model=list[WebhookEndpointItem])
def list_webhooks(
    session: DatabaseSession,
    user: CurrentCustomer,
) -> list[WebhookEndpointItem]:
    organization_id = _require_webhook_admin(session, user)
    endpoints = session.scalars(
        select(OrganizationWebhookEndpoint)
        .where(OrganizationWebhookEndpoint.organization_id == organization_id)
        .order_by(OrganizationWebhookEndpoint.created_at.desc())
    ).all()
    return [_endpoint_item(endpoint) for endpoint in endpoints]


@router.post("", response_model=WebhookEndpointCreated, status_code=status.HTTP_201_CREATED)
def create_webhook(
    payload: WebhookCreateRequest,
    session: DatabaseSession,
    user: CurrentCustomer,
) -> WebhookEndpointCreated:
    organization_id = _require_webhook_admin(session, user)
    try:
        endpoint, secret = create_endpoint(
            session,
            get_settings(),
            organization_id=organization_id,
            created_by_user_id=user.id,
            name=payload.name,
            url=payload.url,
            event_types=payload.event_types,
            jurisdiction_codes=payload.jurisdiction_codes,
        )
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        message = str(error)
        code = 503 if "not configured" in message else 422
        raise HTTPException(status_code=code, detail=message) from error
    return WebhookEndpointCreated(
        **_endpoint_item(endpoint).model_dump(),
        signing_secret=secret,
        signing_note=(
            "Copy this signing secret now. Gaia derives it from operator key material and "
            "does not store the plaintext secret."
        ),
    )


@router.post("/{endpoint_id}/rotate-secret", response_model=WebhookSecretRotated)
def rotate_webhook_secret(
    endpoint_id: uuid.UUID,
    session: DatabaseSession,
    user: CurrentCustomer,
) -> WebhookSecretRotated:
    organization_id = _require_webhook_admin(session, user)
    endpoint = _owned_endpoint(session, organization_id, endpoint_id)
    try:
        secret = rotate_endpoint_secret(session, get_settings(), endpoint)
    except ValueError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    return WebhookSecretRotated(
        endpoint_id=endpoint.id,
        secret_version=endpoint.secret_version,
        signing_secret=secret,
        signing_note="Replace the previous signing secret with this value immediately.",
    )


@router.post("/{endpoint_id}/disable", response_model=WebhookEndpointItem)
def disable_webhook(
    endpoint_id: uuid.UUID,
    session: DatabaseSession,
    user: CurrentCustomer,
) -> WebhookEndpointItem:
    organization_id = _require_webhook_admin(session, user)
    endpoint = _owned_endpoint(session, organization_id, endpoint_id)
    set_endpoint_enabled(session, endpoint, enabled=False)
    return _endpoint_item(endpoint)


@router.post("/{endpoint_id}/enable", response_model=WebhookEndpointItem)
def enable_webhook(
    endpoint_id: uuid.UUID,
    session: DatabaseSession,
    user: CurrentCustomer,
) -> WebhookEndpointItem:
    organization_id = _require_webhook_admin(session, user)
    endpoint = _owned_endpoint(session, organization_id, endpoint_id)
    set_endpoint_enabled(session, endpoint, enabled=True)
    return _endpoint_item(endpoint)


@router.get("/deliveries", response_model=list[WebhookDeliveryItem])
def webhook_deliveries(
    session: DatabaseSession,
    user: CurrentCustomer,
    endpoint_id: Annotated[uuid.UUID | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
) -> list[WebhookDeliveryItem]:
    organization_id = _require_webhook_admin(session, user)
    query = select(OrganizationWebhookDelivery).where(
        OrganizationWebhookDelivery.organization_id == organization_id
    )
    if endpoint_id is not None:
        _owned_endpoint(session, organization_id, endpoint_id)
        query = query.where(OrganizationWebhookDelivery.endpoint_id == endpoint_id)
    deliveries = session.scalars(
        query.order_by(OrganizationWebhookDelivery.created_at.desc()).limit(limit)
    ).all()
    return [
        WebhookDeliveryItem(
            id=delivery.id,
            endpoint_id=delivery.endpoint_id,
            fiscal_event_id=delivery.fiscal_event_id,
            status=delivery.status,
            attempt_count=delivery.attempt_count,
            next_attempt_at=delivery.next_attempt_at,
            last_attempt_at=delivery.last_attempt_at,
            delivered_at=delivery.delivered_at,
            response_status=delivery.response_status,
            last_error=delivery.last_error,
            payload_sha256=delivery.payload_sha256,
            created_at=delivery.created_at,
        )
        for delivery in deliveries
    ]


@router.get("/deliveries/{delivery_id}/attempts", response_model=list[WebhookAttemptItem])
def webhook_delivery_attempts(
    delivery_id: uuid.UUID,
    session: DatabaseSession,
    user: CurrentCustomer,
) -> list[WebhookAttemptItem]:
    organization_id = _require_webhook_admin(session, user)
    _owned_delivery(session, organization_id, delivery_id)
    attempts = session.scalars(
        select(OrganizationWebhookAttempt)
        .where(OrganizationWebhookAttempt.delivery_id == delivery_id)
        .order_by(OrganizationWebhookAttempt.attempt_number)
    ).all()
    return [
        WebhookAttemptItem(
            id=attempt.id,
            delivery_id=attempt.delivery_id,
            attempt_number=attempt.attempt_number,
            attempted_at=attempt.attempted_at,
            response_status=attempt.response_status,
            response_body_excerpt=attempt.response_body_excerpt,
            error=attempt.error,
        )
        for attempt in attempts
    ]
