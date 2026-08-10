from __future__ import annotations

from collections import defaultdict
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.models import ReportingPeriod, State, StateAllocation
from gaiafaac_api.fiscal_watch_schemas import FiscalWatchEvent, FiscalWatchResponse

_MONTHLY_MOVE_THRESHOLD = Decimal("25")
_DEDUCTION_BURDEN_THRESHOLD = Decimal("50")


def _money(value: Decimal | None) -> str | None:
    return format(value, ".2f") if value is not None else None


def _pct(value: Decimal) -> float:
    return round(float(value), 2)


def fiscal_watch(session: Session, year: int) -> FiscalWatchResponse:
    periods = list(
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

    if not periods:
        return FiscalWatchResponse(
            year=year,
            latest_revenue_month=None,
            previous_revenue_month=None,
            event_count=0,
            events=[],
            note=(
                "Fiscal Watch is derived only from published, non-demo GaiaFAAC records. "
                "No published periods are available for this year."
            ),
        )

    period_ids = [period.id for period in periods]
    period_by_id = {period.id: period for period in periods}
    rows = list(
        session.execute(
            select(StateAllocation, State)
            .join(State, StateAllocation.state_id == State.id)
            .where(
                StateAllocation.reporting_period_id.in_(period_ids),
                StateAllocation.is_published.is_(True),
                StateAllocation.is_demo.is_(False),
            )
        ).tuples()
    )

    grouped: dict[object, list[tuple[StateAllocation, State, ReportingPeriod]]] = defaultdict(list)
    for allocation, state in rows:
        grouped[state.id].append((allocation, state, period_by_id[allocation.reporting_period_id]))

    events: list[FiscalWatchEvent] = []

    for state_rows in grouped.values():
        state_rows.sort(key=lambda item: item[2].revenue_month)
        current, state, current_period = state_rows[-1]
        previous = state_rows[-2][0] if len(state_rows) >= 2 else None

        proof_path = f"/fiscal-proof/{state.slug}/{current_period.revenue_month.isoformat()}"

        if current.net_allocation is not None and current.net_allocation < 0:
            events.append(
                FiscalWatchEvent(
                    kind="negative_net",
                    severity="elevated",
                    state_name=state.name,
                    state_slug=state.slug,
                    state_code=state.code,
                    revenue_month=current_period.revenue_month,
                    headline=f"{state.name} reported a negative net FAAC allocation",
                    detail=(
                        f"Published net allocation is NGN {_money(current.net_allocation)}. "
                        "This is a source-reported value and should be reviewed "
                        "in its Fiscal Proof."
                    ),
                    current_net=_money(current.net_allocation),
                    previous_net=_money(previous.net_allocation) if previous else None,
                    change_pct=None,
                    deduction_burden_pct=None,
                    proof_path=proof_path,
                )
            )

        if (
            previous is not None
            and current.net_allocation is not None
            and previous.net_allocation is not None
            and previous.net_allocation != 0
        ):
            change = (
                (current.net_allocation - previous.net_allocation)
                / abs(previous.net_allocation)
                * Decimal("100")
            )
            if abs(change) >= _MONTHLY_MOVE_THRESHOLD:
                direction = "increased" if change > 0 else "decreased"
                events.append(
                    FiscalWatchEvent(
                        kind="large_monthly_move",
                        severity="watch",
                        state_name=state.name,
                        state_slug=state.slug,
                        state_code=state.code,
                        revenue_month=current_period.revenue_month,
                        headline=(
                            f"{state.name} net FAAC allocation {direction} sharply month over month"
                        ),
                        detail=(
                            f"Net allocation moved {_pct(change):+.2f}% from the prior "
                            "published month."
                        ),
                        current_net=_money(current.net_allocation),
                        previous_net=_money(previous.net_allocation),
                        change_pct=_pct(change),
                        deduction_burden_pct=None,
                        proof_path=proof_path,
                    )
                )

        if (
            current.gross_total is not None
            and current.total_deductions is not None
            and current.gross_total > 0
        ):
            burden = current.total_deductions / current.gross_total * Decimal("100")
            if burden >= _DEDUCTION_BURDEN_THRESHOLD:
                events.append(
                    FiscalWatchEvent(
                        kind="high_deduction_burden",
                        severity="watch",
                        state_name=state.name,
                        state_slug=state.slug,
                        state_code=state.code,
                        revenue_month=current_period.revenue_month,
                        headline=f"{state.name} deductions exceeded half of gross allocation",
                        detail=(
                            f"Deductions were {_pct(burden):.2f}% of gross allocation "
                            "in the latest published month."
                        ),
                        current_net=_money(current.net_allocation),
                        previous_net=_money(previous.net_allocation) if previous else None,
                        change_pct=None,
                        deduction_burden_pct=_pct(burden),
                        proof_path=proof_path,
                    )
                )

    severity_order = {"elevated": 0, "watch": 1}
    events.sort(
        key=lambda event: (
            severity_order[event.severity],
            event.state_name,
            event.kind,
        )
    )

    return FiscalWatchResponse(
        year=year,
        latest_revenue_month=periods[-1].revenue_month,
        previous_revenue_month=periods[-2].revenue_month if len(periods) >= 2 else None,
        event_count=len(events),
        events=events,
        note=(
            "Fiscal Watch is a deterministic monitoring layer over published, non-demo records. "
            "Signals describe allocation changes and deductions; they are not credit ratings, "
            "solvency assessments, corruption indicators, or predictions."
        ),
    )
