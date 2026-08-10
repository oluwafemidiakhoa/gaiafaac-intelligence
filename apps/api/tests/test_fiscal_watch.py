from datetime import date
from decimal import Decimal

from sqlalchemy import select

from gaiafaac_api.database.enums import ReportedUnit
from gaiafaac_api.database.models import ReportingPeriod, SourceDocument, State, StateAllocation
from gaiafaac_api.database.seeds import seed_states
from gaiafaac_api.services.fiscal_watch import fiscal_watch


def _source(session) -> SourceDocument:
    source = SourceDocument(
        source_organization="OAGF",
        original_filename="watch.pdf",
        storage_path="watch.pdf",
        sha256="c" * 64,
        mime_type="application/pdf",
    )
    session.add(source)
    session.flush()
    return source


def _period(session, month: int, *, published: bool = True):
    period = ReportingPeriod(
        revenue_month=date(2026, month, 1),
        reporting_label=f"2026-{month:02d}",
        is_demo=False,
        is_published=published,
    )
    session.add(period)
    session.flush()
    return period


def _allocation(
    session,
    source,
    period,
    state,
    *,
    gross: Decimal,
    deductions: Decimal,
    net: Decimal,
    published: bool = True,
):
    session.add(
        StateAllocation(
            reporting_period_id=period.id,
            state_id=state.id,
            source_document_id=source.id,
            gross_total=gross,
            total_deductions=deductions,
            net_allocation=net,
            reported_unit=ReportedUnit.NAIRA,
            is_demo=False,
            is_published=published,
        )
    )


def test_fiscal_watch_flags_negative_net_large_move_and_high_deductions(session):
    seed_states(session)
    state = session.scalars(select(State).where(State.is_fct.is_(False))).first()
    source = _source(session)

    january = _period(session, 1)
    february = _period(session, 2)

    _allocation(
        session,
        source,
        january,
        state,
        gross=Decimal("100"),
        deductions=Decimal("20"),
        net=Decimal("80"),
    )
    _allocation(
        session,
        source,
        february,
        state,
        gross=Decimal("100"),
        deductions=Decimal("140"),
        net=Decimal("-40"),
    )

    session.flush()
    result = fiscal_watch(session, 2026)

    assert result.latest_revenue_month == date(2026, 2, 1)
    assert result.previous_revenue_month == date(2026, 1, 1)
    assert result.event_count == 3

    by_kind = {event.kind: event for event in result.events}
    assert set(by_kind) == {
        "negative_net",
        "large_monthly_move",
        "high_deduction_burden",
    }
    assert by_kind["negative_net"].severity == "elevated"
    assert by_kind["large_monthly_move"].change_pct == -150.0
    assert by_kind["high_deduction_burden"].deduction_burden_pct == 140.0
    assert by_kind["negative_net"].proof_path == (
        f"/fiscal-proof/{state.slug}/2026-02-01"
    )


def test_fiscal_watch_ignores_unpublished_rows(session):
    seed_states(session)
    state = session.scalars(select(State).where(State.is_fct.is_(False))).first()
    source = _source(session)

    january = _period(session, 1)
    february = _period(session, 2, published=False)

    _allocation(
        session,
        source,
        january,
        state,
        gross=Decimal("100"),
        deductions=Decimal("10"),
        net=Decimal("90"),
    )
    _allocation(
        session,
        source,
        february,
        state,
        gross=Decimal("100"),
        deductions=Decimal("200"),
        net=Decimal("-100"),
        published=False,
    )

    session.flush()
    result = fiscal_watch(session, 2026)

    assert result.latest_revenue_month == date(2026, 1, 1)
    assert result.event_count == 0


def test_fiscal_watch_returns_empty_feed_when_year_has_no_published_data(session):
    result = fiscal_watch(session, 2026)
    assert result.latest_revenue_month is None
    assert result.previous_revenue_month is None
    assert result.event_count == 0
    assert result.events == []
