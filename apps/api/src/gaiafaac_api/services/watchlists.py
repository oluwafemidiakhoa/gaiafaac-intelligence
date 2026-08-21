from __future__ import annotations

import uuid
from datetime import UTC, datetime, time

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.customer_models import (
    CustomerAlert,
    CustomerWatchlist,
    OrganizationAlert,
    OrganizationAlertReceipt,
    OrganizationWatchlist,
)
from gaiafaac_api.database.ledger_models import FiscalEvent
from gaiafaac_api.database.models import State, User
from gaiafaac_api.services.fiscal_watch import fiscal_watch
from gaiafaac_api.watchlist_schemas import (
    WatchlistAlert,
    WatchlistAlertsResponse,
    WatchlistItem,
)


def _stored_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _headline(event_type: str, state_name: str) -> str:
    labels = {
        "new_source_detected": "New fiscal source detected",
        "source_revised": "Official fiscal source revised",
        "claim_superseded": "Published fiscal claim superseded",
        "evidence_upgraded": "Fiscal evidence status upgraded",
        "evidence_downgraded": "Fiscal evidence status downgraded",
        "cross_source_conflict": "Cross-source fiscal conflict recorded",
        "fiscal_state_changed": "Published Fiscal State changed",
        "faac_spike": "FAAC movement crossed the spike threshold",
        "faac_decline": "FAAC movement crossed the decline threshold",
    }
    return f"{state_name}: {labels.get(event_type, event_type.replace('_', ' '))}"


def _watch_payload(event) -> dict[str, object]:
    return {
        "headline": event.headline,
        "detail": event.detail,
        "link_path": event.proof_path,
        "evidence_ids": [],
        "metrics": {
            "current_net": event.current_net,
            "previous_net": event.previous_net,
            "change_pct": event.change_pct,
            "deduction_burden_pct": event.deduction_burden_pct,
        },
    }


def _fiscal_event_payload(event: FiscalEvent, state: State) -> dict[str, object]:
    return {
        "headline": _headline(event.event_type, state.name),
        "detail": event.explanation,
        "link_path": f"/events?jurisdiction=NG-{state.code}&event_type={event.event_type}",
        "evidence_ids": list(event.evidence_ids),
        "metrics": dict(event.calculation),
    }


def list_watchlists(session: Session, user: User) -> list[WatchlistItem]:
    rows = session.execute(
        select(CustomerWatchlist, State)
        .join(State, State.id == CustomerWatchlist.state_id)
        .where(CustomerWatchlist.user_id == user.id)
        .order_by(State.name)
    ).all()
    return [
        WatchlistItem(
            id=watch.id,
            state_name=state.name,
            state_code=state.code,
            state_slug=state.slug,
            geopolitical_zone=state.geopolitical_zone,
            created_at=watch.created_at,
        )
        for watch, state in rows
    ]


def add_watchlist(session: Session, user: User, state_code: str) -> WatchlistItem | None:
    code = state_code.strip().upper()
    state = session.scalar(select(State).where(State.code == code))
    if state is None:
        return None

    existing = session.scalar(
        select(CustomerWatchlist).where(
            CustomerWatchlist.user_id == user.id,
            CustomerWatchlist.state_id == state.id,
        )
    )
    if existing is not None:
        return WatchlistItem(
            id=existing.id,
            state_name=state.name,
            state_code=state.code,
            state_slug=state.slug,
            geopolitical_zone=state.geopolitical_zone,
            created_at=existing.created_at,
        )

    row = CustomerWatchlist(user_id=user.id, state_id=state.id)
    session.add(row)
    session.commit()
    session.refresh(row)
    return WatchlistItem(
        id=row.id,
        state_name=state.name,
        state_code=state.code,
        state_slug=state.slug,
        geopolitical_zone=state.geopolitical_zone,
        created_at=row.created_at,
    )


def remove_watchlist(session: Session, user: User, watchlist_id: uuid.UUID) -> bool:
    row = session.scalar(
        select(CustomerWatchlist).where(
            CustomerWatchlist.id == watchlist_id,
            CustomerWatchlist.user_id == user.id,
        )
    )
    if row is None:
        return False
    session.delete(row)
    session.commit()
    return True


def _watched_states(session: Session, user: User) -> list[State]:
    return list(
        session.scalars(
            select(State)
            .join(CustomerWatchlist, CustomerWatchlist.state_id == State.id)
            .where(CustomerWatchlist.user_id == user.id)
            .order_by(State.name)
        )
    )


def _existing_event_keys(session: Session, user: User) -> set[str]:
    return set(
        session.scalars(select(CustomerAlert.event_key).where(CustomerAlert.user_id == user.id))
    )


def sync_watchlist_alerts(session: Session, user: User, year: int) -> int:
    states = _watched_states(session, user)
    if not states:
        return 0

    state_by_code = {state.code: state for state in states}
    state_by_id = {state.id: state for state in states}
    existing_keys = _existing_event_keys(session, user)
    pending: list[CustomerAlert] = []

    watch = fiscal_watch(session, year)
    for event in watch.events:
        state = state_by_code.get(event.state_code)
        if state is None:
            continue
        event_key = (
            f"fiscal-watch:{event.state_code}:{event.revenue_month.isoformat()}:{event.kind}"
        )
        if event_key in existing_keys:
            continue
        pending.append(
            CustomerAlert(
                user_id=user.id,
                state_id=state.id,
                event_key=event_key,
                source_kind="fiscal_watch",
                source_event_id=None,
                event_type=event.kind,
                severity=event.severity,
                occurred_at=datetime.combine(event.revenue_month, time.min, tzinfo=UTC),
                payload=_watch_payload(event),
            )
        )
        existing_keys.add(event_key)

    start = datetime(year, 1, 1, tzinfo=UTC)
    end = datetime(year + 1, 1, 1, tzinfo=UTC)
    lifecycle_events = list(
        session.scalars(
            select(FiscalEvent)
            .where(
                FiscalEvent.state_id.in_(list(state_by_id)),
                FiscalEvent.detected_at >= start,
                FiscalEvent.detected_at < end,
            )
            .order_by(FiscalEvent.detected_at, FiscalEvent.event_id)
        )
    )
    for event in lifecycle_events:
        state = state_by_id[event.state_id]
        event_key = f"fiscal-event:{event.event_id}"
        if event_key in existing_keys:
            continue
        pending.append(
            CustomerAlert(
                user_id=user.id,
                state_id=state.id,
                event_key=event_key,
                source_kind="fiscal_event",
                source_event_id=event.event_id,
                event_type=event.event_type,
                severity=str(event.severity),
                occurred_at=_stored_utc(event.detected_at),
                payload=_fiscal_event_payload(event, state),
            )
        )
        existing_keys.add(event_key)

    if not pending:
        return 0
    session.add_all(pending)
    session.commit()
    return len(pending)


def _alert_item(
    alert: CustomerAlert | OrganizationAlert,
    state: State,
    read_at: datetime | None = None,
) -> WatchlistAlert:
    payload = alert.payload if isinstance(alert.payload, dict) else {}
    evidence_ids = payload.get("evidence_ids", [])
    metrics = payload.get("metrics", {})
    effective_read_at = read_at
    if isinstance(alert, CustomerAlert):
        effective_read_at = alert.read_at
    return WatchlistAlert(
        id=alert.id,
        event_key=alert.event_key,
        source_kind=alert.source_kind,
        event_type=alert.event_type,
        severity=alert.severity,
        state_name=state.name,
        state_slug=state.slug,
        state_code=state.code,
        occurred_at=_stored_utc(alert.occurred_at),
        headline=str(payload.get("headline") or alert.event_type.replace("_", " ")),
        detail=str(payload.get("detail") or "Recorded governed fiscal event."),
        link_path=str(payload.get("link_path") or "/events"),
        evidence_ids=(
            [str(item) for item in evidence_ids] if isinstance(evidence_ids, list) else []
        ),
        metrics=metrics if isinstance(metrics, dict) else {},
        read_at=_stored_utc(effective_read_at) if effective_read_at is not None else None,
        is_read=effective_read_at is not None,
    )


def watchlist_alerts(session: Session, user: User, year: int) -> WatchlistAlertsResponse:
    sync_watchlist_alerts(session, user, year)
    start = datetime(year, 1, 1, tzinfo=UTC)
    end = datetime(year + 1, 1, 1, tzinfo=UTC)
    rows = session.execute(
        select(CustomerAlert, State)
        .join(State, State.id == CustomerAlert.state_id)
        .where(
            CustomerAlert.user_id == user.id,
            CustomerAlert.occurred_at >= start,
            CustomerAlert.occurred_at < end,
        )
        .order_by(CustomerAlert.occurred_at.desc(), CustomerAlert.created_at.desc())
    ).all()
    alerts = [_alert_item(alert, state) for alert, state in rows]
    return WatchlistAlertsResponse(
        year=year,
        watchlist_count=len(list_watchlists(session, user)),
        alert_count=len(alerts),
        unread_count=sum(not alert.is_read for alert in alerts),
        alerts=alerts,
        note=(
            "The inbox persists customer notification snapshots derived from deterministic "
            "Fiscal Watch signals and immutable Fiscal Events. Authoritative fiscal values "
            "remain in GaiaFAAC's governed ledgers; alerts are not credit ratings, solvency "
            "assessments, corruption indicators, or predictions."
        ),
    )


def mark_alert_read(session: Session, user: User, alert_id: uuid.UUID) -> bool:
    alert = session.scalar(
        select(CustomerAlert).where(
            CustomerAlert.id == alert_id,
            CustomerAlert.user_id == user.id,
        )
    )
    if alert is None:
        return False
    if alert.read_at is None:
        alert.read_at = datetime.now(UTC)
        session.commit()
    return True


def mark_all_alerts_read(session: Session, user: User, year: int) -> int:
    start = datetime(year, 1, 1, tzinfo=UTC)
    end = datetime(year + 1, 1, 1, tzinfo=UTC)
    rows = list(
        session.scalars(
            select(CustomerAlert).where(
                CustomerAlert.user_id == user.id,
                CustomerAlert.read_at.is_(None),
                CustomerAlert.occurred_at >= start,
                CustomerAlert.occurred_at < end,
            )
        )
    )
    if not rows:
        return 0
    now = datetime.now(UTC)
    for row in rows:
        row.read_at = now
    session.commit()
    return len(rows)


def list_organization_watchlists(
    session: Session, organization_id: uuid.UUID
) -> list[WatchlistItem]:
    rows = session.execute(
        select(OrganizationWatchlist, State)
        .join(State, State.id == OrganizationWatchlist.state_id)
        .where(OrganizationWatchlist.organization_id == organization_id)
        .order_by(State.name)
    ).all()
    return [
        WatchlistItem(
            id=watch.id,
            state_name=state.name,
            state_code=state.code,
            state_slug=state.slug,
            geopolitical_zone=state.geopolitical_zone,
            created_at=watch.created_at,
        )
        for watch, state in rows
    ]


def add_organization_watchlist(
    session: Session,
    organization_id: uuid.UUID,
    user: User,
    state_code: str,
) -> WatchlistItem | None:
    code = state_code.strip().upper()
    state = session.scalar(select(State).where(State.code == code))
    if state is None:
        return None

    existing = session.scalar(
        select(OrganizationWatchlist).where(
            OrganizationWatchlist.organization_id == organization_id,
            OrganizationWatchlist.state_id == state.id,
        )
    )
    if existing is not None:
        return WatchlistItem(
            id=existing.id,
            state_name=state.name,
            state_code=state.code,
            state_slug=state.slug,
            geopolitical_zone=state.geopolitical_zone,
            created_at=existing.created_at,
        )

    row = OrganizationWatchlist(
        organization_id=organization_id,
        state_id=state.id,
        created_by_user_id=user.id,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return WatchlistItem(
        id=row.id,
        state_name=state.name,
        state_code=state.code,
        state_slug=state.slug,
        geopolitical_zone=state.geopolitical_zone,
        created_at=row.created_at,
    )


def remove_organization_watchlist(
    session: Session,
    organization_id: uuid.UUID,
    watchlist_id: uuid.UUID,
) -> bool:
    row = session.scalar(
        select(OrganizationWatchlist).where(
            OrganizationWatchlist.id == watchlist_id,
            OrganizationWatchlist.organization_id == organization_id,
        )
    )
    if row is None:
        return False
    session.delete(row)
    session.commit()
    return True


def _organization_watched_states(session: Session, organization_id: uuid.UUID) -> list[State]:
    return list(
        session.scalars(
            select(State)
            .join(OrganizationWatchlist, OrganizationWatchlist.state_id == State.id)
            .where(OrganizationWatchlist.organization_id == organization_id)
            .order_by(State.name)
        )
    )


def _existing_organization_event_keys(session: Session, organization_id: uuid.UUID) -> set[str]:
    return set(
        session.scalars(
            select(OrganizationAlert.event_key).where(
                OrganizationAlert.organization_id == organization_id
            )
        )
    )


def sync_organization_watchlist_alerts(
    session: Session, organization_id: uuid.UUID, year: int
) -> int:
    states = _organization_watched_states(session, organization_id)
    if not states:
        return 0

    state_by_code = {state.code: state for state in states}
    state_by_id = {state.id: state for state in states}
    existing_keys = _existing_organization_event_keys(session, organization_id)
    pending: list[OrganizationAlert] = []

    watch = fiscal_watch(session, year)
    for event in watch.events:
        state = state_by_code.get(event.state_code)
        if state is None:
            continue
        event_key = (
            f"fiscal-watch:{event.state_code}:{event.revenue_month.isoformat()}:{event.kind}"
        )
        if event_key in existing_keys:
            continue
        pending.append(
            OrganizationAlert(
                organization_id=organization_id,
                state_id=state.id,
                event_key=event_key,
                source_kind="fiscal_watch",
                source_event_id=None,
                event_type=event.kind,
                severity=event.severity,
                occurred_at=datetime.combine(event.revenue_month, time.min, tzinfo=UTC),
                payload=_watch_payload(event),
            )
        )
        existing_keys.add(event_key)

    start = datetime(year, 1, 1, tzinfo=UTC)
    end = datetime(year + 1, 1, 1, tzinfo=UTC)
    lifecycle_events = list(
        session.scalars(
            select(FiscalEvent)
            .where(
                FiscalEvent.state_id.in_(list(state_by_id)),
                FiscalEvent.detected_at >= start,
                FiscalEvent.detected_at < end,
            )
            .order_by(FiscalEvent.detected_at, FiscalEvent.event_id)
        )
    )
    for event in lifecycle_events:
        state = state_by_id[event.state_id]
        event_key = f"fiscal-event:{event.event_id}"
        if event_key in existing_keys:
            continue
        pending.append(
            OrganizationAlert(
                organization_id=organization_id,
                state_id=state.id,
                event_key=event_key,
                source_kind="fiscal_event",
                source_event_id=event.event_id,
                event_type=event.event_type,
                severity=str(event.severity),
                occurred_at=_stored_utc(event.detected_at),
                payload=_fiscal_event_payload(event, state),
            )
        )
        existing_keys.add(event_key)

    if not pending:
        return 0
    session.add_all(pending)
    session.commit()
    return len(pending)


def organization_watchlist_alerts(
    session: Session,
    user: User,
    organization_id: uuid.UUID,
    year: int,
) -> WatchlistAlertsResponse:
    sync_organization_watchlist_alerts(session, organization_id, year)
    start = datetime(year, 1, 1, tzinfo=UTC)
    end = datetime(year + 1, 1, 1, tzinfo=UTC)
    rows = session.execute(
        select(OrganizationAlert, State)
        .join(State, State.id == OrganizationAlert.state_id)
        .where(
            OrganizationAlert.organization_id == organization_id,
            OrganizationAlert.occurred_at >= start,
            OrganizationAlert.occurred_at < end,
        )
        .order_by(OrganizationAlert.occurred_at.desc(), OrganizationAlert.created_at.desc())
    ).all()
    alert_ids = [alert.id for alert, _state in rows]
    read_map: dict[uuid.UUID, datetime] = {}
    if alert_ids:
        read_map = {
            alert_id: read_at
            for alert_id, read_at in session.execute(
                select(OrganizationAlertReceipt.alert_id, OrganizationAlertReceipt.read_at).where(
                    OrganizationAlertReceipt.user_id == user.id,
                    OrganizationAlertReceipt.alert_id.in_(alert_ids),
                )
            ).all()
        }
    alerts = [_alert_item(alert, state, read_map.get(alert.id)) for alert, state in rows]
    return WatchlistAlertsResponse(
        year=year,
        watchlist_count=len(list_organization_watchlists(session, organization_id)),
        alert_count=len(alerts),
        unread_count=sum(not alert.is_read for alert in alerts),
        alerts=alerts,
        note=(
            "This shared organization inbox is derived from deterministic Fiscal Watch signals "
            "and immutable Fiscal Events. Read state is personal to each member. Authoritative "
            "fiscal values remain in GaiaFAAC's governed ledgers; alerts are not credit ratings, "
            "solvency assessments, corruption indicators, or predictions."
        ),
    )


def mark_organization_alert_read(
    session: Session,
    user: User,
    organization_id: uuid.UUID,
    alert_id: uuid.UUID,
) -> bool:
    alert = session.scalar(
        select(OrganizationAlert).where(
            OrganizationAlert.id == alert_id,
            OrganizationAlert.organization_id == organization_id,
        )
    )
    if alert is None:
        return False
    existing = session.scalar(
        select(OrganizationAlertReceipt).where(
            OrganizationAlertReceipt.alert_id == alert.id,
            OrganizationAlertReceipt.user_id == user.id,
        )
    )
    if existing is None:
        session.add(OrganizationAlertReceipt(alert_id=alert.id, user_id=user.id))
        session.commit()
    return True


def mark_all_organization_alerts_read(
    session: Session,
    user: User,
    organization_id: uuid.UUID,
    year: int,
) -> int:
    start = datetime(year, 1, 1, tzinfo=UTC)
    end = datetime(year + 1, 1, 1, tzinfo=UTC)
    alerts = list(
        session.scalars(
            select(OrganizationAlert).where(
                OrganizationAlert.organization_id == organization_id,
                OrganizationAlert.occurred_at >= start,
                OrganizationAlert.occurred_at < end,
            )
        )
    )
    if not alerts:
        return 0
    alert_ids = [alert.id for alert in alerts]
    read_ids = set(
        session.scalars(
            select(OrganizationAlertReceipt.alert_id).where(
                OrganizationAlertReceipt.user_id == user.id,
                OrganizationAlertReceipt.alert_id.in_(alert_ids),
            )
        )
    )
    pending = [
        OrganizationAlertReceipt(alert_id=alert.id, user_id=user.id)
        for alert in alerts
        if alert.id not in read_ids
    ]
    if not pending:
        return 0
    session.add_all(pending)
    session.commit()
    return len(pending)
