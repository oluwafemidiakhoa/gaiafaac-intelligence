from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import delete
from sqlalchemy.orm import Session

from gaiafaac_api.database.enums import VerificationStatus
from gaiafaac_api.database.models import Forecast, StateIndicator
from gaiafaac_api.pipeline.analytics.common import analytics_source
from gaiafaac_api.pipeline.analytics.dependency import compute_dependency
from gaiafaac_api.pipeline.analytics.forecasting import compute_forecasts
from gaiafaac_api.pipeline.analytics.rankings import compute_rankings
from gaiafaac_api.pipeline.analytics.volatility import compute_volatility


@dataclass(frozen=True)
class AnalyticsRunResult:
    indicators: int
    forecasts: int


def compute_analytics(session: Session) -> AnalyticsRunResult:
    """Recompute and persist all analytics for the demo dataset (idempotent)."""
    source = analytics_source(session)
    if source is None:
        return AnalyticsRunResult(0, 0)

    session.execute(delete(StateIndicator).where(StateIndicator.source_document_id == source.id))
    session.execute(delete(Forecast).where(Forecast.source_document_id == source.id))

    indicator_specs = (
        compute_rankings(session) + compute_volatility(session) + compute_dependency(session)
    )
    for spec in indicator_specs:
        session.add(
            StateIndicator(
                reporting_period_id=spec.reporting_period_id,
                state_id=spec.state_id,
                source_document_id=spec.source_document_id,
                indicator_type=spec.indicator_type,
                indicator_name=spec.indicator_name,
                value=spec.value,
                unit=spec.unit,
                methodology=spec.methodology,
                verification_status=VerificationStatus.PENDING,
            )
        )

    forecast_specs = compute_forecasts(session)
    for spec in forecast_specs:
        session.add(
            Forecast(
                state_id=spec.state_id,
                source_document_id=spec.source_document_id,
                target_period=spec.target_period,
                method=spec.method,
                point_estimate=spec.point_estimate,
                lower_bound=spec.lower_bound,
                upper_bound=spec.upper_bound,
                training_start=spec.training_start,
                training_end=spec.training_end,
                metrics=spec.metrics,
                verification_status=VerificationStatus.PENDING,
                is_demo=True,
                is_published=False,
            )
        )

    session.commit()
    return AnalyticsRunResult(len(indicator_specs), len(forecast_specs))
