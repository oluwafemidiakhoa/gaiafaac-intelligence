from sqlalchemy import func, select
from sqlalchemy.orm import Session

from gaiafaac_api.database.enums import VerificationStatus
from gaiafaac_api.database.models import Forecast, StateIndicator
from gaiafaac_api.pipeline.analytics.dataset import generate_analytics_dataset
from gaiafaac_api.pipeline.analytics.run import compute_analytics


def test_compute_analytics_persists_and_is_idempotent(session: Session) -> None:
    generate_analytics_dataset(session)
    first = compute_analytics(session)
    assert first.indicators > 0
    assert first.forecasts == 37

    indicators_after_first = session.scalar(select(func.count()).select_from(StateIndicator))
    second = compute_analytics(session)
    indicators_after_second = session.scalar(select(func.count()).select_from(StateIndicator))
    assert indicators_after_first == indicators_after_second
    assert (first.indicators, first.forecasts) == (second.indicators, second.forecasts)

    assert all(
        indicator.verification_status is VerificationStatus.PENDING
        for indicator in session.scalars(select(StateIndicator))
    )
    assert all(
        forecast.is_demo is True and forecast.is_published is False
        for forecast in session.scalars(select(Forecast))
    )
