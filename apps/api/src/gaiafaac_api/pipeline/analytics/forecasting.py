from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.enums import ForecastMethod
from gaiafaac_api.database.models import ReportingPeriod, StateAllocation
from gaiafaac_api.pipeline.analytics.common import (
    CENTS,
    FORECAST_MIN_HISTORY,
    FORECAST_TARGET,
    FORECAST_WINDOW,
    FORECAST_Z,
    ForecastSpec,
    analytics_periods,
    analytics_source,
    decimal_mean,
    decimal_pstdev,
)


@dataclass(frozen=True)
class ForecastPoint:
    point: Decimal
    lower: Decimal
    upper: Decimal
    residual_stdev: Decimal
    mae: Decimal
    rmse: Decimal
    observations: int
    window: int


def moving_average_forecast(history: list[Decimal]) -> ForecastPoint | None:
    values = [value for value in history if value is not None]
    if len(values) < FORECAST_MIN_HISTORY:
        return None
    window = min(FORECAST_WINDOW, len(values) - 1)
    point = decimal_mean(values[-window:]).quantize(CENTS)
    residuals = [
        values[t] - decimal_mean(values[t - window : t]) for t in range(window, len(values))
    ]
    residual_stdev = decimal_pstdev(residuals) if residuals else Decimal("0")
    half_width = (FORECAST_Z * residual_stdev).quantize(CENTS)
    mae = decimal_mean([abs(r) for r in residuals]).quantize(CENTS) if residuals else Decimal("0")
    rmse = (
        decimal_mean([r * r for r in residuals]).sqrt().quantize(CENTS)
        if residuals
        else Decimal("0")
    )
    return ForecastPoint(
        point=point,
        lower=point - half_width,
        upper=point + half_width,
        residual_stdev=residual_stdev.quantize(CENTS),
        mae=mae,
        rmse=rmse,
        observations=len(residuals),
        window=window,
    )


def compute_forecasts(session: Session) -> list[ForecastSpec]:
    source = analytics_source(session)
    periods = analytics_periods(session)
    if source is None or not periods:
        return []
    period_ids = [period.id for period in periods]
    training_start = periods[0].revenue_month
    training_end = periods[-1].revenue_month

    rows = session.execute(
        select(StateAllocation.state_id, StateAllocation.net_allocation)
        .join(ReportingPeriod, StateAllocation.reporting_period_id == ReportingPeriod.id)
        .where(StateAllocation.reporting_period_id.in_(period_ids))
        .order_by(StateAllocation.state_id, ReportingPeriod.revenue_month)
    ).all()

    by_state: dict = {}
    for state_id, net in rows:
        by_state.setdefault(state_id, []).append(net)

    specs: list[ForecastSpec] = []
    for state_id, history in by_state.items():
        forecast = moving_average_forecast(history)
        if forecast is None:
            continue
        specs.append(
            ForecastSpec(
                state_id=state_id,
                source_document_id=source.id,
                target_period=FORECAST_TARGET,
                method=ForecastMethod.MOVING_AVERAGE,
                point_estimate=forecast.point,
                lower_bound=forecast.lower,
                upper_bound=forecast.upper,
                training_start=training_start,
                training_end=training_end,
                metrics={
                    "residual_stdev": str(forecast.residual_stdev),
                    "mae": str(forecast.mae),
                    "rmse": str(forecast.rmse),
                    "observations": forecast.observations,
                    "window": forecast.window,
                    "is_estimate": True,
                },
            )
        )
    return specs
