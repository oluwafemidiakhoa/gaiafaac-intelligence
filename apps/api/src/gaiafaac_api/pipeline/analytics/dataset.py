from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from gaiafaac_api.database.enums import (
    ComponentType,
    ProcessingStatus,
    ReportedUnit,
    SourceStatus,
    VerificationStatus,
)
from gaiafaac_api.database.models import (
    ReportingPeriod,
    SourceDocument,
    State,
    StateAllocation,
    StateAllocationComponent,
)
from gaiafaac_api.database.seeds import seed_states
from gaiafaac_api.pipeline.analytics.common import (
    ANALYTICS_PERIOD_PREFIX,
    ANALYTICS_SOURCE_ORG,
    ANALYTICS_SOURCE_SHA256,
    CENTS,
    MONTH_NAMES,
    OIL_STATES,
    PERIOD_COUNT,
    START_YEAR,
    analytics_source,
    deterministic_unit,
    seasonal_factor,
    state_base,
)


@dataclass(frozen=True)
class DatasetSummary:
    periods: int
    allocations: int
    components: int
    source_document_id: uuid.UUID


def _next_month(year: int, month: int) -> date:
    return date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)


def _split(total: Decimal, shares: list[Decimal]) -> list[Decimal]:
    parts = [(total * share).quantize(CENTS) for share in shares[:-1]]
    parts.append(total - sum(parts))
    return parts


def _component_shares(code: str) -> list[tuple[ComponentType, str, Decimal]]:
    if code in OIL_STATES:
        return [
            (ComponentType.STATUTORY_ALLOCATION, "Statutory allocation", Decimal("0.55")),
            (ComponentType.VAT, "VAT", Decimal("0.20")),
            (ComponentType.DERIVATION, "Derivation", Decimal("0.25")),
        ]
    return [
        (ComponentType.STATUTORY_ALLOCATION, "Statutory allocation", Decimal("0.75")),
        (ComponentType.VAT, "VAT", Decimal("0.25")),
    ]


def _summarize(session: Session, source: SourceDocument) -> DatasetSummary:
    periods = session.scalar(
        select(func.count())
        .select_from(ReportingPeriod)
        .where(ReportingPeriod.reporting_label.like(f"{ANALYTICS_PERIOD_PREFIX}%"))
    )
    allocations = session.scalar(
        select(func.count())
        .select_from(StateAllocation)
        .where(StateAllocation.source_document_id == source.id)
    )
    components = session.scalar(
        select(func.count())
        .select_from(StateAllocationComponent)
        .join(StateAllocation, StateAllocationComponent.state_allocation_id == StateAllocation.id)
        .where(StateAllocation.source_document_id == source.id)
    )
    return DatasetSummary(periods or 0, allocations or 0, components or 0, source.id)


def generate_analytics_dataset(session: Session) -> DatasetSummary:
    """Create a labelled synthetic 37-state x 36-month demo dataset (idempotent)."""
    seed_states(session)
    existing = analytics_source(session)
    if existing is not None:
        return _summarize(session, existing)

    source = SourceDocument(
        source_organization=ANALYTICS_SOURCE_ORG,
        original_filename="demo-analytics-synthetic.dataset",
        storage_path="(synthetic; generated in-process, no file)",
        sha256=ANALYTICS_SOURCE_SHA256,
        mime_type="application/x-gaiafaac-demo",
        processing_status=ProcessingStatus.REGISTERED,
        source_status=SourceStatus.DEMO,
        document_version="analytics-v1",
        is_demo=True,
    )
    session.add(source)
    session.flush()

    states = list(session.scalars(select(State).order_by(State.code)))
    for idx in range(PERIOD_COUNT):
        year = START_YEAR + idx // 12
        month = idx % 12 + 1
        period = ReportingPeriod(
            revenue_month=date(year, month, 1),
            faac_meeting_date=_next_month(year, month),
            publication_date=_next_month(year, month),
            reporting_label=(
                f"{ANALYTICS_PERIOD_PREFIX} {MONTH_NAMES[month - 1]} {year} synthetic period"
            ),
            source_status=SourceStatus.DEMO,
            verification_status=VerificationStatus.PENDING,
            is_demo=True,
            is_published=False,
        )
        session.add(period)
        session.flush()
        for state in states:
            unit = deterministic_unit(state.code, year, month)
            gross = (
                state_base(state.code)
                * seasonal_factor(month)
                * (Decimal("0.9") + Decimal("0.2") * unit)
            ).quantize(CENTS)
            ded_rate = Decimal("0.05") + Decimal("0.10") * deterministic_unit(
                state.code, year, month, salt="ded"
            )
            deductions = (gross * ded_rate).quantize(CENTS)
            net = gross - deductions
            allocation = StateAllocation(
                reporting_period_id=period.id,
                state_id=state.id,
                source_document_id=source.id,
                gross_total=gross,
                total_deductions=deductions,
                net_allocation=net,
                gross_total_original=str(gross),
                total_deductions_original=str(deductions),
                net_allocation_original=str(net),
                reported_unit=ReportedUnit.NAIRA,
                verification_status=VerificationStatus.PENDING,
                is_demo=True,
                is_published=False,
            )
            session.add(allocation)
            session.flush()
            shares = _component_shares(state.code)
            share_values = [share for _type, _name, share in shares]
            gross_parts = _split(gross, share_values)
            ded_parts = _split(deductions, share_values)
            net_parts = _split(net, share_values)
            for (ctype, cname, _share), cg, cd, cn in zip(
                shares, gross_parts, ded_parts, net_parts, strict=True
            ):
                session.add(
                    StateAllocationComponent(
                        state_allocation_id=allocation.id,
                        component_type=ctype,
                        component_name=cname,
                        gross_amount=cg,
                        deduction_amount=cd,
                        net_amount=cn,
                        gross_amount_original=str(cg),
                        deduction_amount_original=str(cd),
                        net_amount_original=str(cn),
                        reported_unit=ReportedUnit.NAIRA,
                    )
                )

    session.commit()
    return _summarize(session, source)
