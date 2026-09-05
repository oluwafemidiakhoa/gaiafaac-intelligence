from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, aliased

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
    substrate and is deliberately not treated as public evidence here.
    """

    successor = aliased(FiscalClaim)
    statement = (
        select(FiscalClaim, State, SourceDocument, successor.gaia_id)
        .join(State, FiscalClaim.state_id == State.id)
        .join(SourceDocument, FiscalClaim.source_document_id == SourceDocument.id)
        .outerjoin(successor, successor.supersedes_gaia_id == FiscalClaim.gaia_id)
        .where(
            FiscalClaim.object_type == "igr",
            FiscalClaim.metric == "igr",
            FiscalClaim.evidence_status == EvidenceStatus.VERIFIED,
            SourceDocument.source_status == SourceStatus.APPROVED,
            SourceDocument.is_demo.is_(False),
            successor.gaia_id.is_(None),
        )
    )
    if state_slug is not None:
        statement = statement.where(State.slug == state_slug)
    if publisher_fragment is not None:
        needle = publisher_fragment.strip()
        if needle:
            statement = statement.where(SourceDocument.source_organization.ilike(f"%{needle}%"))

    rows = session.execute(
        statement.order_by(
            State.code,
            FiscalClaim.fiscal_period.desc(),
            FiscalClaim.published_at.desc(),
        )
    ).all()

    observations = [
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
        for claim, state, source, _superseded_by in rows
        if year is None or fiscal_period_year(claim.fiscal_period) == year
    ]
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
            "FiscalClaim records. Staged or legacy IGR rows do not make a publication live."
        ),
    )
