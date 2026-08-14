from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from gaiafaac_api.database.enums import EvidenceConflictStatus, EvidenceStatus
from gaiafaac_api.database.ledger_models import (
    ClaimRevision,
    EvidenceConflict,
    EvidenceConflictClaim,
    EvidenceSource,
    FiscalClaim,
)
from gaiafaac_api.database.models import SourceDocument, State
from gaiafaac_api.fiscal_ledger_schemas import (
    EvidenceConflictParticipant,
    EvidenceConflictResponse,
    EvidenceRevisionResponse,
    EvidenceSourceResponse,
)
from gaiafaac_api.ledger import canonical_sha256

TRUST_METHODOLOGY_VERSION = "1.1.0"
REVISION_MATERIALITY_PERCENT = Decimal("5.000000")


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _safe_public_url(value: str | None) -> str | None:
    if not value:
        return None
    from urllib.parse import urlsplit

    parsed = urlsplit(value)
    return value if parsed.scheme in {"http", "https"} and parsed.netloc else None


def register_evidence_source(
    session: Session,
    *,
    source: SourceDocument,
    state: State,
    fiscal_domain: str,
    verification_status: EvidenceStatus,
    source_type: str = "official_publication",
    reporting_cadence: str | None = None,
    canonical_url: str | None = None,
) -> EvidenceSource:
    existing = session.scalar(
        select(EvidenceSource).where(
            EvidenceSource.source_document_id == source.id,
            EvidenceSource.state_id == state.id,
            EvidenceSource.fiscal_domain == fiscal_domain,
        )
    )
    if existing is not None:
        return existing

    previous_source = None
    if source.supersedes_document_id is not None:
        previous_source = session.scalar(
            select(EvidenceSource).where(
                EvidenceSource.source_document_id == source.supersedes_document_id,
                EvidenceSource.state_id == state.id,
                EvidenceSource.fiscal_domain == fiscal_domain,
            )
        )
    record = EvidenceSource(
        id=uuid.uuid4(),
        source_document_id=source.id,
        state_id=state.id,
        publisher=source.source_organization,
        source_type=source_type,
        fiscal_domain=fiscal_domain,
        reporting_cadence=reporting_cadence,
        canonical_url=_safe_public_url(canonical_url),
        document_url=_safe_public_url(source.source_url),
        retrieved_at=source.downloaded_at,
        document_sha256=source.sha256,
        source_status=source.source_status.value,
        extraction_status=source.processing_status.value,
        verification_status=verification_status,
        last_checked_at=source.downloaded_at,
        revision_detected=source.supersedes_document_id is not None,
        supersedes_source_id=previous_source.id if previous_source else None,
    )
    session.add(record)
    session.flush()
    return record


def create_claim_revision(
    session: Session,
    *,
    previous_claim: FiscalClaim,
    revised_claim: FiscalClaim,
    source_revision: bool,
    detected_at: datetime,
    methodology_version: str = TRUST_METHODOLOGY_VERSION,
) -> ClaimRevision:
    existing = session.scalar(
        select(ClaimRevision).where(ClaimRevision.revised_claim_gaia_id == revised_claim.gaia_id)
    )
    if existing is not None:
        return existing

    value_delta = None
    value_change_percent = None
    material_change = None
    if previous_claim.value_text is not None and revised_claim.value_text is not None:
        previous_value = Decimal(previous_claim.value_text)
        revised_value = Decimal(revised_claim.value_text)
        value_delta = revised_value - previous_value
        if previous_value != 0:
            value_change_percent = (value_delta / abs(previous_value) * Decimal("100")).quantize(
                Decimal("0.000001"), rounding=ROUND_HALF_UP
            )
            material_change = abs(value_change_percent) >= REVISION_MATERIALITY_PERCENT

    revision = ClaimRevision(
        id=uuid.uuid4(),
        previous_claim_gaia_id=previous_claim.gaia_id,
        revised_claim_gaia_id=revised_claim.gaia_id,
        reason="source_revision" if source_revision else "claim_revision",
        value_delta=value_delta,
        value_delta_text=format(value_delta, "f") if value_delta is not None else None,
        value_change_percent=value_change_percent,
        value_change_percent_text=(
            format(value_change_percent, "f") if value_change_percent is not None else None
        ),
        material_change=material_change,
        source_revision=source_revision,
        detected_at=_utc(detected_at),
        methodology_version=methodology_version,
    )
    session.add(revision)
    session.flush()
    return revision


def record_evidence_conflict(
    session: Session,
    *,
    claim_gaia_ids: list[str],
    explanation: str,
    detected_at: datetime,
    methodology_version: str = TRUST_METHODOLOGY_VERSION,
) -> EvidenceConflict:
    identifiers = sorted(set(claim_gaia_ids))
    if len(identifiers) < 2:
        raise ValueError("An evidence conflict requires at least two distinct claims.")
    claims = list(
        session.scalars(
            select(FiscalClaim)
            .where(FiscalClaim.gaia_id.in_(identifiers))
            .order_by(FiscalClaim.gaia_id)
        )
    )
    if len(claims) != len(identifiers):
        raise ValueError("Every conflict participant must be an existing fiscal claim.")
    key = {
        (claim.state_id, claim.object_type, claim.fiscal_period, claim.metric) for claim in claims
    }
    if len(key) != 1:
        raise ValueError(
            "Conflicting claims must describe the same jurisdiction, period, and metric."
        )
    if (
        any(claim.value_text is None for claim in claims)
        or len({claim.value_text for claim in claims}) < 2
    ):
        raise ValueError("A conflict requires at least two different explicit claim values.")
    if not explanation.strip():
        raise ValueError("An evidence conflict requires a non-empty explanation.")

    state_id, object_type, fiscal_period, metric = next(iter(key))
    state = session.get(State, state_id)
    if state is None:
        raise RuntimeError("Conflict claim jurisdiction is missing.")
    digest = canonical_sha256(
        {
            "claims": identifiers,
            "jurisdiction": f"NG-{state.code.upper()}",
            "object_type": object_type,
            "fiscal_period": fiscal_period,
            "metric": metric,
        }
    )
    conflict_id = (
        f"GFC-NG-{state.code.upper()}-{fiscal_period.replace('-', '')}-{digest[:6].upper()}"
    )
    existing = session.get(EvidenceConflict, conflict_id)
    if existing is not None:
        return existing

    conflict = EvidenceConflict(
        conflict_id=conflict_id,
        state_id=state_id,
        object_type=object_type,
        fiscal_period=fiscal_period,
        metric=metric,
        status=EvidenceConflictStatus.UNRESOLVED,
        explanation=explanation.strip(),
        detected_at=_utc(detected_at),
        methodology_version=methodology_version,
    )
    session.add(conflict)
    session.flush()
    session.add_all(
        [
            EvidenceConflictClaim(
                id=uuid.uuid4(), conflict_id=conflict_id, claim_gaia_id=claim.gaia_id
            )
            for claim in claims
        ]
    )
    session.flush()
    return conflict


def claim_revisions(session: Session, gaia_id: str) -> list[EvidenceRevisionResponse]:
    revisions = list(
        session.scalars(
            select(ClaimRevision)
            .where(
                (ClaimRevision.previous_claim_gaia_id == gaia_id)
                | (ClaimRevision.revised_claim_gaia_id == gaia_id)
            )
            .order_by(ClaimRevision.detected_at, ClaimRevision.created_at)
        )
    )
    return [
        EvidenceRevisionResponse(
            previous_claim_gaia_id=item.previous_claim_gaia_id,
            revised_claim_gaia_id=item.revised_claim_gaia_id,
            reason=item.reason,
            value_delta=item.value_delta_text,
            value_change_percent=item.value_change_percent_text,
            material_change=item.material_change,
            source_revision=item.source_revision,
            detected_at=_utc(item.detected_at),
            methodology_version=item.methodology_version,
        )
        for item in revisions
    ]


def conflicts_for_claims(
    session: Session, claim_gaia_ids: list[str]
) -> list[EvidenceConflictResponse]:
    if not claim_gaia_ids:
        return []
    conflicts = list(
        session.scalars(
            select(EvidenceConflict)
            .join(
                EvidenceConflictClaim,
                EvidenceConflictClaim.conflict_id == EvidenceConflict.conflict_id,
            )
            .where(EvidenceConflictClaim.claim_gaia_id.in_(claim_gaia_ids))
            .distinct()
            .order_by(EvidenceConflict.detected_at, EvidenceConflict.conflict_id)
        )
    )
    responses = []
    for conflict in conflicts:
        claims = list(
            session.scalars(
                select(FiscalClaim)
                .join(
                    EvidenceConflictClaim,
                    EvidenceConflictClaim.claim_gaia_id == FiscalClaim.gaia_id,
                )
                .where(EvidenceConflictClaim.conflict_id == conflict.conflict_id)
                .order_by(FiscalClaim.gaia_id)
            )
        )
        participants = []
        for claim in claims:
            source = session.get(SourceDocument, claim.source_document_id)
            participants.append(
                EvidenceConflictParticipant(
                    claim_gaia_id=claim.gaia_id,
                    publisher=source.source_organization if source else "Unavailable",
                    value=claim.value_text,
                    unit=claim.unit,
                    currency=claim.currency,
                    source_sha256=claim.source_sha256,
                )
            )
        responses.append(
            EvidenceConflictResponse(
                conflict_id=conflict.conflict_id,
                status=conflict.status,
                object_type=conflict.object_type,
                fiscal_period=conflict.fiscal_period,
                metric=conflict.metric,
                explanation=conflict.explanation,
                detected_at=_utc(conflict.detected_at),
                participants=participants,
            )
        )
    return responses


def evidence_sources(
    session: Session,
    *,
    jurisdiction_code: str | None = None,
    publisher: str | None = None,
    fiscal_domain: str | None = None,
) -> list[EvidenceSourceResponse]:
    query = select(EvidenceSource, State).join(State, EvidenceSource.state_id == State.id)
    if jurisdiction_code:
        code = jurisdiction_code.strip().upper().removeprefix("NG-")
        query = query.where(State.code == code)
    if publisher:
        query = query.where(func.lower(EvidenceSource.publisher) == publisher.strip().lower())
    if fiscal_domain:
        query = query.where(EvidenceSource.fiscal_domain == fiscal_domain.strip().lower())
    rows = session.execute(
        query.order_by(
            EvidenceSource.publisher,
            State.code,
            EvidenceSource.fiscal_domain,
            EvidenceSource.revision_detected,
            EvidenceSource.created_at,
        ).limit(200)
    )
    return [
        EvidenceSourceResponse(
            source_id=str(source.id),
            publisher=source.publisher,
            source_type=source.source_type,
            jurisdiction=f"NG-{state.code.upper()}",
            fiscal_domain=source.fiscal_domain,
            reporting_cadence=source.reporting_cadence,
            canonical_url=source.canonical_url,
            document_url=source.document_url,
            retrieved_at=_utc(source.retrieved_at) if source.retrieved_at else None,
            document_sha256=source.document_sha256,
            source_status=source.source_status,
            extraction_status=source.extraction_status,
            verification_status=source.verification_status,
            last_checked_at=(_utc(source.last_checked_at) if source.last_checked_at else None),
            revision_detected=source.revision_detected,
            supersedes_source_id=(
                str(source.supersedes_source_id) if source.supersedes_source_id else None
            ),
        )
        for source, state in rows
    ]
