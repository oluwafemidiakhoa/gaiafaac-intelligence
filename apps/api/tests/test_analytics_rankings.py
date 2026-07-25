from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.models import StateAllocation
from gaiafaac_api.pipeline.analytics.common import latest_analytics_period
from gaiafaac_api.pipeline.analytics.dataset import generate_analytics_dataset
from gaiafaac_api.pipeline.analytics.rankings import compute_rankings


def test_rankings_match_net_ordering(session: Session) -> None:
    generate_analytics_dataset(session)
    latest = latest_analytics_period(session)
    assert latest is not None

    nets = {
        state_id: net
        for state_id, net in session.execute(
            select(StateAllocation.state_id, StateAllocation.net_allocation).where(
                StateAllocation.reporting_period_id == latest.id
            )
        )
    }
    expected_order = [sid for sid, _net in sorted(nets.items(), key=lambda kv: kv[1], reverse=True)]

    specs = compute_rankings(session)
    ranks = {
        spec.state_id: spec.value for spec in specs if spec.indicator_name == "net_allocation_rank"
    }
    assert len(ranks) == 37
    assert ranks[expected_order[0]] == Decimal("1")
    assert ranks[expected_order[-1]] == Decimal("37")
    assert any(spec.indicator_name == "net_allocation_rank_change" for spec in specs)
