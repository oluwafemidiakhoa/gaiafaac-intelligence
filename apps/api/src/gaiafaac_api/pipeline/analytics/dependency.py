from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.models import StateAllocation, StateAllocationComponent
from gaiafaac_api.pipeline.analytics.common import (
    RATIO_QUANT,
    IndicatorSpec,
    analytics_source,
    latest_analytics_period,
)


def component_shares(
    pairs: list[tuple[str, Decimal]],
) -> tuple[dict[str, Decimal], Decimal] | None:
    total = sum((net for _type, net in pairs), Decimal("0"))
    if not pairs or total <= 0:
        return None
    shares = {ctype: (net / total).quantize(RATIO_QUANT) for ctype, net in pairs}
    hhi = sum((share * share for share in shares.values()), Decimal("0")).quantize(RATIO_QUANT)
    return shares, hhi


def compute_dependency(session: Session) -> list[IndicatorSpec]:
    source = analytics_source(session)
    latest = latest_analytics_period(session)
    if source is None or latest is None:
        return []

    rows = session.execute(
        select(
            StateAllocation.state_id,
            StateAllocationComponent.component_type,
            StateAllocationComponent.net_amount,
        )
        .join(
            StateAllocationComponent,
            StateAllocationComponent.state_allocation_id == StateAllocation.id,
        )
        .where(StateAllocation.reporting_period_id == latest.id)
    ).all()

    by_state: dict[uuid.UUID, list[tuple[str, Decimal]]] = {}
    for state_id, component_type, net in rows:
        if net is None:
            continue
        by_state.setdefault(state_id, []).append((str(component_type), net))

    specs: list[IndicatorSpec] = []
    for state_id, pairs in by_state.items():
        result = component_shares(pairs)
        if result is None:
            continue
        shares, hhi = result
        for component_type, share in shares.items():
            specs.append(
                IndicatorSpec(
                    reporting_period_id=latest.id,
                    state_id=state_id,
                    source_document_id=source.id,
                    indicator_type="dependency",
                    indicator_name=f"{component_type}_net_share",
                    value=share,
                    unit="ratio",
                    methodology=(
                        f"Share of net allocation from {component_type} "
                        f"for {latest.reporting_label}."
                    ),
                )
            )
        specs.append(
            IndicatorSpec(
                reporting_period_id=latest.id,
                state_id=state_id,
                source_document_id=source.id,
                indicator_type="dependency",
                indicator_name="net_concentration_hhi",
                value=hhi,
                unit="index",
                methodology="Herfindahl-Hirschman index (sum of squared component net shares).",
            )
        )
    return specs
