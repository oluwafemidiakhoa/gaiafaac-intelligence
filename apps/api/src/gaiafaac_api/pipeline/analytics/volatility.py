from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.models import ReportingPeriod, StateAllocation
from gaiafaac_api.pipeline.analytics.common import (
    RATIO_QUANT,
    VOLATILITY_MIN_OBS,
    VOLATILITY_WINDOW,
    IndicatorSpec,
    analytics_periods,
    analytics_source,
    decimal_mean,
    decimal_pstdev,
)


def coefficient_of_variation(values: list[Decimal]) -> Decimal | None:
    cleaned = [value for value in values if value is not None]
    if len(cleaned) < VOLATILITY_MIN_OBS:
        return None
    mean = decimal_mean(cleaned)
    if mean == 0:
        return None
    return (decimal_pstdev(cleaned) / mean).quantize(RATIO_QUANT)


def compute_volatility(session: Session) -> list[IndicatorSpec]:
    source = analytics_source(session)
    periods = analytics_periods(session)
    if source is None or not periods:
        return []
    window = periods[-VOLATILITY_WINDOW:]
    window_ids = [period.id for period in window]
    latest = periods[-1]

    rows = session.execute(
        select(StateAllocation.state_id, StateAllocation.net_allocation)
        .join(ReportingPeriod, StateAllocation.reporting_period_id == ReportingPeriod.id)
        .where(StateAllocation.reporting_period_id.in_(window_ids))
        .order_by(StateAllocation.state_id, ReportingPeriod.revenue_month)
    ).all()

    by_state: dict = {}
    for state_id, net in rows:
        by_state.setdefault(state_id, []).append(net)

    specs: list[IndicatorSpec] = []
    for state_id, nets in by_state.items():
        cv = coefficient_of_variation(nets)
        if cv is None:
            continue
        specs.append(
            IndicatorSpec(
                reporting_period_id=latest.id,
                state_id=state_id,
                source_document_id=source.id,
                indicator_type="volatility",
                indicator_name="net_allocation_cv",
                value=cv,
                unit="ratio",
                methodology=(
                    f"Coefficient of variation (population) of net_allocation over the "
                    f"trailing {len(window)} periods ending {latest.reporting_label}."
                ),
            )
        )
    return specs
