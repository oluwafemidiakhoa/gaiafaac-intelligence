from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.ledger_models import FiscalClaim
from gaiafaac_api.database.models import SourceDocument, State
from gaiafaac_api.fiscal_ledger_schemas import JurisdictionIdentity, LedgerMeta
from gaiafaac_api.temporal_schemas import (
    TemporalFiscalClaim,
    TemporalFiscalSnapshotData,
    TemporalFiscalSnapshotEnvelope,
)

TEMPORAL_SCHEMA_VERSION = "1.0.0"
TEMPORAL_METHODOLOGY_VERSION = "1.0.0"


def _utc(value: datetime, *, field: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must include a timezone.")
    return value.astimezone(UTC)


def _stored_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def temporal_fiscal_snapshot(
    session: Session,
    *,
    jurisdiction_code: str,
    effective_as_of: datetime,
    known_as_of: datetime,
) -> TemporalFiscalSnapshotEnvelope | None:
    """Return the current claim set under explicit effective-time and knowledge-time cutoffs."""

    effective_cutoff = _utc(effective_as_of, field="effective_as_of")
    knowledge_cutoff = _utc(known_as_of, field="known_as_of")
    code = jurisdiction_code.strip().upper().removeprefix("NG-")
    state = session.scalar(select(State).where(State.code == code))
    if state is None:
        return None

    rows = session.execute(
        select(FiscalClaim, SourceDocument)
        .join(SourceDocument, FiscalClaim.source_document_id == SourceDocument.id)
        .where(
            FiscalClaim.state_id == state.id,
            FiscalClaim.effective_at <= effective_cutoff,
            FiscalClaim.published_at <= knowledge_cutoff,
        )
        .order_by(
            FiscalClaim.object_type,
            FiscalClaim.metric,
            FiscalClaim.fiscal_period,
            FiscalClaim.published_at,
            FiscalClaim.gaia_id,
        )
    ).all()

    candidate_ids = {claim.gaia_id for claim, _source in rows}
    superseded_ids = {
        claim.supersedes_gaia_id
        for claim, _source in rows
        if claim.supersedes_gaia_id in candidate_ids
    }
    current_rows = [
        (claim, source)
        for claim, source in rows
        if claim.gaia_id not in superseded_ids
    ]

    domains: dict[str, list[TemporalFiscalClaim]] = {}
    for claim, source in current_rows:
        domains.setdefault(claim.object_type, []).append(
            TemporalFiscalClaim(
                gaia_id=claim.gaia_id,
                object_type=claim.object_type,
                fiscal_period=claim.fiscal_period,
                metric=claim.metric,
                value=claim.value_text,
                unit=claim.unit,
                currency=claim.currency,
                evidence_status=claim.evidence_status,
                source_sha256=claim.source_sha256,
                source_publisher=source.source_organization,
                source_url=source.source_url,
                effective_at=_stored_utc(claim.effective_at),
                published_at=_stored_utc(claim.published_at),
                supersedes_gaia_id=claim.supersedes_gaia_id,
            )
        )
    return TemporalFiscalSnapshotEnvelope(
        data=TemporalFiscalSnapshotData(
            jurisdiction=JurisdictionIdentity(code=f"NG-{state.code.upper()}", name=state.name),
            effective_as_of=effective_cutoff,
            known_as_of=knowledge_cutoff,
            domains=domains,
            claim_count=sum(len(items) for items in domains.values()),
        ),
        evidence={
            "meaning": (
                "effective_as_of limits when a fiscal fact applies; known_as_of limits when Gaia "
                "had published evidence for it. Superseded claims remain retained but are omitted "
                "from the current-as-known snapshot once their replacement was known."
            ),
            "history_rewritten": False,
        },
        meta=LedgerMeta(
            schema_version=TEMPORAL_SCHEMA_VERSION,
            methodology_version=TEMPORAL_METHODOLOGY_VERSION,
        ),
    )
