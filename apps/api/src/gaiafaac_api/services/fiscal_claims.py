from __future__ import annotations

from urllib.parse import urlsplit

from sqlalchemy import select
from sqlalchemy.orm import Session, aliased

from gaiafaac_api.database.ledger_models import FiscalClaim
from gaiafaac_api.database.models import SourceDocument, State
from gaiafaac_api.fiscal_claim_schemas import (
    FiscalClaimEnvelope,
    FiscalClaimQuery,
    FiscalClaimSource,
    FiscalClaimSummary,
)
from gaiafaac_api.fiscal_ledger_schemas import JurisdictionIdentity, LedgerMeta
from gaiafaac_api.services.fiscal_ledger import METHODOLOGY_VERSION


def _public_url(value: str | None) -> str | None:
    if not value:
        return None
    parsed = urlsplit(value)
    return value if parsed.scheme in {"http", "https"} and parsed.netloc else None


def governed_claims(session: Session, query: FiscalClaimQuery) -> FiscalClaimEnvelope:
    successor = aliased(FiscalClaim)
    statement = (
        select(FiscalClaim, State, SourceDocument, successor.gaia_id)
        .join(State, FiscalClaim.state_id == State.id)
        .join(SourceDocument, FiscalClaim.source_document_id == SourceDocument.id)
        .outerjoin(successor, successor.supersedes_gaia_id == FiscalClaim.gaia_id)
    )

    if query.jurisdiction:
        state_code = query.jurisdiction.strip().upper().removeprefix("NG-")
        statement = statement.where(State.code == state_code)
    if query.fiscal_domain:
        statement = statement.where(
            FiscalClaim.object_type == query.fiscal_domain.strip().lower()
        )
    if query.fiscal_period:
        statement = statement.where(FiscalClaim.fiscal_period == query.fiscal_period.strip())
    if query.metric:
        statement = statement.where(FiscalClaim.metric == query.metric.strip().lower())
    if not query.include_superseded:
        statement = statement.where(successor.gaia_id.is_(None))

    rows = session.execute(
        statement.order_by(
            State.code,
            FiscalClaim.object_type,
            FiscalClaim.fiscal_period.desc(),
            FiscalClaim.metric,
            FiscalClaim.published_at.desc(),
        ).limit(query.limit)
    )

    data = [
        FiscalClaimSummary(
            gaia_id=claim.gaia_id,
            object_type=claim.object_type,
            jurisdiction=JurisdictionIdentity(
                code=f"NG-{state.code.upper()}",
                name=state.name,
            ),
            fiscal_period=claim.fiscal_period,
            metric=claim.metric,
            value=claim.value_text,
            unit=claim.unit,
            currency=claim.currency,
            evidence_status=claim.evidence_status,
            effective_at=claim.effective_at,
            published_at=claim.published_at,
            supersedes_gaia_id=claim.supersedes_gaia_id,
            superseded_by_gaia_id=superseded_by,
            source=FiscalClaimSource(
                publisher=source.source_organization,
                document_url=_public_url(source.source_url),
                document_sha256=claim.source_sha256,
                page=claim.source_page,
                table=claim.source_table,
            ),
        )
        for claim, state, source, superseded_by in rows
    ]

    return FiscalClaimEnvelope(
        data=data,
        evidence={
            "record_count": len(data),
            "meaning": (
                "Claims are immutable source-linked observations. Missing or unreported values "
                "remain textual or unavailable and are never converted to zero."
            ),
        },
        meta=LedgerMeta(
            schema_version="1.0.0",
            methodology_version=METHODOLOGY_VERSION,
        ),
    )
