from datetime import date, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from gaiafaac_api.database.enums import EvidenceStatus, FiscalEventSeverity
from gaiafaac_api.database.session import get_session
from gaiafaac_api.fiscal_ledger_schemas import (
    EvidenceManifestResponse,
    EvidenceSourceRegistryEnvelope,
    FiscalArtifactVerificationResponse,
    FiscalCertificateEnvelope,
    FiscalEventStreamEnvelope,
    FiscalProofEnvelope,
    FiscalStateEnvelope,
)
from gaiafaac_api.ledger import canonical_sha256
from gaiafaac_api.services.fiscal_institutional import fiscal_events, get_fiscal_certificate
from gaiafaac_api.services.fiscal_ledger import (
    METHODOLOGY_VERSION,
    get_fiscal_proof_by_gaia_id,
    get_fiscal_state_by_id,
    get_jurisdiction_fiscal_state,
)
from gaiafaac_api.services.fiscal_trust import evidence_sources

router = APIRouter(tags=["fiscal ledger"])
DatabaseSession = Annotated[Session, Depends(get_session)]


@router.get(
    "/jurisdictions/{code}/state",
    response_model=FiscalStateEnvelope,
    summary="Latest published Fiscal State for a jurisdiction",
)
def jurisdiction_fiscal_state(
    code: str,
    session: DatabaseSession,
    as_of: Annotated[date | datetime | None, Query()] = None,
) -> FiscalStateEnvelope:
    try:
        result = get_jurisdiction_fiscal_state(session, jurisdiction_code=code, as_of=as_of)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No published Fiscal State exists for this jurisdiction and date.",
        )
    return result


@router.get(
    "/fiscal-states/{gaia_id}",
    response_model=FiscalStateEnvelope,
    summary="Published Fiscal State by immutable Gaia ID",
)
def fiscal_state_by_id(gaia_id: str, session: DatabaseSession) -> FiscalStateEnvelope:
    result = get_fiscal_state_by_id(session, fiscal_state_gaia_id=gaia_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fiscal State not found.",
        )
    return result


@router.get(
    "/proofs/{gaia_id}",
    response_model=FiscalProofEnvelope,
    summary="Portable Fiscal Proof by immutable Gaia ID",
)
def fiscal_proof_by_id(gaia_id: str, session: DatabaseSession) -> FiscalProofEnvelope:
    result = get_fiscal_proof_by_gaia_id(session, gaia_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fiscal Proof not found.")
    return result


@router.get(
    "/events",
    response_model=FiscalEventStreamEnvelope,
    summary="Deterministic fiscal evidence lifecycle event stream",
)
def fiscal_event_stream(
    session: DatabaseSession,
    jurisdiction: Annotated[str | None, Query(min_length=2, max_length=16)] = None,
    event_type: Annotated[str | None, Query(min_length=2, max_length=80)] = None,
    severity: Annotated[FiscalEventSeverity | None, Query()] = None,
    evidence_status: Annotated[EvidenceStatus | None, Query()] = None,
    date_from: Annotated[date | None, Query()] = None,
    date_to: Annotated[date | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
) -> FiscalEventStreamEnvelope:
    if date_from and date_to and date_from > date_to:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="date_from cannot be after date_to.",
        )
    return fiscal_events(
        session,
        jurisdiction_code=jurisdiction,
        event_type=event_type,
        severity=severity,
        evidence_status=evidence_status,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
    )


@router.get(
    "/jurisdictions/{code}/events",
    response_model=FiscalEventStreamEnvelope,
    summary="Fiscal evidence lifecycle events for one jurisdiction",
)
def jurisdiction_fiscal_events(
    code: str,
    session: DatabaseSession,
    event_type: Annotated[str | None, Query(min_length=2, max_length=80)] = None,
    severity: Annotated[FiscalEventSeverity | None, Query()] = None,
    evidence_status: Annotated[EvidenceStatus | None, Query()] = None,
    date_from: Annotated[date | None, Query()] = None,
    date_to: Annotated[date | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
) -> FiscalEventStreamEnvelope:
    if date_from and date_to and date_from > date_to:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="date_from cannot be after date_to.",
        )
    return fiscal_events(
        session,
        jurisdiction_code=code,
        event_type=event_type,
        severity=severity,
        evidence_status=evidence_status,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
    )


@router.get(
    "/certificates/{gaia_id}",
    response_model=FiscalCertificateEnvelope,
    summary="Immutable Gaia Fiscal Certificate by ID",
)
def fiscal_certificate_by_id(gaia_id: str, session: DatabaseSession) -> FiscalCertificateEnvelope:
    result = get_fiscal_certificate(session, gaia_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fiscal Certificate not found.",
        )
    return result


@router.get(
    "/evidence-sources",
    response_model=EvidenceSourceRegistryEnvelope,
    summary="Browse the versioned Gaia evidence source registry",
)
def evidence_source_registry(
    session: DatabaseSession,
    jurisdiction: Annotated[str | None, Query(min_length=2, max_length=16)] = None,
    publisher: Annotated[str | None, Query(min_length=2, max_length=200)] = None,
    fiscal_domain: Annotated[str | None, Query(min_length=2, max_length=40)] = None,
) -> EvidenceSourceRegistryEnvelope:
    items = evidence_sources(
        session,
        jurisdiction_code=jurisdiction,
        publisher=publisher,
        fiscal_domain=fiscal_domain,
    )
    return EvidenceSourceRegistryEnvelope(
        data=items,
        evidence={
            "record_count": len(items),
            "meaning": (
                "Registry records describe Gaia's retained source lineage and workflow state; "
                "they do not certify the originating publisher's claims as true."
            ),
        },
        meta={"schema_version": "1.1.0", "methodology_version": METHODOLOGY_VERSION},
    )


@router.get(
    "/jurisdictions/{code}/evidence",
    response_model=EvidenceSourceRegistryEnvelope,
    summary="Evidence sources retained for one jurisdiction",
)
def jurisdiction_evidence_sources(
    code: str,
    session: DatabaseSession,
    publisher: Annotated[str | None, Query(min_length=2, max_length=200)] = None,
    fiscal_domain: Annotated[str | None, Query(min_length=2, max_length=40)] = None,
) -> EvidenceSourceRegistryEnvelope:
    return evidence_source_registry(
        session,
        jurisdiction=code,
        publisher=publisher,
        fiscal_domain=fiscal_domain,
    )


@router.post(
    "/verify",
    response_model=FiscalArtifactVerificationResponse,
    summary="Recompute a Gaia Fiscal Proof or Fiscal State manifest hash",
)
def verify_fiscal_artifact(
    manifest: EvidenceManifestResponse,
) -> FiscalArtifactVerificationResponse:
    supported_versions = {
        "gaia-fiscal-proof-manifest-v1",
        "gaia-fiscal-state-manifest-v1",
        "gaia-fiscal-state-manifest-v2",
        "gaia-fiscal-certificate-manifest-v1",
    }
    if manifest.manifest_version not in supported_versions:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Unsupported Gaia fiscal manifest version.",
        )
    if manifest.canonicalization_version != "gaia-canonical-json-v1":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Unsupported canonicalization version.",
        )

    try:
        computed = canonical_sha256(manifest.payload)
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    verified = computed == manifest.payload_sha256.lower()
    recorded = manifest.payload.get("verification")
    verification = recorded if isinstance(recorded, dict) else {}
    return FiscalArtifactVerificationResponse(
        status="verified" if verified else "mismatch",
        artifact_integrity="verified" if verified else "failed",
        embedded_sha256=manifest.payload_sha256.lower(),
        computed_sha256=computed,
        manifest_version=manifest.manifest_version,
        source_provenance_recorded=(
            verification.get("source_verified")
            if isinstance(verification.get("source_verified"), bool)
            else None
        ),
        reconciliation_recorded=(
            verification.get("reconciled")
            if isinstance(verification.get("reconciled"), bool)
            else None
        ),
        human_review_recorded=(
            verification.get("human_reviewed")
            if isinstance(verification.get("human_reviewed"), bool)
            else None
        ),
        meaning=(
            "This result verifies artifact integrity only. Recorded provenance, reconciliation, "
            "and review states do not independently prove the originating government claim."
        ),
    )
