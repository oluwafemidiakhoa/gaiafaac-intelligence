from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Response, status

from gaiafaac_api.config import get_settings
from gaiafaac_api.customer_auth import CurrentCustomer, DatabaseSession
from gaiafaac_api.services.account import current_plan, membership_for
from gaiafaac_api.services.alert_delivery import (
    get_notification_preference,
    update_notification_preference,
)
from gaiafaac_api.services.watchlists import (
    add_organization_watchlist,
    add_watchlist,
    list_organization_watchlists,
    list_watchlists,
    mark_alert_read,
    mark_all_alerts_read,
    mark_all_organization_alerts_read,
    mark_organization_alert_read,
    organization_watchlist_alerts,
    remove_organization_watchlist,
    remove_watchlist,
    watchlist_alerts,
)
from gaiafaac_api.watchlist_schemas import (
    NotificationPreferenceResponse,
    NotificationPreferenceUpdate,
    WatchlistAlertsResponse,
    WatchlistCreateRequest,
    WatchlistItem,
)

router = APIRouter(prefix="/watchlists", tags=["customer watchlists"])


def _require_organization_monitoring(session: DatabaseSession, user: CurrentCustomer):
    if user.organization_id is None:
        raise HTTPException(status_code=403, detail="No customer organization is attached.")
    membership = membership_for(session, user)
    if membership is None:
        raise HTTPException(status_code=403, detail="Organization membership is required.")
    _plan_code, entitlements, _subscription = current_plan(session, user.organization_id)
    if entitlements.max_users <= 1:
        raise HTTPException(
            status_code=403,
            detail="Shared organization monitoring requires the Team or API plan.",
        )
    return user.organization_id, membership


def _require_organization_monitoring_admin(
    session: DatabaseSession, user: CurrentCustomer
) -> uuid.UUID:
    organization_id, membership = _require_organization_monitoring(session, user)
    if membership.role not in {"owner", "admin"}:
        raise HTTPException(
            status_code=403,
            detail="Organization administrator access is required to change shared monitoring.",
        )
    return organization_id


@router.get("", response_model=list[WatchlistItem])
def get_watchlists(session: DatabaseSession, user: CurrentCustomer) -> list[WatchlistItem]:
    return list_watchlists(session, user)


@router.post("", response_model=WatchlistItem, status_code=status.HTTP_201_CREATED)
def create_watchlist(
    payload: WatchlistCreateRequest,
    session: DatabaseSession,
    user: CurrentCustomer,
) -> WatchlistItem:
    item = add_watchlist(session, user, payload.state_code)
    if item is None:
        raise HTTPException(status_code=404, detail="Unknown state code.")
    return item


@router.get("/organization", response_model=list[WatchlistItem])
def get_organization_watchlists(
    session: DatabaseSession, user: CurrentCustomer
) -> list[WatchlistItem]:
    organization_id, _membership = _require_organization_monitoring(session, user)
    return list_organization_watchlists(session, organization_id)


@router.post(
    "/organization",
    response_model=WatchlistItem,
    status_code=status.HTTP_201_CREATED,
)
def create_organization_watchlist(
    payload: WatchlistCreateRequest,
    session: DatabaseSession,
    user: CurrentCustomer,
) -> WatchlistItem:
    organization_id = _require_organization_monitoring_admin(session, user)
    item = add_organization_watchlist(session, organization_id, user, payload.state_code)
    if item is None:
        raise HTTPException(status_code=404, detail="Unknown state code.")
    return item


@router.delete("/organization/{watchlist_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_organization_watchlist(
    watchlist_id: uuid.UUID,
    session: DatabaseSession,
    user: CurrentCustomer,
) -> Response:
    organization_id = _require_organization_monitoring_admin(session, user)
    if not remove_organization_watchlist(session, organization_id, watchlist_id):
        raise HTTPException(status_code=404, detail="Shared watchlist item not found.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/organization/alerts", response_model=WatchlistAlertsResponse)
def get_organization_watchlist_alerts(
    session: DatabaseSession,
    user: CurrentCustomer,
    year: Annotated[int | None, Query(ge=2000, le=2100)] = None,
) -> WatchlistAlertsResponse:
    organization_id, _membership = _require_organization_monitoring(session, user)
    resolved_year = year if year is not None else datetime.now(UTC).year
    return organization_watchlist_alerts(session, user, organization_id, resolved_year)


@router.post(
    "/organization/alerts/{alert_id}/read",
    status_code=status.HTTP_204_NO_CONTENT,
)
def read_organization_watchlist_alert(
    alert_id: uuid.UUID,
    session: DatabaseSession,
    user: CurrentCustomer,
) -> Response:
    organization_id, _membership = _require_organization_monitoring(session, user)
    if not mark_organization_alert_read(session, user, organization_id, alert_id):
        raise HTTPException(status_code=404, detail="Shared alert not found.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/organization/alerts/read-all",
    status_code=status.HTTP_204_NO_CONTENT,
)
def read_all_organization_watchlist_alerts(
    session: DatabaseSession,
    user: CurrentCustomer,
    year: Annotated[int | None, Query(ge=2000, le=2100)] = None,
) -> Response:
    organization_id, _membership = _require_organization_monitoring(session, user)
    resolved_year = year if year is not None else datetime.now(UTC).year
    mark_all_organization_alerts_read(session, user, organization_id, resolved_year)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/{watchlist_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_watchlist(
    watchlist_id: uuid.UUID,
    session: DatabaseSession,
    user: CurrentCustomer,
) -> Response:
    if not remove_watchlist(session, user, watchlist_id):
        raise HTTPException(status_code=404, detail="Watchlist item not found.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/alerts", response_model=WatchlistAlertsResponse)
def get_watchlist_alerts(
    session: DatabaseSession,
    user: CurrentCustomer,
    year: Annotated[int | None, Query(ge=2000, le=2100)] = None,
) -> WatchlistAlertsResponse:
    resolved_year = year if year is not None else datetime.now(UTC).year
    return watchlist_alerts(session, user, resolved_year)


@router.post("/alerts/{alert_id}/read", status_code=status.HTTP_204_NO_CONTENT)
def read_watchlist_alert(
    alert_id: uuid.UUID,
    session: DatabaseSession,
    user: CurrentCustomer,
) -> Response:
    if not mark_alert_read(session, user, alert_id):
        raise HTTPException(status_code=404, detail="Alert not found.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/alerts/read-all", status_code=status.HTTP_204_NO_CONTENT)
def read_all_watchlist_alerts(
    session: DatabaseSession,
    user: CurrentCustomer,
    year: Annotated[int | None, Query(ge=2000, le=2100)] = None,
) -> Response:
    resolved_year = year if year is not None else datetime.now(UTC).year
    mark_all_alerts_read(session, user, resolved_year)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/preferences", response_model=NotificationPreferenceResponse)
def get_watchlist_preferences(
    session: DatabaseSession,
    user: CurrentCustomer,
) -> NotificationPreferenceResponse:
    return get_notification_preference(session, user, get_settings())


@router.post("/preferences", response_model=NotificationPreferenceResponse)
def set_watchlist_preferences(
    payload: NotificationPreferenceUpdate,
    session: DatabaseSession,
    user: CurrentCustomer,
) -> NotificationPreferenceResponse:
    return update_notification_preference(session, user, payload, get_settings())
