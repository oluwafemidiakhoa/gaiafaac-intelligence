from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.models import ReportingPeriod, StateAllocation
from gaiafaac_api.pipeline.analytics.common import (
    IndicatorSpec,
    analytics_periods,
    analytics_source,
)


def _rank_map(session: Session, period_id: uuid.UUID) -> dict[uuid.UUID, int]:
    rows = session.execute(
        select(StateAllocation.state_id, StateAllocation.net_allocation)
        .where(
            StateAllocation.reporting_period_id == period_id,
            StateAllocation.net_allocation.is_not(None),
        )
        .order_by(StateAllocation.net_allocation.desc())
    ).all()
    return {state_id: index for index, (state_id, _net) in enumerate(rows, start=1)}


def compute_rankings(session: Session) -> list[IndicatorSpec]:
    source = analytics_source(session)
    periods = analytics_periods(session)
    if source is None or not periods:
        return []
    latest = periods[-1]
    previous: ReportingPeriod | None = periods[-2] if len(periods) >= 2 else None
    current = _rank_map(session, latest.id)
    prior = _rank_map(session, previous.id) if previous is not None else {}

    specs: list[IndicatorSpec] = []
    for state_id, rank in current.items():
        specs.append(
            IndicatorSpec(
                reporting_period_id=latest.id,
                state_id=state_id,
                source_document_id=source.id,
                indicator_type="ranking",
                indicator_name="net_allocation_rank",
                value=Decimal(rank),
                unit="rank",
                methodology=f"Descending net_allocation rank for {latest.reporting_label}.",
            )
        )
        if state_id in prior:
            specs.append(
                IndicatorSpec(
                    reporting_period_id=latest.id,
                    state_id=state_id,
                    source_document_id=source.id,
                    indicator_type="ranking",
                    indicator_name="net_allocation_rank_change",
                    value=Decimal(prior[state_id] - rank),
                    unit="rank_delta",
                    methodology="Prior-period rank minus current rank (positive = moved up).",
                )
            )
    return specs
