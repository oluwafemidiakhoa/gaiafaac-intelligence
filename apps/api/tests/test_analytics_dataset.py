from datetime import date
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from gaiafaac_api.database.models import StateAllocation
from gaiafaac_api.pipeline.analytics.common import latest_analytics_period
from gaiafaac_api.pipeline.analytics.dataset import generate_analytics_dataset


def _demo_csv() -> Path:
    return Path(__file__).resolve().parents[3] / "database/seeds/demo_state_allocations.csv"


def test_dataset_shape_and_invariants(session: Session) -> None:
    summary = generate_analytics_dataset(session)
    assert summary.periods == 36
    assert summary.allocations == 36 * 37

    allocations = list(session.scalars(select(StateAllocation)))
    assert allocations
    for allocation in allocations:
        assert allocation.is_demo is True
        assert allocation.is_published is False
        assert allocation.gross_total - allocation.total_deductions == allocation.net_allocation

    latest = latest_analytics_period(session)
    assert latest is not None
    assert latest.revenue_month == date(2098, 12, 1)


def test_dataset_is_idempotent(session: Session) -> None:
    first = generate_analytics_dataset(session)
    second = generate_analytics_dataset(session)
    assert (first.periods, first.allocations) == (second.periods, second.allocations)
    assert session.scalar(select(func.count()).select_from(StateAllocation)) == 36 * 37


def test_dataset_does_not_change_m4_latest_demo_period(session: Session) -> None:
    from gaiafaac_api.database.seeds import seed_demo_allocations
    from gaiafaac_api.services.demo_data import latest_demo_period

    seed_demo_allocations(session, _demo_csv())
    generate_analytics_dataset(session)
    period = latest_demo_period(session)
    assert period is not None
    assert period.revenue_month == date(2099, 1, 1)
