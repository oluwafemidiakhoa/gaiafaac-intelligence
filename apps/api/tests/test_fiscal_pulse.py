from datetime import date
from decimal import Decimal

from sqlalchemy import select

from gaiafaac_api.database.enums import ReportedUnit
from gaiafaac_api.database.models import ReportingPeriod, SourceDocument, State, StateAllocation
from gaiafaac_api.database.seeds import seed_states
from gaiafaac_api.services.fiscal_pulse import fiscal_pulse


def _source(session) -> SourceDocument:
    source = SourceDocument(
        source_organization="OAGF",
        original_filename="pulse.pdf",
        storage_path="pulse",
        sha256="b" * 64,
        mime_type="application/pdf",
    )
    session.add(source)
    session.flush()
    return source


def _period(session, month: int, *, published: bool = True, demo: bool = False):
    period = ReportingPeriod(
        revenue_month=date(2024, month, 1),
        reporting_label=f"2024-{month:02d}",
        is_demo=demo,
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
    gross=None,
    deductions=None,
    net=None,
    published=True,
    demo=False,
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
            is_demo=demo,
            is_published=published,
        )
    )


def test_fiscal_pulse_metrics_and_fct_missing_financials(session):
    seed_states(session)
    regular = session.scalars(select(State).where(State.is_fct.is_(False))).first()
    fct = session.scalars(select(State).where(State.is_fct.is_(True))).one()
    source = _source(session)

    regular_nets = [
        Decimal("90"),
        Decimal("90"),
        Decimal("90"),
        Decimal("110"),
        Decimal("110"),
        Decimal("110"),
    ]
    for month, net in enumerate(regular_nets, start=1):
        period = _period(session, month)
        _allocation(
            session,
            source,
            period,
            regular,
            gross=Decimal("120"),
            deductions=Decimal("20") if net == Decimal("100") else Decimal("120") - net,
            net=net,
        )
        _allocation(session, source, period, fct, net=Decimal("50"))

    session.flush()
    result = fiscal_pulse(session, 2024)
    by_slug = {state.state_slug: state for state in result.states}

    assert result.months_published == 6
    assert result.expected_months == 12
    assert result.coverage_status == "partial_year"
    assert result.coverage_label == "Partial 2024 series · 6 of 12 months published"

    regular_result = by_slug[regular.slug]
    assert regular_result.annual_gross == "720.00"
    assert regular_result.annual_net == "600.00"
    assert regular_result.annual_deductions == "120.00"
    assert regular_result.deduction_burden_pct == 16.67
    assert regular_result.net_retention_pct == 83.33
    assert regular_result.momentum == "Improving"
    assert regular_result.momentum_pct == 22.22
    assert regular_result.volatility == "Moderate"
    assert regular_result.evidence_status == "Verified"

    fct_result = by_slug[fct.slug]
    assert fct_result.annual_gross is None
    assert fct_result.annual_deductions is None
    assert fct_result.deduction_burden_pct is None
    assert fct_result.net_retention_pct is None
    assert fct_result.evidence_status == "Partial"


def test_fiscal_pulse_excludes_demo_unpublished_and_incomplete_rows(session):
    seed_states(session)
    state = session.scalars(select(State).where(State.is_fct.is_(False))).first()
    source = _source(session)

    published_period = _period(session, 1)
    _allocation(
        session,
        source,
        published_period,
        state,
        gross=Decimal("100"),
        deductions=Decimal("10"),
        net=Decimal("90"),
    )

    unpublished_period = _period(session, 2, published=False)
    _allocation(session, source, unpublished_period, state, net=Decimal("999"), published=False)

    demo_period = _period(session, 3, demo=True, published=False)
    _allocation(session, source, demo_period, state, net=Decimal("888"), demo=True, published=False)

    session.flush()
    result = fiscal_pulse(session, 2024)
    assert result.months_published == 1
    assert result.coverage_status == "partial_year"
    assert result.coverage_label == "Partial 2024 series · 1 of 12 months published"
    assert len(result.states) == 1
    item = result.states[0]
    assert item.annual_net == "90.00"
    assert item.momentum == "Insufficient data"
    assert item.volatility == "Insufficient data"


def test_fiscal_pulse_marks_full_twelve_month_series_complete(session):
    seed_states(session)
    state = session.scalars(select(State).where(State.is_fct.is_(False))).first()
    source = _source(session)

    for month in range(1, 13):
        period = _period(session, month)
        _allocation(
            session,
            source,
            period,
            state,
            gross=Decimal("100"),
            deductions=Decimal("10"),
            net=Decimal("90"),
        )

    session.flush()
    result = fiscal_pulse(session, 2024)
    assert result.months_published == 12
    assert result.coverage_status == "complete_year"
    assert result.coverage_label == "Complete 2024 series · 12 of 12 months published"
