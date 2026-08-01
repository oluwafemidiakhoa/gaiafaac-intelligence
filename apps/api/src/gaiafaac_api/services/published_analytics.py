from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.models import ReportingPeriod, State, StateAllocation
from gaiafaac_api.published_analytics_schemas import (
    MonthMover,
    PublishedAnalytics,
    RankedState,
    TrendPoint,
)


def _money(value: Decimal) -> str:
    return format(value, ".2f")


def _published_periods(session: Session) -> list[ReportingPeriod]:
    return list(
        session.scalars(
            select(ReportingPeriod)
            .where(
                ReportingPeriod.is_published.is_(True),
                ReportingPeriod.is_demo.is_(False),
            )
            .order_by(ReportingPeriod.revenue_month)
        )
    )


def _allocations(session: Session, period: ReportingPeriod) -> list[tuple[StateAllocation, State]]:
    return list(
        session.execute(
            select(StateAllocation, State)
            .join(State, StateAllocation.state_id == State.id)
            .where(
                StateAllocation.reporting_period_id == period.id,
                StateAllocation.is_published.is_(True),
                StateAllocation.is_demo.is_(False),
            )
        ).tuples()
    )


def published_analytics(session: Session) -> PublishedAnalytics:
    """Real analytics computed only from human-verified, published, non-demo records."""
    periods = _published_periods(session)
    if not periods:
        return PublishedAnalytics(
            months_published=0,
            national_trend=[],
            latest_period_label=None,
            top_states=[],
            biggest_movers=[],
            note="No verified month is published yet.",
        )

    trend: list[TrendPoint] = []
    for period in periods:
        rows = _allocations(session, period)
        total_net = sum(
            (alloc.net_allocation for alloc, _ in rows if alloc.net_allocation is not None),
            Decimal("0"),
        )
        trend.append(
            TrendPoint(
                revenue_month=period.revenue_month,
                reporting_label=period.reporting_label,
                total_net=_money(total_net),
                covered_states=len(rows),
            )
        )

    latest = periods[-1]
    latest_rows = _allocations(session, latest)
    ranked = sorted(
        (r for r in latest_rows if r[0].net_allocation is not None),
        key=lambda r: r[0].net_allocation,
        reverse=True,
    )
    top_states = [
        RankedState(
            state_name=state.name,
            state_slug=state.slug,
            state_code=state.code,
            geopolitical_zone=state.geopolitical_zone,
            net_allocation=_money(alloc.net_allocation),
        )
        for alloc, state in ranked[:10]
    ]

    movers: list[MonthMover] = []
    if len(periods) >= 2:
        previous = periods[-2]
        prev_by_state = {
            state.id: alloc.net_allocation
            for alloc, state in _allocations(session, previous)
            if alloc.net_allocation is not None
        }
        candidates: list[MonthMover] = []
        for alloc, state in latest_rows:
            prev = prev_by_state.get(state.id)
            if prev is None or prev == 0 or alloc.net_allocation is None:
                continue
            change = alloc.net_allocation - prev
            pct = float(change / prev * 100)
            candidates.append(
                MonthMover(
                    state_name=state.name,
                    state_slug=state.slug,
                    previous_net=_money(prev),
                    current_net=_money(alloc.net_allocation),
                    change=_money(change),
                    pct_change=round(pct, 2),
                )
            )
        movers = sorted(candidates, key=lambda m: abs(m.pct_change), reverse=True)[:10]

    return PublishedAnalytics(
        months_published=len(periods),
        national_trend=trend,
        latest_period_label=latest.reporting_label,
        top_states=top_states,
        biggest_movers=movers,
        note=(
            "Computed from published, human-verified records only. Movers compare the two "
            "most recent published months, which may not be calendar-consecutive."
        ),
    )
