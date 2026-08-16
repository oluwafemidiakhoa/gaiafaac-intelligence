from datetime import date
from decimal import Decimal

from sqlalchemy import select

from gaiafaac_api.database.enums import ReportedUnit, VerificationStatus
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


def _publish_month(session, source, month, states, amounts):
    period = ReportingPeriod(
        revenue_month=month,
        reporting_label=f"Month {month}",
        verification_status=VerificationStatus.HUMAN_VERIFIED,
        is_demo=False,
        is_published=True,
    )
    session.add(period)
    session.flush()
    for index, state in enumerate(states):
        session.add(
            StateAllocation(
                reporting_period_id=period.id,
                state_id=state.id,
                source_document_id=source.id,
                net_allocation=amounts.get(index, Decimal("100")),
                reported_unit=ReportedUnit.NAIRA,
                verification_status=VerificationStatus.HUMAN_VERIFIED,
                is_demo=False,
                is_published=True,
            )
        )
    session.flush()
    return period


def test_analytics_trend_rankings_and_movers(session):
    seed_states(session)
    states = list(session.scalars(select(State).order_by(State.name)))
    source = _source(session)
    _publish_month(
        session,
        source,
        date(2024, 1, 1),
        states,
        {0: Decimal("100"), 1: Decimal("200")},
    )
    _publish_month(
        session,
        source,
        date(2024, 2, 1),
        states,
        {0: Decimal("150"), 1: Decimal("100")},
    )

    result = published_analytics(session)
    assert result.months_published == 2
    assert [trend.total_net for trend in result.national_trend] == ["3800.00", "3750.00"]
    assert result.top_states[0].net_allocation == "150.00"
    movers = {mover.state_slug: mover.pct_change for mover in result.biggest_movers}
    assert movers[states[0].slug] == 50.0
    assert movers[states[1].slug] == -50.0


def test_analytics_ignores_incomplete_published_period(session):
    seed_states(session)
    states = list(session.scalars(select(State).order_by(State.name)))
    source = _source(session)
    _publish_month(
        session,
        source,
        date(2024, 1, 1),
        states[:2],
        {0: Decimal("100"), 1: Decimal("200")},
    )

    result = published_analytics(session)
    assert result.months_published == 0
    assert result.national_trend == []
    assert result.top_states == []


def test_analytics_empty_when_nothing_published(session):
    seed_states(session)
    result = published_analytics(session)
    assert result.months_published == 0
    assert result.national_trend == []
    assert result.top_states == []
