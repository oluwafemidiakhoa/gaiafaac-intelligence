from __future__ import annotations

import re
from datetime import date

from sqlalchemy.orm import Session

from gaiafaac_api.igr_schemas import (
    PublishedIgrRecord,
    PublishedIgrResponse,
    PublishedIgrSource,
)
from gaiafaac_api.services.canonical_igr import (
    GovernedIgrObservation,
    governed_igr_observations,
    latest_governed_igr,
)

_PERIOD_RE = re.compile(r"^(?P<year>20\d{2})(?:Q(?P<quarter>[1-4]))?$")


def _period_fields(period: str) -> tuple[int, str, int | None, date, date] | None:
    match = _PERIOD_RE.fullmatch(period.strip().upper())
    if match is None:
        return None
    year = int(match.group("year"))
    quarter_text = match.group("quarter")
    if quarter_text is None:
        return year, "annual", None, date(year, 1, 1), date(year, 12, 31)
    quarter = int(quarter_text)
    starts = {1: (1, 1), 2: (4, 1), 3: (7, 1), 4: (10, 1)}
    ends = {1: (3, 31), 2: (6, 30), 3: (9, 30), 4: (12, 31)}
    return (
        year,
        "quarterly",
        quarter,
        date(year, *starts[quarter]),
        date(year, *ends[quarter]),
    )


def _published_record(observation: GovernedIgrObservation) -> PublishedIgrRecord | None:
    fields = _period_fields(observation.fiscal_period)
    if fields is None or observation.value is None:
        return None
    fiscal_year, period_type, quarter, period_start, period_end = fields
    return PublishedIgrRecord(
        state_name=observation.state_name,
        state_slug=observation.state_slug,
        state_code=observation.state_code,
        fiscal_year=fiscal_year,
        period_type=period_type,
        quarter=quarter,
        period_start=period_start,
        period_end=period_end,
        igr_amount=observation.value,
        reported_unit=observation.currency or observation.unit,
        source_page=observation.source_page,
        source_table=observation.source_table,
        verification_status=observation.evidence_status.value,
        source=PublishedIgrSource(
            organization=observation.source_organization,
            source_url=observation.source_url,
            sha256=observation.source_sha256,
            publication_date=observation.published_at.date(),
        ),
    )


def published_igr(
    session: Session,
    *,
    year: int,
    state_slug: str | None = None,
) -> PublishedIgrResponse:
    observations = governed_igr_observations(session, year=year, state_slug=state_slug)
    records = [
        record
        for observation in observations
        if (record := _published_record(observation)) is not None
    ]
    records.sort(key=lambda item: (item.state_name, item.period_start, item.period_end))
    return PublishedIgrResponse(
        year=year,
        state_slug=state_slug,
        record_count=len(records),
        records=records,
        note=(
            "IGR records come from the canonical governed FiscalClaim publication ledger only: "
            "current, source-approved, non-demo and verified claims. Staged or legacy IGR rows "
            "are not treated as published evidence, and missing periods are never inferred."
        ),
    )


def latest_published_igr(session: Session, *, state_slug: str) -> PublishedIgrRecord | None:
    observation = latest_governed_igr(session, state_slug=state_slug)
    return _published_record(observation) if observation is not None else None
