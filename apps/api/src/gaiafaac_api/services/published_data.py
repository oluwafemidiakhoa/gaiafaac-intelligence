from __future__ import annotations

from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from gaiafaac_api.database.models import (
    ReportingPeriod,
    SourceDocument,
    State,
    StateAllocation,
)
from gaiafaac_api.published_schemas import (
    PublishedAllocation,
    PublishedOverviewResponse,
    PublishedPeriod,
    PublishedSource,
    PublishedSourceItem,
)

EXPECTED_STATE_COUNT = 37


def _money(value: Decimal | None) -> str | None:
    return format(value, ".2f") if value is not None else None


def _sum(values: list[Decimal | None]) -> str | None:
    if not values or any(value is None for value in values):
        return None
    return _money(sum((value for value in values if value is not None), Decimal("0")))


def latest_published_period(session: Session) -> ReportingPeriod | None:
    return session.scalar(
        select(ReportingPeriod)
        .where(ReportingPeriod.is_published.is_(True), ReportingPeriod.is_demo.is_(False))
        .order_by(ReportingPeriod.revenue_month.desc())
        .limit(1)
    )


def published_sources(session: Session) -> list[PublishedSourceItem]:
    """One source-document record per published month, newest first."""
    periods = session.scalars(
        select(ReportingPeriod)
        .where(ReportingPeriod.is_published.is_(True), ReportingPeriod.is_demo.is_(False))
        .order_by(ReportingPeriod.revenue_month.desc())
    )
    items: list[PublishedSourceItem] = []
    for period in periods:
        source = session.scalar(
            select(SourceDocument).where(SourceDocument.reporting_period_id == period.id)
        )
        if source is None:
            continue
        covered = (
            session.scalar(
                select(func.count())
                .select_from(StateAllocation)
                .where(
                    StateAllocation.reporting_period_id == period.id,
                    StateAllocation.is_published.is_(True),
                    StateAllocation.is_demo.is_(False),
                )
            )
            or 0
        )
        items.append(
            PublishedSourceItem(
                revenue_month=period.revenue_month,
                reporting_label=period.reporting_label,
                source_organization=source.source_organization,
                original_filename=source.original_filename,
                sha256=source.sha256,
                source_url=source.source_url,
                publication_date=source.publication_date,
                covered_states=covered,
                expected_states=EXPECTED_STATE_COUNT,
            )
        )
    return items


def get_published_overview(
    session: Session, period: ReportingPeriod
) -> PublishedOverviewResponse | None:
    rows = list(
        session.execute(
            select(StateAllocation, State)
            .join(State, StateAllocation.state_id == State.id)
            .where(
                StateAllocation.reporting_period_id == period.id,
                StateAllocation.is_published.is_(True),
                StateAllocation.is_demo.is_(False),
            )
            .order_by(State.name)
        ).tuples()
    )
    source = session.scalar(
        select(SourceDocument).where(SourceDocument.reporting_period_id == period.id)
    )
    if source is None:
        return None
    return PublishedOverviewResponse(
        period=PublishedPeriod(
            id=str(period.id),
            reporting_label=period.reporting_label,
            revenue_month=period.revenue_month,
            faac_meeting_date=period.faac_meeting_date,
            publication_date=period.publication_date,
            published_at=period.published_at,
        ),
        source=PublishedSource(
            source_organization=source.source_organization,
            source_url=source.source_url,
            original_filename=source.original_filename,
            sha256=source.sha256,
            publication_date=source.publication_date,
        ),
        covered_states=len(rows),
        expected_states=EXPECTED_STATE_COUNT,
        total_gross=_sum([allocation.gross_total for allocation, _state in rows]),
        total_deductions=_sum([allocation.total_deductions for allocation, _state in rows]),
        total_net=_sum([allocation.net_allocation for allocation, _state in rows]),
        allocations=[
            PublishedAllocation(
                state_name=state.name,
                state_code=state.code,
                state_slug=state.slug,
                geopolitical_zone=state.geopolitical_zone,
                gross_total=_money(allocation.gross_total),
                total_deductions=_money(allocation.total_deductions),
                net_allocation=_money(allocation.net_allocation),
                reported_unit=allocation.reported_unit.value,
            )
            for allocation, state in rows
        ],
    )
