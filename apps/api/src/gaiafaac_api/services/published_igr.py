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


def _published_record(
    record: StateIgrRecord,
    state: State,
    source: SourceDocument,
) -> PublishedIgrRecord:
    return PublishedIgrRecord(
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


def _published_statement():
    return (
        select(StateIgrRecord, State, SourceDocument)
        .join(State, StateIgrRecord.state_id == State.id)
        .join(SourceDocument, StateIgrRecord.source_document_id == SourceDocument.id)
        .where(
            StateIgrRecord.is_published.is_(True),
            StateIgrRecord.is_demo.is_(False),
            StateIgrRecord.verification_status == VerificationStatus.HUMAN_VERIFIED,
            SourceDocument.is_demo.is_(False),
        )
    )


def published_igr(
    session: Session,
    *,
    year: int,
    state_slug: str | None = None,
) -> PublishedIgrResponse:
    statement = _published_statement().where(StateIgrRecord.fiscal_year == year)
    if state_slug is not None:
        statement = statement.where(State.slug == state_slug)
    statement = statement.order_by(State.name, StateIgrRecord.period_start, StateIgrRecord.period_end)

    records = [
        _published_record(record, state, source)
        for record, state, source in session.execute(statement).tuples()
    ]

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


def latest_published_igr(session: Session, *, state_slug: str) -> PublishedIgrRecord | None:
    row = session.execute(
        _published_statement()
        .where(State.slug == state_slug)
        .order_by(
            StateIgrRecord.period_end.desc(),
            StateIgrRecord.period_start.desc(),
            StateIgrRecord.created_at.desc(),
        )
        .limit(1)
    ).first()
    if row is None:
        return None
    record, state, source = row
    return _published_record(record, state, source)
