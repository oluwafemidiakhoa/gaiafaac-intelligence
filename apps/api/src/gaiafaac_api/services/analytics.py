from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.analytics_schemas import (
    DependencyResponse,
    DependencyRow,
    ForecastRow,
    ForecastsResponse,
    RankingRow,
    RankingsResponse,
    VolatilityResponse,
    VolatilityRow,
)
from gaiafaac_api.database.models import Forecast, State, StateAllocation, StateIndicator
from gaiafaac_api.pipeline.analytics.common import (
    VOLATILITY_WINDOW,
    analytics_source,
    latest_analytics_period,
)

_SCOPE = (
    "Synthetic demo analytics computed from labelled demo figures only. "
    "Not real FAAC data; forecasts are estimates, not reported allocations."
)


def _money(value: Decimal | None) -> str | None:
    return format(value, ".2f") if value is not None else None


def _ratio(value: Decimal | None) -> str | None:
    return format(value, "f") if value is not None else None


def _states(session: Session) -> dict:
    return {state.id: state for state in session.scalars(select(State))}


def get_rankings(session: Session) -> RankingsResponse | None:
    latest = latest_analytics_period(session)
    if latest is None:
        return None
    indicators = list(
        session.scalars(
            select(StateIndicator).where(
                StateIndicator.reporting_period_id == latest.id,
                StateIndicator.indicator_type == "ranking",
            )
        )
    )
    if not indicators:
        return None
    states = _states(session)
    nets = {
        state_id: net
        for state_id, net in session.execute(
            select(StateAllocation.state_id, StateAllocation.net_allocation).where(
                StateAllocation.reporting_period_id == latest.id
            )
        )
    }
    ranks = {
        i.state_id: int(i.value) for i in indicators if i.indicator_name == "net_allocation_rank"
    }
    changes = {
        i.state_id: int(i.value)
        for i in indicators
        if i.indicator_name == "net_allocation_rank_change"
    }
    rows = [
        RankingRow(
            state_name=states[state_id].name,
            state_code=states[state_id].code,
            state_slug=states[state_id].slug,
            geopolitical_zone=states[state_id].geopolitical_zone,
            net_allocation=_money(nets.get(state_id)),
            rank=rank,
            rank_change=changes.get(state_id),
        )
        for state_id, rank in sorted(ranks.items(), key=lambda kv: kv[1])
    ]
    return RankingsResponse(
        scope_note=_SCOPE,
        reporting_label=latest.reporting_label,
        revenue_month=latest.revenue_month,
        rankings=rows,
    )


def get_volatility(session: Session) -> VolatilityResponse | None:
    latest = latest_analytics_period(session)
    if latest is None:
        return None
    indicators = list(
        session.scalars(
            select(StateIndicator).where(
                StateIndicator.reporting_period_id == latest.id,
                StateIndicator.indicator_type == "volatility",
            )
        )
    )
    if not indicators:
        return None
    states = _states(session)
    rows = [
        VolatilityRow(
            state_name=states[i.state_id].name,
            state_code=states[i.state_id].code,
            state_slug=states[i.state_id].slug,
            coefficient_of_variation=_ratio(i.value),
        )
        for i in sorted(indicators, key=lambda i: states[i.state_id].name)
    ]
    return VolatilityResponse(scope_note=_SCOPE, window_periods=VOLATILITY_WINDOW, rows=rows)


def get_dependency(session: Session) -> DependencyResponse | None:
    latest = latest_analytics_period(session)
    if latest is None:
        return None
    indicators = list(
        session.scalars(
            select(StateIndicator).where(
                StateIndicator.reporting_period_id == latest.id,
                StateIndicator.indicator_type == "dependency",
            )
        )
    )
    if not indicators:
        return None
    states = _states(session)
    shares: dict = {}
    hhi: dict = {}
    for indicator in indicators:
        if indicator.indicator_name == "net_concentration_hhi":
            hhi[indicator.state_id] = indicator.value
        elif indicator.indicator_name.endswith("_net_share"):
            component = indicator.indicator_name.removesuffix("_net_share")
            shares.setdefault(indicator.state_id, {})[component] = _ratio(indicator.value)
    rows = [
        DependencyRow(
            state_name=states[state_id].name,
            state_code=states[state_id].code,
            state_slug=states[state_id].slug,
            shares=shares.get(state_id, {}),
            concentration_hhi=_ratio(hhi.get(state_id)),
        )
        for state_id in sorted(hhi, key=lambda sid: states[sid].name)
    ]
    return DependencyResponse(scope_note=_SCOPE, reporting_label=latest.reporting_label, rows=rows)


def get_forecasts(session: Session) -> ForecastsResponse | None:
    source = analytics_source(session)
    if source is None:
        return None
    forecasts = list(
        session.scalars(
            select(Forecast).where(
                Forecast.source_document_id == source.id,
                Forecast.is_demo.is_(True),
                Forecast.is_published.is_(False),
            )
        )
    )
    if not forecasts:
        return None
    states = _states(session)
    rows = [
        ForecastRow(
            state_name=states[f.state_id].name,
            state_code=states[f.state_id].code,
            state_slug=states[f.state_id].slug,
            method=f.method.value,
            target_period=f.target_period,
            point_estimate=_money(f.point_estimate),
            lower_bound=_money(f.lower_bound),
            upper_bound=_money(f.upper_bound),
            training_start=f.training_start,
            training_end=f.training_end,
        )
        for f in sorted(forecasts, key=lambda f: states[f.state_id].name)
    ]
    return ForecastsResponse(scope_note=_SCOPE, forecasts=rows)
