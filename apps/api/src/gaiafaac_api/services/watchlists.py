from __future__ import annotations

import uuid
from datetime import UTC, datetime, time

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.customer_models import CustomerAlert, CustomerWatchlist
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
                payload={
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
                },
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
                payload={
                    "headline": _headline(event.event_type, state.name),
                    "detail": event.explanation,
                    "link_path": (
                        f"/events?jurisdiction=NG-{state.code}&event_type={event.event_type}"
                    ),
                    "evidence_ids": list(event.evidence_ids),
                    "metrics": dict(event.calculation),
                },
            )
        )
        existing_keys.add(event_key)

    if not pending:
        return 0
    session.add_all(pending)
    session.commit()
    return len(pending)


def _alert_item(alert: CustomerAlert, state: State) -> WatchlistAlert:
    payload = alert.payload if isinstance(alert.payload, dict) else {}
    evidence_ids = payload.get("evidence_ids", [])
    metrics = payload.get("metrics", {})
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
        read_at=_stored_utc(alert.read_at) if alert.read_at is not None else None,
        is_read=alert.read_at is not None,
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
