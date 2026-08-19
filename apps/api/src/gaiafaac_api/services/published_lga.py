from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.enums import VerificationStatus
from gaiafaac_api.database.lga_models import LocalGovernment, LocalGovernmentAllocation
from gaiafaac_api.database.models import ReportingPeriod, SourceDocument, State
from gaiafaac_api.lga_schemas import (
    PublishedLgaAllocation,
    PublishedLgaDetailResponse,
    PublishedLgaSource,
    PublishedLgaStateResponse,
)


def _allocation(
    allocation: LocalGovernmentAllocation,
    lga: LocalGovernment,
    state: State,
    period: ReportingPeriod,
    source: SourceDocument,
) -> PublishedLgaAllocation:
    return PublishedLgaAllocation(
        reporting_period_id=period.id,
        reporting_label=period.reporting_label,
        revenue_month=period.revenue_month,
        disbursement_month=period.disbursement_month or period.revenue_month,
        allocation_period_month=period.allocation_period_month,
        published_at=allocation.published_at,
        state_name=state.name,
        state_code=state.code,
        state_slug=state.slug,
        local_government_name=lga.official_name,
        local_government_slug=lga.slug,
        net_statutory_allocation=(
            format(allocation.net_statutory_allocation, ".2f")
            if allocation.net_statutory_allocation is not None
            else None
        ),
        deduction_amount=(
            format(allocation.deduction_amount, ".2f")
            if allocation.deduction_amount is not None
            else None
        ),
        ecology_share=(
            format(allocation.ecology_share, ".2f")
            if allocation.ecology_share is not None
            else None
        ),
        ecology_transfer=(
            format(allocation.ecology_transfer, ".2f")
            if allocation.ecology_transfer is not None
            else None
        ),
        net_ecology_share=(
            format(allocation.net_ecology_share, ".2f")
            if allocation.net_ecology_share is not None
            else None
        ),
        vat_amount=(
            format(allocation.vat_amount, ".2f")
            if allocation.vat_amount is not None
            else None
        ),
        total_net_allocation=format(allocation.total_net_allocation, ".2f"),
        reported_unit=allocation.reported_unit.value,
        source_page=allocation.source_page,
        source_table=allocation.source_table,
        verification_status=allocation.verification_status.value,
        source=PublishedLgaSource(
            organization=source.source_organization,
            source_url=source.source_url,
            original_filename=source.original_filename,
            sha256=source.sha256,
            publication_date=source.publication_date,
            document_version=source.document_version,
        ),
    )


def _published_statement():
    return (
        select(
            LocalGovernmentAllocation,
            LocalGovernment,
            State,
            ReportingPeriod,
            SourceDocument,
        )
        .join(LocalGovernment, LocalGovernmentAllocation.local_government_id == LocalGovernment.id)
        .join(State, LocalGovernment.state_id == State.id)
        .join(ReportingPeriod, LocalGovernmentAllocation.reporting_period_id == ReportingPeriod.id)
        .join(SourceDocument, LocalGovernmentAllocation.source_document_id == SourceDocument.id)
        .where(
            LocalGovernmentAllocation.is_published.is_(True),
            LocalGovernmentAllocation.is_demo.is_(False),
            LocalGovernmentAllocation.verification_status == VerificationStatus.HUMAN_VERIFIED,
            SourceDocument.is_demo.is_(False),
        )
    )


def published_lgas_for_state(session: Session, *, state_code: str) -> PublishedLgaStateResponse | None:
    rows = list(
        session.execute(
            _published_statement()
            .where(State.code == state_code.upper())
            .order_by(
                LocalGovernment.official_name,
                ReportingPeriod.disbursement_month.desc(),
                ReportingPeriod.revenue_month.desc(),
            )
        ).tuples()
    )
    if not rows:
        return None

    latest_by_lga: dict[str, PublishedLgaAllocation] = {}
    for allocation, lga, state, period, source in rows:
        latest_by_lga.setdefault(
            lga.slug,
            _allocation(allocation, lga, state, period, source),
        )

    state = rows[0][2]
    records = sorted(latest_by_lga.values(), key=lambda item: item.local_government_name)
    return PublishedLgaStateResponse(
        state_name=state.name,
        state_code=state.code,
        state_slug=state.slug,
        local_government_count=len(records),
        local_governments=records,
        note=(
            "Only published, non-demo, human-verified OAGF Table IV local-government evidence is returned. "
            "No LGA amount is estimated from an aggregate."
        ),
    )


def published_lga_history(
    session: Session,
    *,
    state_code: str,
    local_government_slug: str,
) -> PublishedLgaDetailResponse | None:
    rows = list(
        session.execute(
            _published_statement()
            .where(
                State.code == state_code.upper(),
                LocalGovernment.slug == local_government_slug,
            )
            .order_by(
                ReportingPeriod.disbursement_month.desc(),
                ReportingPeriod.revenue_month.desc(),
            )
        ).tuples()
    )
    if not rows:
        return None

    allocations = [
        _allocation(allocation, lga, state, period, source)
        for allocation, lga, state, period, source in rows
    ]
    lga = rows[0][1]
    state = rows[0][2]
    return PublishedLgaDetailResponse(
        state_name=state.name,
        state_code=state.code,
        state_slug=state.slug,
        local_government_name=lga.official_name,
        local_government_slug=lga.slug,
        record_count=len(allocations),
        allocations=allocations,
        note=(
            "History contains only governed OAGF Table IV publications for this local government. "
            "Missing months remain missing."
        ),
    )
