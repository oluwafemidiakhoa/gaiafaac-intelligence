from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, time
from decimal import Decimal
from urllib.parse import urlsplit

from sqlalchemy import exists, select
from sqlalchemy.orm import Session, aliased

from gaiafaac_api.database.enums import EvidenceStatus, SourceStatus, VerificationStatus
from gaiafaac_api.database.ledger_models import (
    EvidenceManifest,
    EvidenceVerification,
    FiscalClaim,
    FiscalProof,
    FiscalState,
)
from gaiafaac_api.database.models import ReportingPeriod, SourceDocument, State, StateAllocation
from gaiafaac_api.fiscal_ledger_schemas import (
    EvidenceConflictResponse,
    EvidenceManifestResponse,
    FiscalProofData,
    FiscalProofEnvelope,
    FiscalProofEvidence,
    FiscalStateData,
    FiscalStateEnvelope,
    FiscalStateEvidence,
    JurisdictionIdentity,
    LedgerMeta,
    ProofSource,
    ProofVerification,
)
from gaiafaac_api.ledger import (
    CANONICALIZATION_VERSION,
    GaiaObjectType,
    calculate_evidence_coverage,
    calculate_evidence_integrity,
    canonical_sha256,
    canonicalize,
    fiscal_state_id,
    gaia_object_id,
)
from gaiafaac_api.services.fiscal_trust import (
    claim_revisions,
    conflicts_for_claims,
    create_claim_revision,
    register_evidence_source,
)

PROOF_SCHEMA_VERSION = "1.0.0"
STATE_SCHEMA_VERSION = "1.1.0"
PROOF_METHODOLOGY_VERSION = "1.0.0"
STATE_METHODOLOGY_VERSION = "1.1.0"
METHODOLOGY_VERSION = STATE_METHODOLOGY_VERSION
PROOF_MANIFEST_VERSION = "gaia-fiscal-proof-manifest-v1"
STATE_MANIFEST_VERSION = "gaia-fiscal-state-manifest-v2"
FISCAL_DOMAINS = (
    "faac",
    "igr",
    "debt",
    "debt_service",
    "budget",
    "expenditure",
    "liabilities",
)


def _money(value: Decimal | None) -> str | None:
    return format(value, ".2f") if value is not None else None


def _jurisdiction_code(state: State) -> str:
    return f"NG-{state.code.upper()}"


def _public_source_url(value: str | None) -> str | None:
    if value is None:
        return None
    parsed = urlsplit(value)
    return value if parsed.scheme in {"http", "https"} and parsed.netloc else None


def _utc_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    # SQLite removes timezone metadata in tests; the durable schema contract is UTC.
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _published_at(allocation: StateAllocation, period: ReportingPeriod) -> datetime:
    published_at = allocation.published_at or period.published_at
    if published_at is None:
        raise ValueError("Published ledger objects require an explicit publication timestamp.")
    normalized = _utc_datetime(published_at)
    assert normalized is not None
    return normalized


def _effective_at(period: ReportingPeriod) -> datetime:
    return datetime.combine(period.revenue_month, time.min, tzinfo=UTC)


def _reconciliation(allocation: StateAllocation) -> tuple[str, bool | None, str | None]:
    if (
        allocation.gross_total is None
        or allocation.total_deductions is None
        or allocation.net_allocation is None
    ):
        return "not_applicable", None, None
    delta = allocation.gross_total - allocation.total_deductions - allocation.net_allocation
    reconciled = abs(delta) <= Decimal("0.01")
    return ("reconciled" if reconciled else "mismatch"), reconciled, _money(delta)


def _manifest_response(manifest: EvidenceManifest) -> EvidenceManifestResponse:
    return EvidenceManifestResponse(
        manifest_version=manifest.manifest_version,
        schema_version=manifest.schema_version,
        canonicalization_version=manifest.canonicalization_version,
        hash_algorithm="sha256",
        payload_sha256=manifest.payload_sha256,
        payload=manifest.payload,
    )


def publish_faac_claim_proof(
    session: Session,
    *,
    allocation_id: uuid.UUID,
    methodology_version: str = PROOF_METHODOLOGY_VERSION,
    extraction_method: str = "governed_pipeline",
) -> FiscalProof:
    """Materialize an immutable proof from an already-published FAAC allocation."""

    row = session.execute(
        select(StateAllocation, State, ReportingPeriod, SourceDocument)
        .join(State, StateAllocation.state_id == State.id)
        .join(ReportingPeriod, StateAllocation.reporting_period_id == ReportingPeriod.id)
        .join(SourceDocument, StateAllocation.source_document_id == SourceDocument.id)
        .where(StateAllocation.id == allocation_id)
    ).first()
    if row is None:
        raise LookupError("State allocation does not exist.")
    allocation, state, period, source = row
    if allocation.is_demo or period.is_demo or source.is_demo:
        raise ValueError("Demo records cannot be published to the Gaia Fiscal Ledger.")
    if not allocation.is_published or not period.is_published:
        raise ValueError("Only published allocations can produce a Fiscal Proof.")

    published_at = _published_at(allocation, period)
    effective_at = _effective_at(period)
    reconciliation_status, reconciled, reconciliation_delta = _reconciliation(allocation)
    source_verified = source.source_status is SourceStatus.APPROVED
    human_reviewed = (
        allocation.verification_status is VerificationStatus.HUMAN_VERIFIED
        and period.verification_status is VerificationStatus.HUMAN_VERIFIED
    )
    evidence_status = (
        EvidenceStatus.VERIFIED
        if source_verified and human_reviewed and reconciled is not False
        else EvidenceStatus.PARTIAL
    )
    jurisdiction = _jurisdiction_code(state)
    fiscal_period = period.revenue_month.strftime("%Y-%m")
    identity_payload = {
        "object_type": "faac",
        "jurisdiction": jurisdiction,
        "fiscal_period": fiscal_period,
        "metric": "faac_net_allocation",
        "value": _money(allocation.net_allocation),
        "unit": allocation.reported_unit.value,
        "currency": "NGN",
        "source_sha256": source.sha256,
        "methodology_version": methodology_version,
    }
    identity_hash = canonical_sha256(identity_payload)
    gaia_id = gaia_object_id(
        GaiaObjectType.FAAC,
        jurisdiction=jurisdiction,
        fiscal_period=fiscal_period,
        integrity_hash=identity_hash,
    )
    existing = session.scalar(select(FiscalProof).where(FiscalProof.gaia_id == gaia_id))
    if existing is not None:
        return existing

    previous_claim = session.scalar(
        select(FiscalClaim)
        .where(
            FiscalClaim.state_id == state.id,
            FiscalClaim.object_type == "faac",
            FiscalClaim.fiscal_period == fiscal_period,
            FiscalClaim.metric == "faac_net_allocation",
        )
        .order_by(FiscalClaim.published_at.desc())
        .limit(1)
    )
    claim = FiscalClaim(
        gaia_id=gaia_id,
        object_type="faac",
        state_id=state.id,
        fiscal_period=fiscal_period,
        metric="faac_net_allocation",
        value=allocation.net_allocation,
        value_text=_money(allocation.net_allocation),
        unit=allocation.reported_unit.value,
        currency="NGN",
        source_document_id=source.id,
        source_sha256=source.sha256,
        source_page=None,
        source_table=None,
        extraction_method=extraction_method,
        evidence_status=evidence_status,
        methodology_version=methodology_version,
        supersedes_gaia_id=previous_claim.gaia_id if previous_claim else None,
        effective_at=effective_at,
        published_at=published_at,
    )
    verification = EvidenceVerification(
        claim_gaia_id=gaia_id,
        status=evidence_status,
        source_verified=source_verified,
        reconciled=reconciled,
        human_reviewed=human_reviewed,
        published=True,
        verified_at=_utc_datetime(allocation.reviewed_at),
        methodology_version=methodology_version,
        notes=(
            "Integrity verifies Gaia's artifact and source lineage; it does not certify "
            "the originating government's claim as true."
        ),
    )
    payload = canonicalize(
        {
            "gaia_id": gaia_id,
            "schema_version": PROOF_SCHEMA_VERSION,
            "object_type": "faac",
            "jurisdiction": {
                "country": "NG",
                "code": jurisdiction,
                "name": state.name,
            },
            "fiscal_period": fiscal_period,
            "dates": {
                "revenue_month": period.revenue_month,
                "faac_meeting_date": period.faac_meeting_date,
                "publication_date": period.publication_date,
            },
            "metric": "faac_net_allocation",
            "value": _money(allocation.net_allocation),
            "unit": allocation.reported_unit.value,
            "currency": "NGN",
            "source": {
                "publisher": source.source_organization,
                "document_url": _public_source_url(source.source_url),
                "document_sha256": source.sha256,
                "publication_date": source.publication_date,
                "page": None,
                "table": None,
            },
            "verification": {
                "status": evidence_status,
                "source_verified": source_verified,
                "reconciliation_status": reconciliation_status,
                "reconciled": reconciled,
                "reconciliation_delta": reconciliation_delta,
                "human_reviewed": human_reviewed,
                "published": True,
                "verified_at": _utc_datetime(allocation.reviewed_at),
            },
            "methodology_version": methodology_version,
            "effective_at": effective_at,
            "published_at": published_at,
            "supersedes_gaia_id": claim.supersedes_gaia_id,
        }
    )
    payload_hash = canonical_sha256(payload)
    manifest = EvidenceManifest(
        id=uuid.uuid4(),
        subject_gaia_id=gaia_id,
        manifest_version=PROOF_MANIFEST_VERSION,
        schema_version=PROOF_SCHEMA_VERSION,
        canonicalization_version=CANONICALIZATION_VERSION,
        hash_algorithm="sha256",
        payload_sha256=payload_hash,
        payload=payload,
    )
    proof = FiscalProof(
        gaia_id=gaia_id,
        manifest_id=manifest.id,
        schema_version=PROOF_SCHEMA_VERSION,
        methodology_version=methodology_version,
        integrity_hash=payload_hash,
        previous_proof_gaia_id=previous_claim.gaia_id if previous_claim else None,
        published_at=published_at,
    )
    session.add_all([claim, verification, manifest, proof])
    session.flush()
    register_evidence_source(
        session,
        source=source,
        state=state,
        fiscal_domain="faac",
        verification_status=evidence_status,
        reporting_cadence="monthly",
    )
    if previous_claim is not None:
        create_claim_revision(
            session,
            previous_claim=previous_claim,
            revised_claim=claim,
            source_revision=source.supersedes_document_id == previous_claim.source_document_id,
            detected_at=published_at,
        )
    return proof


def get_fiscal_proof_by_gaia_id(session: Session, gaia_id: str) -> FiscalProofEnvelope | None:
    row = session.execute(
        select(
            FiscalProof, FiscalClaim, EvidenceVerification, EvidenceManifest, State, SourceDocument
        )
        .join(FiscalClaim, FiscalProof.gaia_id == FiscalClaim.gaia_id)
        .join(EvidenceVerification, EvidenceVerification.claim_gaia_id == FiscalClaim.gaia_id)
        .join(EvidenceManifest, FiscalProof.manifest_id == EvidenceManifest.id)
        .join(State, FiscalClaim.state_id == State.id)
        .join(SourceDocument, FiscalClaim.source_document_id == SourceDocument.id)
        .where(FiscalProof.gaia_id == gaia_id)
    ).first()
    if row is None:
        return None
    proof, claim, verification, manifest, state, source = row
    superseded_by = session.scalar(
        select(FiscalClaim.gaia_id)
        .where(FiscalClaim.supersedes_gaia_id == claim.gaia_id)
        .order_by(FiscalClaim.published_at.desc())
        .limit(1)
    )
    return FiscalProofEnvelope(
        data=FiscalProofData(
            gaia_id=claim.gaia_id,
            object_type=claim.object_type,
            jurisdiction=JurisdictionIdentity(code=_jurisdiction_code(state), name=state.name),
            fiscal_period=claim.fiscal_period,
            metric=claim.metric,
            value=claim.value_text,
            unit=claim.unit,
            currency=claim.currency,
            effective_at=claim.effective_at,
            methodology_version=claim.methodology_version,
            supersedes_gaia_id=claim.supersedes_gaia_id,
            superseded_by_gaia_id=superseded_by,
            source=ProofSource(
                publisher=source.source_organization,
                document_url=_public_source_url(source.source_url),
                document_sha256=source.sha256,
                publication_date=(
                    source.publication_date.isoformat() if source.publication_date else None
                ),
                page=claim.source_page,
                table=claim.source_table,
            ),
            verification=ProofVerification(
                status=verification.status,
                source_verified=verification.source_verified,
                reconciled=verification.reconciled,
                human_reviewed=verification.human_reviewed,
                published=verification.published,
                verified_at=_utc_datetime(verification.verified_at),
                note=verification.notes or "",
            ),
            published_at=proof.published_at,
        ),
        evidence=FiscalProofEvidence(
            manifest=_manifest_response(manifest),
            disclaimer=(
                "This proof establishes the integrity and recorded provenance of Gaia's artifact. "
                "It does not independently prove that the originating government data is true."
            ),
            revisions=claim_revisions(session, claim.gaia_id),
            conflicts=conflicts_for_claims(session, [claim.gaia_id]),
        ),
        meta=LedgerMeta(
            schema_version=proof.schema_version,
            methodology_version=proof.methodology_version,
        ),
    )


def publish_fiscal_state(
    session: Session,
    *,
    jurisdiction_code: str,
    effective_at: datetime,
    fiscal_period: str,
    claim_gaia_ids: list[str],
    methodology_version: str = STATE_METHODOLOGY_VERSION,
) -> FiscalState:
    canonical_code = jurisdiction_code.strip().upper()
    state_code = canonical_code.removeprefix("NG-")
    state = session.scalar(select(State).where(State.code == state_code))
    if state is None:
        raise LookupError("Jurisdiction does not exist.")
    if effective_at.tzinfo is None or effective_at.utcoffset() is None:
        raise ValueError("Fiscal State effective_at must be timezone-aware.")
    effective_at = effective_at.astimezone(UTC)

    claims = list(
        session.scalars(
            select(FiscalClaim)
            .where(FiscalClaim.gaia_id.in_(claim_gaia_ids))
            .order_by(FiscalClaim.object_type, FiscalClaim.fiscal_period, FiscalClaim.gaia_id)
        )
    )
    if len(claims) != len(set(claim_gaia_ids)):
        raise ValueError("Every Fiscal State claim must exist exactly once.")
    if any(claim.state_id != state.id for claim in claims):
        raise ValueError("Fiscal State claims must belong to the requested jurisdiction.")

    domains: dict[str, dict[str, object]] = {
        domain: {"status": EvidenceStatus.UNAVAILABLE.value, "claims": []}
        for domain in FISCAL_DOMAINS
    }
    for claim in claims:
        domain = domains.setdefault(
            claim.object_type,
            {"status": EvidenceStatus.UNAVAILABLE.value, "claims": []},
        )
        domain_claims = domain["claims"]
        assert isinstance(domain_claims, list)
        domain_claims.append(
            {
                "gaia_id": claim.gaia_id,
                "metric": claim.metric,
                "fiscal_period": claim.fiscal_period,
                "value": claim.value_text,
                "unit": claim.unit,
                "currency": claim.currency,
                "status": claim.evidence_status.value,
            }
        )
    for domain in domains.values():
        domain_claims = domain["claims"]
        assert isinstance(domain_claims, list)
        if domain_claims:
            domain["status"] = (
                EvidenceStatus.VERIFIED.value
                if all(item["status"] == EvidenceStatus.VERIFIED.value for item in domain_claims)
                else EvidenceStatus.PARTIAL.value
            )

    conflicts = conflicts_for_claims(session, [claim.gaia_id for claim in claims])
    unresolved_conflicts = [
        conflict for conflict in conflicts if conflict.status.value == "unresolved"
    ]
    conflicting_domains = {conflict.object_type for conflict in unresolved_conflicts}
    for domain_name in conflicting_domains:
        if domain_name in domains:
            domains[domain_name]["status"] = EvidenceStatus.CONFLICTING.value

    sources = []
    seen_sources: set[str] = set()
    for claim in claims:
        if claim.source_sha256 in seen_sources:
            continue
        seen_sources.add(claim.source_sha256)
        source = session.get(SourceDocument, claim.source_document_id)
        if source is not None:
            sources.append(
                {
                    "publisher": source.source_organization,
                    "document_url": _public_source_url(source.source_url),
                    "document_sha256": source.sha256,
                    "publication_date": (
                        source.publication_date.isoformat() if source.publication_date else None
                    ),
                }
            )
    sources.sort(key=lambda item: (str(item["publisher"]), str(item["document_sha256"])))

    previous = session.scalar(
        select(FiscalState)
        .where(FiscalState.state_id == state.id, FiscalState.effective_at < effective_at)
        .order_by(FiscalState.effective_at.desc(), FiscalState.created_at.desc())
        .limit(1)
    )
    coverage = calculate_evidence_coverage(domains)
    verifications = list(
        session.scalars(
            select(EvidenceVerification).where(
                EvidenceVerification.claim_gaia_id.in_([claim.gaia_id for claim in claims])
            )
        )
    )
    evidence_integrity = calculate_evidence_integrity(
        claims=claims,
        verifications=verifications,
        domains=domains,
        coverage=coverage,
        sources=sources,
        unresolved_conflict_count=len(unresolved_conflicts),
        effective_at=effective_at,
    )
    ledger_status = (
        EvidenceStatus.CONFLICTING
        if unresolved_conflicts
        else (EvidenceStatus.PARTIAL if claims else EvidenceStatus.UNAVAILABLE)
    )
    state_seed = {
        "jurisdiction": canonical_code,
        "effective_at": effective_at,
        "fiscal_period": fiscal_period,
        "domains": domains,
        "sources": sources,
        "evidence_coverage": coverage,
        "evidence_integrity": evidence_integrity,
        "conflicts": [conflict.model_dump(mode="json") for conflict in conflicts],
        "previous_state_id": previous.fiscal_state_id if previous else None,
        "methodology_version": methodology_version,
    }
    identity_hash = canonical_sha256(state_seed)
    state_gaia_id = fiscal_state_id(
        jurisdiction=canonical_code,
        effective_at=effective_at,
        integrity_hash=identity_hash,
    )
    existing = session.get(FiscalState, state_gaia_id)
    if existing is not None:
        return existing
    payload = canonicalize(
        {
            "fiscal_state_id": state_gaia_id,
            "schema_version": STATE_SCHEMA_VERSION,
            "jurisdiction": {"country": "NG", "code": canonical_code, "name": state.name},
            "effective_at": effective_at,
            "fiscal_period": fiscal_period,
            "ledger_status": ledger_status,
            "evidence_coverage": coverage,
            "domains": domains,
            "evidence_integrity": evidence_integrity,
            "conflicts": [conflict.model_dump(mode="json") for conflict in conflicts],
            "events": [],
            "sources": sources,
            "previous_state_id": previous.fiscal_state_id if previous else None,
            "methodology_version": methodology_version,
            "published_at": effective_at,
        }
    )
    payload_hash = canonical_sha256(payload)
    manifest = EvidenceManifest(
        id=uuid.uuid4(),
        subject_gaia_id=state_gaia_id,
        manifest_version=STATE_MANIFEST_VERSION,
        schema_version=STATE_SCHEMA_VERSION,
        canonicalization_version=CANONICALIZATION_VERSION,
        hash_algorithm="sha256",
        payload_sha256=payload_hash,
        payload=payload,
    )
    fiscal_state = FiscalState(
        fiscal_state_id=state_gaia_id,
        state_id=state.id,
        effective_at=effective_at,
        fiscal_period=fiscal_period,
        ledger_status=ledger_status,
        evidence_coverage=Decimal(str(coverage["score"])),
        evidence_coverage_status=str(coverage["status"]),
        domains=domains,
        evidence_integrity=evidence_integrity,
        events=[],
        sources=sources,
        manifest_id=manifest.id,
        integrity_hash=payload_hash,
        schema_version=STATE_SCHEMA_VERSION,
        methodology_version=methodology_version,
        previous_state_id=previous.fiscal_state_id if previous else None,
        published_at=effective_at,
    )
    session.add_all([manifest, fiscal_state])
    session.flush()
    return fiscal_state


def publish_current_fiscal_state(
    session: Session,
    *,
    state_id: uuid.UUID,
    effective_at: datetime,
    fiscal_period: str,
    methodology_version: str = STATE_METHODOLOGY_VERSION,
) -> FiscalState:
    state = session.get(State, state_id)
    if state is None:
        raise LookupError("Jurisdiction does not exist.")
    superseding_claim = aliased(FiscalClaim)
    claim_ids = list(
        session.scalars(
            select(FiscalClaim.gaia_id)
            .where(
                FiscalClaim.state_id == state_id,
                FiscalClaim.published_at <= effective_at,
                ~exists(
                    select(1).where(
                        superseding_claim.supersedes_gaia_id == FiscalClaim.gaia_id,
                        superseding_claim.published_at <= effective_at,
                    )
                ),
            )
            .order_by(FiscalClaim.object_type, FiscalClaim.fiscal_period, FiscalClaim.gaia_id)
        )
    )
    return publish_fiscal_state(
        session,
        jurisdiction_code=_jurisdiction_code(state),
        effective_at=effective_at,
        fiscal_period=fiscal_period,
        claim_gaia_ids=claim_ids,
        methodology_version=methodology_version,
    )


def _fiscal_state_envelope(session: Session, fiscal_state: FiscalState) -> FiscalStateEnvelope:
    state = session.get(State, fiscal_state.state_id)
    manifest = session.get(EvidenceManifest, fiscal_state.manifest_id)
    if state is None or manifest is None:
        raise RuntimeError("Fiscal State lineage is incomplete.")
    stored_conflicts = manifest.payload.get("conflicts", [])
    if not isinstance(stored_conflicts, list):
        raise RuntimeError("Fiscal State conflict evidence is malformed.")
    return FiscalStateEnvelope(
        data=FiscalStateData(
            fiscal_state_id=fiscal_state.fiscal_state_id,
            jurisdiction=JurisdictionIdentity(code=_jurisdiction_code(state), name=state.name),
            effective_at=fiscal_state.effective_at,
            fiscal_period=fiscal_state.fiscal_period,
            ledger_status=fiscal_state.ledger_status,
            evidence_coverage=(
                format(fiscal_state.evidence_coverage, "f")
                if fiscal_state.evidence_coverage is not None
                else None
            ),
            evidence_coverage_status=fiscal_state.evidence_coverage_status,
            domains=fiscal_state.domains,
            evidence_integrity=fiscal_state.evidence_integrity,
            events=fiscal_state.events,
            sources=fiscal_state.sources,
            previous_state_id=fiscal_state.previous_state_id,
            published_at=fiscal_state.published_at,
        ),
        evidence=FiscalStateEvidence(
            manifest=_manifest_response(manifest),
            conflicts=[
                EvidenceConflictResponse.model_validate(conflict) for conflict in stored_conflicts
            ],
        ),
        meta=LedgerMeta(
            schema_version=fiscal_state.schema_version,
            methodology_version=fiscal_state.methodology_version,
        ),
    )


def get_jurisdiction_fiscal_state(
    session: Session, *, jurisdiction_code: str, as_of: date | datetime | None = None
) -> FiscalStateEnvelope | None:
    state_code = jurisdiction_code.strip().upper().removeprefix("NG-")
    state = session.scalar(select(State).where(State.code == state_code))
    if state is None:
        return None
    query = select(FiscalState).where(FiscalState.state_id == state.id)
    if as_of is not None:
        if isinstance(as_of, datetime):
            if as_of.tzinfo is None or as_of.utcoffset() is None:
                raise ValueError("Datetime as_of values must include a timezone.")
            cutoff = as_of.astimezone(UTC)
        else:
            cutoff = datetime.combine(as_of, time.max, tzinfo=UTC)
        query = query.where(FiscalState.effective_at <= cutoff)
    fiscal_state = session.scalar(
        query.order_by(FiscalState.effective_at.desc(), FiscalState.created_at.desc()).limit(1)
    )
    return _fiscal_state_envelope(session, fiscal_state) if fiscal_state else None


def get_fiscal_state_by_id(
    session: Session, *, fiscal_state_gaia_id: str
) -> FiscalStateEnvelope | None:
    fiscal_state = session.get(FiscalState, fiscal_state_gaia_id)
    return _fiscal_state_envelope(session, fiscal_state) if fiscal_state else None
