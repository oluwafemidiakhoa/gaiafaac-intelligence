from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.customer_models import CustomerWatchlist
from gaiafaac_api.database.models import State, User
from gaiafaac_api.services.fiscal_watch import fiscal_watch
from gaiafaac_api.watchlist_schemas import (
    WatchlistAlert,
    WatchlistAlertsResponse,
    WatchlistItem,
)


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


def watchlist_alerts(session: Session, user: User, year: int) -> WatchlistAlertsResponse:
    watchlist = list_watchlists(session, user)
    watched_codes = {item.state_code for item in watchlist}
    source = fiscal_watch(session, year)

    alerts = [
        WatchlistAlert(
            event_key=(
                f"fiscal-watch:{event.state_code}:{event.revenue_month.isoformat()}:{event.kind}"
            ),
            kind=event.kind,
            severity=event.severity,
            state_name=event.state_name,
            state_slug=event.state_slug,
            state_code=event.state_code,
            revenue_month=event.revenue_month,
            headline=event.headline,
            detail=event.detail,
            current_net=event.current_net,
            previous_net=event.previous_net,
            change_pct=event.change_pct,
            deduction_burden_pct=event.deduction_burden_pct,
            proof_path=event.proof_path,
        )
        for event in source.events
        if event.state_code in watched_codes
    ]

    return WatchlistAlertsResponse(
        year=year,
        watchlist_count=len(watchlist),
        alert_count=len(alerts),
        alerts=alerts,
        note=(
            "Watchlist alerts filter GaiaFAAC's deterministic Fiscal Watch signals to states "
            "saved by the authenticated customer. They are not credit ratings, solvency "
            "assessments, corruption indicators, or predictions."
        ),
    )
