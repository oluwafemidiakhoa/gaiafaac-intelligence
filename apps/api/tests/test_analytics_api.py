import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from gaiafaac_api.api.v1.routes.analytics import forecasts, rankings
from gaiafaac_api.pipeline.analytics.dataset import generate_analytics_dataset
from gaiafaac_api.pipeline.analytics.run import compute_analytics


def test_rankings_route_404_without_data(session: Session) -> None:
    with pytest.raises(HTTPException) as error:
        rankings(session)
    assert error.value.status_code == 404


def test_routes_return_labelled_payloads(session: Session) -> None:
    generate_analytics_dataset(session)
    compute_analytics(session)

    payload = rankings(session)
    assert payload.data_label == "DEMO DATA - NOT REAL FAAC DATA"
    assert len(payload.rankings) == 37

    forecast_payload = forecasts(session)
    assert all(f.is_estimate is True for f in forecast_payload.forecasts)
