from sqlalchemy.orm import Session

from gaiafaac_api.pipeline.analytics.dataset import generate_analytics_dataset
from gaiafaac_api.pipeline.analytics.run import compute_analytics
from gaiafaac_api.services.analytics import (
    get_dependency,
    get_forecasts,
    get_rankings,
    get_volatility,
)

LABEL = "DEMO DATA - NOT REAL FAAC DATA"


def _prepare(session: Session) -> None:
    generate_analytics_dataset(session)
    compute_analytics(session)


def test_services_return_labelled_data(session: Session) -> None:
    assert get_rankings(session) is None

    _prepare(session)

    rankings = get_rankings(session)
    assert rankings is not None
    assert rankings.data_label == LABEL
    assert len(rankings.rankings) == 37
    assert rankings.rankings[0].rank == 1

    volatility = get_volatility(session)
    assert volatility is not None and len(volatility.rows) == 37

    dependency = get_dependency(session)
    assert dependency is not None and len(dependency.rows) == 37
    assert all(row.concentration_hhi is not None for row in dependency.rows)

    forecasts = get_forecasts(session)
    assert forecasts is not None and len(forecasts.forecasts) == 37
    assert all(f.is_estimate is True for f in forecasts.forecasts)
