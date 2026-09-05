from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.enums import EvidenceStatus, SourceStatus
from gaiafaac_api.database.ledger_models import FiscalClaim
from gaiafaac_api.database.models import SourceDocument, State
from gaiafaac_api.igr_schemas import GovernedIgrStatus

_PERIOD_RE = re.compile(r"^(?P<year>20\d{2})(?:Q(?P<quarter>[1-4]))?$")


@dataclass(frozen=True)
class GovernedIgrObservation:
    gaia_id: str
    state_name: str
    state_slug: str
    state_code: str
    fiscal_period: str
    value: str | None
    unit: str
    currency: str | None
    source_organization: str
    source_url: str | None
    source_sha256: str
    source_page: int | None
    source_table: str | None
    evidence_status: EvidenceStatus
    effective_at: datetime
    published_at: datetime


def fiscal_period_year(period: str) -> int | None:
    match = _PERIOD_RE.fullmatch(period.strip().upper())
    return int(match.group("year")) if match is not None else None


def fiscal_period_sort_key(period: str) -> tuple[int, int, str]:
    normalized = period.strip().upper()
    match = _PERIOD_RE.fullmatch(normalized)
    if match is None:
        return (0, 0, normalized)
    year = int(match.group("year"))
    quarter = match.group("quarter")
    # An annual observation covers the full year and therefore sorts after Q4.
    period_rank = 5 if quarter is None else int(quarter)
    return (year, period_rank, normalized)


def governed_igr_observations(
    session: Session,
    *,
    year: int | None = None,
    state_slug: str | None = None,
    publisher_fragment: str | None = None,
) -> list[GovernedIgrObservation]:
    """Return the canonical, current, verified IGR publication set.

    FiscalClaim is the publication ledger. StateIgrRecord remains a staging/review
    substrate and is deliberately not treated as public evidence here. A prior verified
    claim remains current until a verified, source-approved, non-demo descendant exists
    in the same publication scope. Partial intermediates therefore cannot hide the last
    verified publication or break a later verified revision chain.
    """

    statement = (
        select(FiscalClaim, State, SourceDocument)
        .join(State, FiscalClaim.state_id == State.id)
        .join(SourceDocument, FiscalClaim.source_document_id == SourceDocument.id)
        .where(
            FiscalClaim.object_type == "igr",
            FiscalClaim.metric == "igr",
        )
    )
    if state_slug is not None:
        statement = statement.where(State.slug == state_slug)

    rows = session.execute(
        statement.order_by(
            State.code,
            FiscalClaim.fiscal_period.desc(),
            FiscalClaim.published_at.desc(),
        )
    ).all()

    children: dict[str, list[str]] = defaultdict(list)
    row_by_gaia_id: dict[str, tuple[FiscalClaim, State, SourceDocument]] = {}
    for claim, state, source in rows:
        row_by_gaia_id[claim.gaia_id] = (claim, state, source)
        if claim.supersedes_gaia_id:
            children[claim.supersedes_gaia_id].append(claim.gaia_id)

    publisher_needle = publisher_fragment.strip().lower() if publisher_fragment else ""

    def eligible(row: tuple[FiscalClaim, State, SourceDocument]) -> bool:
        claim, _state, source = row
        if claim.evidence_status != EvidenceStatus.VERIFIED:
            return False
        if source.source_status != SourceStatus.APPROVED or source.is_demo:
            return False
        if publisher_needle and publisher_needle not in source.source_organization.lower():
            return False
        return True

    eligible_ids = {gaia_id for gaia_id, row in row_by_gaia_id.items() if eligible(row)}

    def has_eligible_descendant(gaia_id: str) -> bool:
        stack = list(children.get(gaia_id, ()))
        visited: set[str] = set()
        while stack:
            descendant_id = stack.pop()
            if descendant_id in visited:
                continue
            visited.add(descendant_id)
            if descendant_id in eligible_ids:
                return True
            stack.extend(children.get(descendant_id, ()))
        return False

    observations: list[GovernedIgrObservation] = []
    for gaia_id in eligible_ids:
        if has_eligible_descendant(gaia_id):
            continue
        claim, state, source = row_by_gaia_id[gaia_id]
        if year is not None and fiscal_period_year(claim.fiscal_period) != year:
            continue
        observations.append(
            GovernedIgrObservation(
                gaia_id=claim.gaia_id,
                state_name=state.name,
                state_slug=state.slug,
                state_code=state.code,
                fiscal_period=claim.fiscal_period,
                value=claim.value_text,
                unit=claim.unit,
                currency=claim.currency,
                source_organization=source.source_organization,
                source_url=source.source_url,
                source_sha256=claim.source_sha256,
                source_page=claim.source_page,
                source_table=claim.source_table,
                evidence_status=claim.evidence_status,
                effective_at=claim.effective_at,
                published_at=claim.published_at,
            )
        )

    observations.sort(
        key=lambda item: (
            item.state_code,
            fiscal_period_sort_key(item.fiscal_period),
            item.published_at,
            item.gaia_id,
        ),
        reverse=True,
    )
    return observations


def latest_governed_igr(
    session: Session,
    *,
    state_slug: str,
    publisher_fragment: str | None = None,
) -> GovernedIgrObservation | None:
    observations = governed_igr_observations(
        session,
        state_slug=state_slug,
        publisher_fragment=publisher_fragment,
    )
    if not observations:
        return None
    return max(
        observations,
        key=lambda item: (
            fiscal_period_sort_key(item.fiscal_period),
            item.published_at,
            item.gaia_id,
        ),
    )


def governed_igr_status(
    session: Session,
    *,
    publisher_fragment: str | None = None,
) -> GovernedIgrStatus:
    observations = governed_igr_observations(
        session,
        publisher_fragment=publisher_fragment,
    )
    latest = (
        max(
            observations,
            key=lambda item: (
                fiscal_period_sort_key(item.fiscal_period),
                item.published_at,
                item.gaia_id,
            ),
        )
        if observations
        else None
    )
    source_organizations = sorted({item.source_organization for item in observations})
    return GovernedIgrStatus(
        source_scope=publisher_fragment,
        is_live=bool(observations),
        published_record_count=len(observations),
        jurisdiction_count=len({item.state_code for item in observations}),
        latest_period=latest.fiscal_period if latest is not None else None,
        latest_published_at=latest.published_at if latest is not None else None,
        source_organizations=source_organizations,
        note=(
            "Status is derived only from current, non-demo, source-approved, verified IGR "
            "FiscalClaim records. Staged, legacy or unverified successor rows do not make "
            "a publication live or hide the last verified publication."
        ),
    )
