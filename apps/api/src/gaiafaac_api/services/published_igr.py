from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.enums import VerificationStatus
from gaiafaac_api.database.igr_models import StateIgrRecord
from gaiafaac_api.database.models import SourceDocument, State
from gaiafaac_api.igr_schemas import (
    PublishedIgrRecord,
    PublishedIgrResponse,
    PublishedIgrSource,
)


def published_igr(
    session: Session,
    *,
    year: int,
    state_slug: str | None = None,
) -> PublishedIgrResponse:
    statement = (
        select(StateIgrRecord, State, SourceDocument)
        .join(State, StateIgrRecord.state_id == State.id)
        .join(SourceDocument, StateIgrRecord.source_document_id == SourceDocument.id)
        .where(
            StateIgrRecord.fiscal_year == year,
            StateIgrRecord.is_published.is_(True),
            StateIgrRecord.is_demo.is_(False),
            StateIgrRecord.verification_status == VerificationStatus.HUMAN_VERIFIED,
            SourceDocument.is_demo.is_(False),
        )
        .order_by(State.name, StateIgrRecord.period_start, StateIgrRecord.period_end)
    )
    if state_slug is not None:
        statement = statement.where(State.slug == state_slug)

    records: list[PublishedIgrRecord] = []
    for record, state, source in session.execute(statement).tuples():
        records.append(
            PublishedIgrRecord(
                state_name=state.name,
                state_slug=state.slug,
                state_code=state.code,
                fiscal_year=record.fiscal_year,
                period_type=record.period_type.value,
                quarter=record.quarter,
                period_start=record.period_start,
                period_end=record.period_end,
                igr_amount=format(record.igr_amount, ".2f"),
                reported_unit=record.reported_unit.value,
                source_page=record.source_page,
                source_table=record.source_table,
                verification_status=record.verification_status.value,
                source=PublishedIgrSource(
                    organization=source.source_organization,
                    source_url=source.source_url,
                    sha256=source.sha256,
                    publication_date=record.publication_date or source.publication_date,
                ),
            )
        )

    return PublishedIgrResponse(
        year=year,
        state_slug=state_slug,
        record_count=len(records),
        records=records,
        note=(
            "IGR records are returned only when they are published, non-demo, and human-verified. "
            "No missing fiscal periods or values are inferred."
        ),
    )
