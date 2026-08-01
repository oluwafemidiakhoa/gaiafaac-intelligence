from datetime import date
from decimal import Decimal

from sqlalchemy import select

from gaiafaac_api.database.enums import ReportedUnit
from gaiafaac_api.database.models import (
    ReportingPeriod,
    SourceDocument,
    State,
    StateAllocation,
)
from gaiafaac_api.database.seeds import seed_states
from gaiafaac_api.services.published_analytics import published_analytics


def _source(session) -> SourceDocument:
    source = SourceDocument(
        source_organization="OAGF",
        original_filename="x.pdf",
        storage_path="x",
        sha256="a" * 64,
        mime_type="application/pdf",
    )
    session.add(source)
    session.flush()
    return source


def _publish_month(session, source, month, allocations):
    period = ReportingPeriod(
        revenue_month=month,
        reporting_label=f"Month {month}",
        is_demo=False,
        is_published=True,
    )
    session.add(period)
    session.flush()
    for state, net in allocations:
        session.add(
            StateAllocation(
                reporting_period_id=period.id,
                state_id=state.id,
                source_document_id=source.id,
                net_allocation=net,
                reported_unit=ReportedUnit.NAIRA,
                is_demo=False,
                is_published=True,
            )
        )
    session.flush()


def test_analytics_trend_rankings_and_movers(session):
    seed_states(session)
    a_state, b_state = session.scalars(select(State).limit(2)).all()
    source = _source(session)
    _publish_month(
        session,
        source,
        date(2024, 1, 1),
        [(a_state, Decimal("100")), (b_state, Decimal("200"))],
    )
    _publish_month(
        session,
        source,
        date(2024, 2, 1),
        [(a_state, Decimal("150")), (b_state, Decimal("100"))],
    )

    result = published_analytics(session)
    assert result.months_published == 2
    assert [t.total_net for t in result.national_trend] == ["300.00", "250.00"]
    # latest month (Feb): a_state 150 outranks b_state 100
    assert result.top_states[0].net_allocation == "150.00"
    movers = {m.state_slug: m.pct_change for m in result.biggest_movers}
    assert movers[a_state.slug] == 50.0  # 100 -> 150
    assert movers[b_state.slug] == -50.0  # 200 -> 100


def test_analytics_empty_when_nothing_published(session):
    seed_states(session)
    result = published_analytics(session)
    assert result.months_published == 0
    assert result.national_trend == []
    assert result.top_states == []
