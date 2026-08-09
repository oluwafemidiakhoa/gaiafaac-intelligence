from __future__ import annotations

import math
from collections import defaultdict
from datetime import date
from decimal import Decimal
from statistics import mean, pstdev

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.models import ReportingPeriod, State, StateAllocation
from gaiafaac_api.fiscal_pulse_schemas import FiscalPulseResponse, FiscalPulseState


def _money(value: Decimal | None) -> str | None:
    return format(value, ".2f") if value is not None else None


def _published_periods_for_year(session: Session, year: int) -> list[ReportingPeriod]:
    return list(
        session.scalars(
            select(ReportingPeriod)
            .where(
                ReportingPeriod.is_published.is_(True),
                ReportingPeriod.is_demo.is_(False),
                ReportingPeriod.revenue_month >= date(year, 1, 1),
                ReportingPeriod.revenue_month < date(year + 1, 1, 1),
            )
            .order_by(ReportingPeriod.revenue_month)
        )
    )


def _rows_for_periods(
    session: Session, periods: list[ReportingPeriod]
) -> list[tuple[StateAllocation, State, ReportingPeriod]]:
    if not periods:
        return []
    period_ids = [period.id for period in periods]
    period_by_id = {period.id: period for period in periods}
    rows = session.execute(
        select(StateAllocation, State)
        .join(State, StateAllocation.state_id == State.id)
        .where(
            StateAllocation.reporting_period_id.in_(period_ids),
            StateAllocation.is_published.is_(True),
            StateAllocation.is_demo.is_(False),
        )
    ).tuples()
    return [
        (allocation, state, period_by_id[allocation.reporting_period_id])
        for allocation, state in rows
    ]


def _momentum(net_values: list[Decimal]) -> tuple[str, float | None]:
    if len(net_values) < 6:
        return "Insufficient data", None
    previous = mean(float(value) for value in net_values[-6:-3])
    recent = mean(float(value) for value in net_values[-3:])
    if previous == 0:
        return "Insufficient data", None
    pct = ((recent - previous) / previous) * 100
    if pct > 5:
        return "Improving", round(pct, 2)
    if pct < -5:
        return "Weakening", round(pct, 2)
    return "Stable", round(pct, 2)


def _volatility(net_values: list[Decimal]) -> tuple[str, float | None]:
    if len(net_values) < 3:
        return "Insufficient data", None
    numeric = [float(value) for value in net_values]
    avg = mean(numeric)
    if avg <= 0:
        return "Insufficient data", None
    cv = (pstdev(numeric) / avg) * 100
    if not math.isfinite(cv):
        return "Insufficient data", None
    if cv < 10:
        label = "Low"
    elif cv < 25:
        label = "Moderate"
    else:
        label = "High"
    return label, round(cv, 2)


def fiscal_pulse(session: Session, year: int) -> FiscalPulseResponse:
    periods = _published_periods_for_year(session, year)
    rows = _rows_for_periods(session, periods)
    grouped: dict[object, list[tuple[StateAllocation, State, ReportingPeriod]]] = defaultdict(list)
    for row in rows:
        grouped[row[1].id].append(row)

    states: list[FiscalPulseState] = []
    total_net = Decimal("0")
    has_total_net = False

    for state_rows in grouped.values():
        state_rows.sort(key=lambda row: row[2].revenue_month)
        state = state_rows[0][1]
        net_values = [
            allocation.net_allocation
            for allocation, _, _ in state_rows
            if allocation.net_allocation is not None
        ]
        complete = [
            allocation
            for allocation, _, _ in state_rows
            if allocation.gross_total is not None
            and allocation.total_deductions is not None
            and allocation.net_allocation is not None
        ]

        annual_net = sum(net_values, Decimal("0")) if net_values else None
        annual_gross = (
            sum((allocation.gross_total for allocation in complete), Decimal("0"))
            if complete and len(complete) == len(periods)
            else None
        )
        annual_deductions = (
            sum((allocation.total_deductions for allocation in complete), Decimal("0"))
            if complete and len(complete) == len(periods)
            else None
        )

        deduction_burden = None
        net_retention = None
        if annual_gross is not None and annual_gross > 0:
            deduction_burden = round(float(annual_deductions / annual_gross * 100), 2)
            net_retention = round(float(annual_net / annual_gross * 100), 2) if annual_net else 0.0

        momentum, momentum_pct = _momentum(net_values)
        volatility, volatility_cv = _volatility(net_values)
        if len(state_rows) == len(periods) and len(net_values) == len(periods):
            evidence = "Verified" if len(complete) == len(periods) else "Partial"
        else:
            evidence = "Review required"

        if annual_net is not None:
            total_net += annual_net
            has_total_net = True

        states.append(
            FiscalPulseState(
                state_name=state.name,
                state_slug=state.slug,
                state_code=state.code,
                geopolitical_zone=state.geopolitical_zone,
                months_published=len(state_rows),
                months_with_net=len(net_values),
                months_with_complete_financials=len(complete),
                annual_gross=_money(annual_gross),
                annual_deductions=_money(annual_deductions),
                annual_net=_money(annual_net),
                deduction_burden_pct=deduction_burden,
                net_retention_pct=net_retention,
                momentum=momentum,
                momentum_pct=momentum_pct,
                volatility=volatility,
                volatility_cv_pct=volatility_cv,
                evidence_status=evidence,
            )
        )

    states.sort(key=lambda item: float(item.annual_net or 0), reverse=True)
    return FiscalPulseResponse(
        year=year,
        months_published=len(periods),
        latest_period_label=periods[-1].reporting_label if periods else None,
        total_net=_money(total_net) if has_total_net else None,
        states=states,
        note=(
            "Derived only from published, non-demo, human-approved records. "
            "Momentum compares the latest three available monthly net allocations "
            "with the preceding three; changes within +/-5% are labelled Stable. "
            "Volatility is population coefficient of variation: Low <10%, Moderate "
            "10-25%, High >=25%. These are descriptive allocation signals, not credit "
            "ratings."
        ),
    )
