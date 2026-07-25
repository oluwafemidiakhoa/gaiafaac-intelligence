from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.models import (
    ReportingPeriod,
    SourceDocument,
    State,
    StateAllocation,
    StateAllocationComponent,
)
from gaiafaac_api.demo_schemas import (
    DemoAllocation,
    DemoComponent,
    DemoOverviewResponse,
    DemoPeriod,
    DemoSource,
    DemoSourcesResponse,
    DemoStateDetailResponse,
    DemoStatesResponse,
    DemoStateSummary,
)

EXPECTED_STATE_COUNT = 37
DEMO_SCOPE_NOTE = (
    "Partial synthetic sample covering 3 of 37 jurisdictions. "
    "Totals are demo-sample totals, not national FAAC totals."
)


def _money(value: Decimal | None) -> str | None:
    return format(value, ".2f") if value is not None else None


def _sum_money(values: list[Decimal | None]) -> str | None:
    if not values or any(value is None for value in values):
        return None
    return _money(sum((value for value in values if value is not None), Decimal("0")))


def latest_demo_period(session: Session) -> ReportingPeriod | None:
    return session.scalar(
        select(ReportingPeriod)
        .where(ReportingPeriod.is_demo.is_(True))
        .order_by(ReportingPeriod.revenue_month.desc())
        .limit(1)
    )


def _period_schema(period: ReportingPeriod) -> DemoPeriod:
    return DemoPeriod(
        id=str(period.id),
        reporting_label=period.reporting_label,
        revenue_month=period.revenue_month,
        faac_meeting_date=period.faac_meeting_date,
        publication_date=period.publication_date,
        verification_status=period.verification_status,
        is_published=False,
    )


def _allocation_schema(allocation: StateAllocation, state: State) -> DemoAllocation:
    return DemoAllocation(
        state_name=state.name,
        state_code=state.code,
        state_slug=state.slug,
        geopolitical_zone=state.geopolitical_zone,
        gross_total=_money(allocation.gross_total),
        total_deductions=_money(allocation.total_deductions),
        net_allocation=_money(allocation.net_allocation),
        reported_unit=allocation.reported_unit.value,
        verification_status=allocation.verification_status,
        source_document_id=str(allocation.source_document_id),
        is_published=False,
    )


def _demo_allocations(
    session: Session, period: ReportingPeriod
) -> list[tuple[StateAllocation, State]]:
    return list(
        session.execute(
            select(StateAllocation, State)
            .join(State, StateAllocation.state_id == State.id)
            .where(
                StateAllocation.reporting_period_id == period.id,
                StateAllocation.is_demo.is_(True),
                StateAllocation.is_published.is_(False),
            )
            .order_by(State.name)
        ).tuples()
    )


def get_demo_overview(session: Session, period: ReportingPeriod) -> DemoOverviewResponse:
    rows = _demo_allocations(session, period)
    return DemoOverviewResponse(
        scope_note=DEMO_SCOPE_NOTE,
        period=_period_schema(period),
        covered_states=len(rows),
        expected_states=EXPECTED_STATE_COUNT,
        sample_gross_total=_sum_money([allocation.gross_total for allocation, _state in rows]),
        sample_deductions_total=_sum_money(
            [allocation.total_deductions for allocation, _state in rows]
        ),
        sample_net_total=_sum_money([allocation.net_allocation for allocation, _state in rows]),
        allocations=[_allocation_schema(allocation, state) for allocation, state in rows],
    )


def get_demo_states(session: Session, period: ReportingPeriod) -> DemoStatesResponse:
    allocations = {
        allocation.state_id: allocation for allocation, _state in _demo_allocations(session, period)
    }
    states = list(session.scalars(select(State).order_by(State.name)))
    return DemoStatesResponse(
        period=_period_schema(period),
        states=[
            DemoStateSummary(
                name=state.name,
                code=state.code,
                slug=state.slug,
                geopolitical_zone=state.geopolitical_zone,
                capital=state.capital,
                has_demo_allocation=state.id in allocations,
                demo_net_allocation=_money(allocations[state.id].net_allocation)
                if state.id in allocations
                else None,
                verification_status=allocations[state.id].verification_status
                if state.id in allocations
                else None,
            )
            for state in states
        ],
    )


def get_demo_state(
    session: Session, period: ReportingPeriod, slug: str
) -> DemoStateDetailResponse | None:
    state = session.scalar(select(State).where(State.slug == slug))
    if state is None:
        return None
    allocation = session.scalar(
        select(StateAllocation).where(
            StateAllocation.reporting_period_id == period.id,
            StateAllocation.state_id == state.id,
            StateAllocation.is_demo.is_(True),
            StateAllocation.is_published.is_(False),
        )
    )
    components: list[DemoComponent] = []
    if allocation is not None:
        components = [
            DemoComponent(
                component_type=component.component_type.value,
                component_name=component.component_name,
                gross_amount=_money(component.gross_amount),
                deduction_amount=_money(component.deduction_amount),
                net_amount=_money(component.net_amount),
                reported_unit=component.reported_unit.value,
            )
            for component in session.scalars(
                select(StateAllocationComponent)
                .where(StateAllocationComponent.state_allocation_id == allocation.id)
                .order_by(StateAllocationComponent.component_name)
            )
        ]
    summary = DemoStateSummary(
        name=state.name,
        code=state.code,
        slug=state.slug,
        geopolitical_zone=state.geopolitical_zone,
        capital=state.capital,
        has_demo_allocation=allocation is not None,
        demo_net_allocation=_money(allocation.net_allocation) if allocation else None,
        verification_status=allocation.verification_status if allocation else None,
    )
    return DemoStateDetailResponse(
        period=_period_schema(period),
        state=summary,
        allocation=_allocation_schema(allocation, state) if allocation else None,
        components=components,
        unavailable_note=None
        if allocation
        else "No labelled demo allocation is available for this state.",
    )


def get_demo_sources(session: Session) -> DemoSourcesResponse:
    sources = list(
        session.scalars(
            select(SourceDocument)
            .where(SourceDocument.is_demo.is_(True))
            .order_by(SourceDocument.created_at.desc())
        )
    )
    return DemoSourcesResponse(
        sources=[
            DemoSource(
                id=str(source.id),
                source_organization=source.source_organization,
                source_url=source.source_url,
                original_filename=source.original_filename,
                sha256=source.sha256,
                mime_type=source.mime_type,
                publication_date=source.publication_date,
                downloaded_at=source.downloaded_at,
                document_version=source.document_version,
                source_status=source.source_status,
                is_demo=True,
            )
            for source in sources
        ]
    )
