from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, time

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.enums import EvidenceStatus, FiscalEventSeverity
from gaiafaac_api.database.ledger_models import (
    ClaimRevision,
    EvidenceManifest,
    EvidenceVerification,
    FiscalCertificate,
    FiscalClaim,
    FiscalEvent,
    FiscalProof,
    FiscalState,
)
from gaiafaac_api.database.models import SourceDocument, State
from gaiafaac_api.fiscal_ledger_schemas import (
    EvidenceHistoryEntry,
    EvidenceManifestResponse,
    FiscalCertificateData,
    FiscalCertificateEnvelope,
    FiscalCertificateEvidence,
    FiscalEventData,
    FiscalEventStreamEnvelope,
    FiscalEventStreamEvidence,
    JurisdictionIdentity,
    LedgerMeta,
)
from gaiafaac_api.ledger import (
    CANONICALIZATION_VERSION,
    GaiaObjectType,
    canonical_sha256,
    canonicalize,
    gaia_object_id,
)

INSTITUTIONAL_SCHEMA_VERSION = "1.0.0"
INSTITUTIONAL_METHODOLOGY_VERSION = "1.0.0"
CERTIFICATE_MANIFEST_VERSION = "gaia-fiscal-certificate-manifest-v1"
LIFECYCLE_EVENT_TYPES = {
    "new_source_detected",
    "source_revised",
    "claim_superseded",
    "evidence_upgraded",
    "evidence_downgraded",
    "cross_source_conflict",
    "fiscal_state_changed",
    "faac_spike",
    "faac_decline",
}


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Institutional object timestamps must be timezone-aware.")
    return value.astimezone(UTC)


def _stored_utc(value: datetime) -> datetime:
    """Normalize timestamps read from stores such as SQLite that strip timezone metadata."""

    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _jurisdiction(state: State) -> JurisdictionIdentity:
    return JurisdictionIdentity(code=f"NG-{state.code.upper()}", name=state.name)


def publish_fiscal_event(
    session: Session,
    *,
    state_id: uuid.UUID,
    event_type: str,
    severity: FiscalEventSeverity,
    effective_at: datetime,
    detected_at: datetime,
    evidence_status: EvidenceStatus,
    evidence_ids: list[str],
    explanation: str,
    calculation: dict[str, object] | None = None,
    fiscal_state_id: str | None = None,
    methodology_version: str = INSTITUTIONAL_METHODOLOGY_VERSION,
) -> FiscalEvent:
    """Publish a deterministic lifecycle event from explicit retained evidence."""

    if event_type not in LIFECYCLE_EVENT_TYPES:
        raise ValueError("Unsupported deterministic fiscal event type.")
    if not explanation.strip():
        raise ValueError("Fiscal events require a deterministic explanation.")
    state = session.get(State, state_id)
    if state is None:
        raise LookupError("Fiscal event jurisdiction does not exist.")
    if fiscal_state_id is not None:
        fiscal_state = session.get(FiscalState, fiscal_state_id)
        if fiscal_state is None or fiscal_state.state_id != state_id:
            raise ValueError("Fiscal event state lineage is invalid.")

    effective_at = _utc(effective_at)
    detected_at = _utc(detected_at)
    identifiers = sorted(set(evidence_ids))
    calculation_payload = canonicalize(calculation or {})
    identity = {
        "jurisdiction": f"NG-{state.code.upper()}",
        "event_type": event_type,
        "effective_at": effective_at,
        "detected_at": detected_at,
        "evidence_status": evidence_status,
        "evidence_ids": identifiers,
        "calculation": calculation_payload,
        "fiscal_state_id": fiscal_state_id,
        "methodology_version": methodology_version,
    }
    digest = canonical_sha256(identity)
    event_id = f"GFE-NG-{state.code.upper()}-{detected_at:%Y%m%d}-{digest[:6].upper()}"
    existing = session.get(FiscalEvent, event_id)
    if existing is not None:
        return existing

    event = FiscalEvent(
        event_id=event_id,
        state_id=state_id,
        event_type=event_type,
        severity=severity,
        effective_at=effective_at,
        detected_at=detected_at,
        evidence_status=evidence_status,
        evidence_ids=identifiers,
        calculation=calculation_payload,
        explanation=explanation.strip(),
        fiscal_state_id=fiscal_state_id,
        methodology_version=methodology_version,
    )
    session.add(event)
    session.flush()
    return event


def _event_data(session: Session, event: FiscalEvent) -> FiscalEventData:
    state = session.get(State, event.state_id)
    if state is None:
        raise RuntimeError("Fiscal event jurisdiction lineage is incomplete.")
    return FiscalEventData(
        event_id=event.event_id,
        jurisdiction=_jurisdiction(state),
        event_type=event.event_type,
        severity=event.severity,
        effective_at=_stored_utc(event.effective_at),
        detected_at=_stored_utc(event.detected_at),
        evidence_status=event.evidence_status,
        evidence_ids=event.evidence_ids,
        calculation=event.calculation,
        explanation=event.explanation,
        fiscal_state_id=event.fiscal_state_id,
        methodology_version=event.methodology_version,
    )


def fiscal_events(
    session: Session,
    *,
    jurisdiction_code: str | None = None,
    event_type: str | None = None,
    severity: FiscalEventSeverity | None = None,
    evidence_status: EvidenceStatus | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    limit: int = 100,
) -> FiscalEventStreamEnvelope:
    query = select(FiscalEvent).join(State, FiscalEvent.state_id == State.id)
    if jurisdiction_code:
        query = query.where(State.code == jurisdiction_code.strip().upper().removeprefix("NG-"))
    if event_type:
        query = query.where(FiscalEvent.event_type == event_type.strip().lower())
    if severity:
        query = query.where(FiscalEvent.severity == severity)
    if evidence_status:
        query = query.where(FiscalEvent.evidence_status == evidence_status)
    if date_from:
        query = query.where(
            FiscalEvent.detected_at >= datetime.combine(date_from, time.min, tzinfo=UTC)
        )
    if date_to:
        query = query.where(
            FiscalEvent.detected_at <= datetime.combine(date_to, time.max, tzinfo=UTC)
        )
    events = list(
        session.scalars(
            query.order_by(FiscalEvent.detected_at.desc(), FiscalEvent.event_id.desc()).limit(limit)
        )
    )
    return FiscalEventStreamEnvelope(
        data=[_event_data(session, event) for event in events],
        evidence=FiscalEventStreamEvidence(
            record_count=len(events),
            meaning=(
                "Events describe recorded evidence changes or threshold classifications. "
                "They do not infer cause, "
                "misconduct, or an unstated fiscal value."
            ),
        ),
        meta=LedgerMeta(
            schema_version=INSTITUTIONAL_SCHEMA_VERSION,
            methodology_version=INSTITUTIONAL_METHODOLOGY_VERSION,
        ),
    )


def evidence_history(session: Session, claim_gaia_id: str) -> list[EvidenceHistoryEntry]:
    row = session.execute(
        select(FiscalClaim, EvidenceVerification, FiscalProof, SourceDocument)
        .join(EvidenceVerification, EvidenceVerification.claim_gaia_id == FiscalClaim.gaia_id)
        .join(FiscalProof, FiscalProof.gaia_id == FiscalClaim.gaia_id)
        .join(SourceDocument, FiscalClaim.source_document_id == SourceDocument.id)
        .where(FiscalClaim.gaia_id == claim_gaia_id)
    ).first()
    if row is None:
        return []
    claim, verification, proof, source = row
    entries: list[EvidenceHistoryEntry] = []
    if source.downloaded_at is not None:
        entries.append(
            EvidenceHistoryEntry(
                entry_type="source_detected",
                occurred_at=_stored_utc(source.downloaded_at),
                label="Source document retrieved and fingerprinted.",
                evidence_ids=[source.sha256],
            )
        )
    if verification.verified_at is not None:
        entries.append(
            EvidenceHistoryEntry(
                entry_type="human_verified",
                occurred_at=_stored_utc(verification.verified_at),
                label="Human verification recorded.",
                evidence_ids=[claim.gaia_id],
            )
        )
    entries.append(
        EvidenceHistoryEntry(
            entry_type="published",
            occurred_at=_stored_utc(proof.published_at),
            label="Immutable Fiscal Proof published.",
            evidence_ids=[claim.gaia_id],
        )
    )
    revisions = list(
        session.scalars(
            select(ClaimRevision)
            .where(
                (ClaimRevision.previous_claim_gaia_id == claim_gaia_id)
                | (ClaimRevision.revised_claim_gaia_id == claim_gaia_id)
            )
            .order_by(ClaimRevision.detected_at, ClaimRevision.created_at)
        )
    )
    for revision in revisions:
        identifiers = [revision.previous_claim_gaia_id, revision.revised_claim_gaia_id]
        if revision.source_revision:
            entries.append(
                EvidenceHistoryEntry(
                    entry_type="source_revised",
                    occurred_at=_stored_utc(revision.detected_at),
                    label="A revised source document was retained.",
                    evidence_ids=identifiers,
                )
            )
        entries.append(
            EvidenceHistoryEntry(
                entry_type="claim_superseded",
                occurred_at=_stored_utc(revision.detected_at),
                label="The previous claim was superseded without rewriting history.",
                evidence_ids=identifiers,
            )
        )
    return sorted(entries, key=lambda entry: (entry.occurred_at, entry.entry_type))


def publish_fiscal_certificate(
    session: Session,
    *,
    fiscal_state_id: str,
    fiscal_period: str,
    issued_at: datetime,
    methodology_version: str = INSTITUTIONAL_METHODOLOGY_VERSION,
) -> FiscalCertificate:
    fiscal_state = session.get(FiscalState, fiscal_state_id)
    if fiscal_state is None:
        raise LookupError("Published Fiscal State does not exist.")
    state = session.get(State, fiscal_state.state_id)
    state_manifest = session.get(EvidenceManifest, fiscal_state.manifest_id)
    if state is None or state_manifest is None:
        raise RuntimeError("Fiscal State lineage is incomplete.")
    issued_at = _utc(issued_at)
    proof_ids = sorted(
        claim["gaia_id"]
        for domain in fiscal_state.domains.values()
        for claim in domain.get("claims", [])
        if isinstance(claim, dict) and isinstance(claim.get("gaia_id"), str)
    )
    domain_statuses = {
        name: str(value.get("status", EvidenceStatus.UNAVAILABLE.value))
        for name, value in fiscal_state.domains.items()
    }
    seed = {
        "jurisdiction": f"NG-{state.code.upper()}",
        "fiscal_period": fiscal_period,
        "fiscal_state_id": fiscal_state.fiscal_state_id,
        "fiscal_state_sha256": fiscal_state.integrity_hash,
        "issued_at": issued_at,
        "proof_gaia_ids": proof_ids,
        "methodology_version": methodology_version,
    }
    gaia_id = gaia_object_id(
        GaiaObjectType.CERTIFICATE,
        jurisdiction=f"NG-{state.code.upper()}",
        fiscal_period=fiscal_period,
        integrity_hash=canonical_sha256(seed),
    )
    existing = session.get(FiscalCertificate, gaia_id)
    if existing is not None:
        return existing
    payload = canonicalize(
        {
            "gaia_id": gaia_id,
            "schema_version": INSTITUTIONAL_SCHEMA_VERSION,
            "jurisdiction": _jurisdiction(state).model_dump(mode="json"),
            "fiscal_period": fiscal_period,
            "fiscal_state_id": fiscal_state.fiscal_state_id,
            "fiscal_state_sha256": fiscal_state.integrity_hash,
            "ledger_status": fiscal_state.ledger_status,
            "evidence_coverage": (
                format(fiscal_state.evidence_coverage, "f")
                if fiscal_state.evidence_coverage is not None
                else None
            ),
            "evidence_integrity": fiscal_state.evidence_integrity,
            "domain_statuses": domain_statuses,
            "proof_gaia_ids": proof_ids,
            "issued_at": issued_at,
            "methodology_version": methodology_version,
        }
    )
    payload_hash = canonical_sha256(payload)
    manifest = EvidenceManifest(
        id=uuid.uuid4(),
        subject_gaia_id=gaia_id,
        manifest_version=CERTIFICATE_MANIFEST_VERSION,
        schema_version=INSTITUTIONAL_SCHEMA_VERSION,
        canonicalization_version=CANONICALIZATION_VERSION,
        hash_algorithm="sha256",
        payload_sha256=payload_hash,
        payload=payload,
    )
    certificate = FiscalCertificate(
        gaia_id=gaia_id,
        state_id=state.id,
        fiscal_state_id=fiscal_state.fiscal_state_id,
        fiscal_period=fiscal_period,
        manifest_id=manifest.id,
        integrity_hash=payload_hash,
        schema_version=INSTITUTIONAL_SCHEMA_VERSION,
        methodology_version=methodology_version,
        issued_at=issued_at,
    )
    session.add_all([manifest, certificate])
    session.flush()
    return certificate


def get_fiscal_certificate(
    session: Session, certificate_gaia_id: str
) -> FiscalCertificateEnvelope | None:
    certificate = session.get(FiscalCertificate, certificate_gaia_id)
    if certificate is None:
        return None
    state = session.get(State, certificate.state_id)
    fiscal_state = session.get(FiscalState, certificate.fiscal_state_id)
    manifest = session.get(EvidenceManifest, certificate.manifest_id)
    if state is None or fiscal_state is None or manifest is None:
        raise RuntimeError("Fiscal Certificate lineage is incomplete.")
    statuses = {
        name: str(value.get("status", EvidenceStatus.UNAVAILABLE.value))
        for name, value in fiscal_state.domains.items()
    }
    proof_ids = manifest.payload.get("proof_gaia_ids", [])
    if not isinstance(proof_ids, list):
        raise RuntimeError("Fiscal Certificate proof lineage is malformed.")
    return FiscalCertificateEnvelope(
        data=FiscalCertificateData(
            gaia_id=certificate.gaia_id,
            jurisdiction=_jurisdiction(state),
            fiscal_period=certificate.fiscal_period,
            fiscal_state_id=fiscal_state.fiscal_state_id,
            ledger_status=fiscal_state.ledger_status,
            evidence_coverage=(
                format(fiscal_state.evidence_coverage, "f")
                if fiscal_state.evidence_coverage is not None
                else None
            ),
            evidence_integrity=fiscal_state.evidence_integrity,
            verified_domains=sorted(
                name for name, status in statuses.items() if status == EvidenceStatus.VERIFIED.value
            ),
            partial_domains=sorted(
                name
                for name, status in statuses.items()
                if status in {EvidenceStatus.PARTIAL.value, EvidenceStatus.CONFLICTING.value}
            ),
            unavailable_domains=sorted(
                name
                for name, status in statuses.items()
                if status == EvidenceStatus.UNAVAILABLE.value
            ),
            proof_gaia_ids=[str(item) for item in proof_ids],
            issued_at=_stored_utc(certificate.issued_at),
        ),
        evidence=FiscalCertificateEvidence(
            manifest=EvidenceManifestResponse(
                manifest_version=manifest.manifest_version,
                schema_version=manifest.schema_version,
                canonicalization_version=manifest.canonicalization_version,
                hash_algorithm="sha256",
                payload_sha256=manifest.payload_sha256,
                payload=manifest.payload,
            ),
            disclaimer=(
                "This certificate packages Gaia's retained evidence at a point in time. It is "
                "not a credit rating and does not independently certify government data as true."
            ),
        ),
        meta=LedgerMeta(
            schema_version=certificate.schema_version,
            methodology_version=certificate.methodology_version,
        ),
    )
