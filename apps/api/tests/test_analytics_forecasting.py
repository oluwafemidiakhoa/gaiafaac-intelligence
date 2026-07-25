from decimal import Decimal

from sqlalchemy.orm import Session

from gaiafaac_api.pipeline.analytics.dataset import generate_analytics_dataset
from gaiafaac_api.pipeline.analytics.forecasting import (
    compute_forecasts,
    moving_average_forecast,
)


def test_forecast_requires_min_history() -> None:
    assert moving_average_forecast([Decimal("1")] * 5) is None


def test_forecast_point_and_bounds_ordering() -> None:
    history = [Decimal(n) for n in range(1, 25)]
    forecast = moving_average_forecast(history)
    assert forecast is not None
    assert forecast.lower <= forecast.point <= forecast.upper
    assert forecast.observations >= 1


def test_compute_forecasts_are_estimates_for_all_states(session: Session) -> None:
    generate_analytics_dataset(session)
    specs = compute_forecasts(session)
    assert len(specs) == 37
    for spec in specs:
        assert spec.lower_bound <= spec.point_estimate <= spec.upper_bound
        assert spec.target_period.year == 2099
        assert "residual_stdev" in spec.metrics
