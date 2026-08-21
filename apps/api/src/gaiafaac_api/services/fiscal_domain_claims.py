from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.enums import EvidenceStatus, FiscalEventSeverity, SourceStatus
from gaiafaac_api.database.ledger_models import (
    EvidenceManifest,
    EvidenceVerification,
    FiscalClaim,
    FiscalProof,
)
from gaiafaac_api.database.models import SourceDocument, State
from gaiafaac_api.ledger import (
    CANONICALIZATION_VERSION,
    GaiaObjectType,
    canonical_sha256,
    canonicalize,
    gaia_object_id,
)
from gaiafaac_api.services.fiscal_institutional import publish_fiscal_event
from gaiafaac_api.services.fiscal_trust import (
    create_claim_revision,
    register_evidence_source,
)

DOMAIN_CLAIM_SCHEMA_VERSION = "1.0.0"
DOMAIN_CLAIM_METHODOLOGY_VERSION = "1.0.0"
DOMAIN_CLAIM_MANIFEST_VERSION = "gaia-fiscal-domain-claim-manifest-v1"
SUPPORTED_DOMAINS: dict[str, GaiaObjectType] = {
    "igr": GaiaObjectType.IGR,
    "debt": GaiaObjectType.DEBT,
    "debt_service": GaiaObjectType.DEBT_SERVICE,
    "budget": GaiaObjectType.BUDGET,
    "expenditure": GaiaObjectType.EXPENDITURE,
    "liabilities": GaiaObjectType.LIABILITY,
}


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Fiscal claim timestamps must be timezone-aware.")
    return value.astimezone(UTC)


def publish_domain_claim(
    session: Session,
    *,
    domain: str,
    state_id: uuid.UUID,
    source_document_id: uuid.UUID,
    fiscal_period: str,
    metric: str,
    value: Decimal | None,
    value_text: str | None,
    unit: str,
    currency: str | None,
    effective_at: datetime,
    published_at: datetime,
    source_page: int | None = None,
    source_table: str | None = None,
    extraction_method: str = "governed_pipeline",
    human_reviewed: bool = False,
    reconciled: bool | None = None,
    methodology_version: str = DOMAIN_CLAIM_METHODOLOGY_VERSION,
) -> FiscalProof:
    """Publish one immutable non-FAAC fiscal claim from retained source evidence.

    This function deliberately accepts observed values only. It does not estimate missing
    fields, annualize partial periods, convert currencies, or infer a fiscal value.
    """

    canonical_domain = domain.strip().lower()
    object_type = SUPPORTED_DOMAINS.get(canonical_domain)
    if object_type is None:
        raise ValueError("Unsupported fiscal domain.")
    if not metric.strip():
        raise ValueError("A fiscal metric is required.")
    if value is None and not (value_text and value_text.strip()):
        raise ValueError("A numeric or textual observed value is required.")
    if currency is not None and len(currency.strip()) != 3:
        raise ValueError("Currency must be a three-letter code when supplied.")

    state = session.get(State, state_id)
    source = session.get(SourceDocument, source_document_id)
    if state is None:
        raise LookupError("Jurisdiction does not exist.")
    if source is None or source.is_demo:
        raise LookupError("A retained non-demo source document is required.")

    effective_at = _utc(effective_at)
    published_at = _utc(published_at)
    source_verified = source.source_status is SourceStatus.APPROVED
    evidence_status = (
        EvidenceStatus.VERIFIED
        if source_verified and human_reviewed and reconciled is not False
        else EvidenceStatus.PARTIAL
    )
    normalized_metric = metric.strip().lower()
    normalized_unit = unit.strip()
    normalized_currency = currency.strip().upper() if currency else None
    normalized_value_text = value_text.strip() if value_text else None
    if normalized_value_text is None and value is not None:
        normalized_value_text = format(value, "f")

    jurisdiction = f"NG-{state.code.upper()}"
    identity = canonicalize(
        {
            "object_type": canonical_domain,
            "jurisdiction": jurisdiction,
            "fiscal_period": fiscal_period,
            "metric": normalized_metric,
            "value": normalized_value_text,
            "unit": normalized_unit,
            "currency": normalized_currency,
            "source_sha256": source.sha256,
            "source_page": source_page,
            "source_table": source_table,
            "methodology_version": methodology_version,
        }
    )
    identity_hash = canonical_sha256(identity)
    gaia_id = gaia_object_id(
        object_type,
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
            FiscalClaim.object_type == canonical_domain,
            FiscalClaim.fiscal_period == fiscal_period,
            FiscalClaim.metric == normalized_metric,
        )
        .order_by(FiscalClaim.published_at.desc())
        .limit(1)
    )
    claim = FiscalClaim(
        gaia_id=gaia_id,
        object_type=canonical_domain,
        state_id=state.id,
        fiscal_period=fiscal_period,
        metric=normalized_metric,
        value=value,
        value_text=normalized_value_text,
        unit=normalized_unit,
        currency=normalized_currency,
        source_document_id=source.id,
        source_sha256=source.sha256,
        source_page=source_page,
        source_table=source_table,
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
        verified_at=published_at if human_reviewed else None,
        methodology_version=methodology_version,
        notes=(
            "Observed source-linked value. Gaia preserves provenance and revisions; "
            "artifact integrity does not independently certify the publisher's claim."
        ),
    )
    payload = canonicalize(
        {
            "gaia_id": gaia_id,
            "schema_version": DOMAIN_CLAIM_SCHEMA_VERSION,
            "object_type": canonical_domain,
            "jurisdiction": {
                "country": "NG",
                "code": jurisdiction,
                "name": state.name,
            },
            "fiscal_period": fiscal_period,
            "metric": normalized_metric,
            "value": normalized_value_text,
            "unit": normalized_unit,
            "currency": normalized_currency,
            "source": {
                "publisher": source.source_organization,
                "document_url": source.source_url,
                "document_sha256": source.sha256,
                "publication_date": (
                    source.publication_date.isoformat() if source.publication_date else None
                ),
                "page": source_page,
                "table": source_table,
            },
            "verification": {
                "status": evidence_status,
                "source_verified": source_verified,
                "reconciled": reconciled,
                "human_reviewed": human_reviewed,
                "published": True,
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
        manifest_version=DOMAIN_CLAIM_MANIFEST_VERSION,
        schema_version=DOMAIN_CLAIM_SCHEMA_VERSION,
        canonicalization_version=CANONICALIZATION_VERSION,
        hash_algorithm="sha256",
        payload_sha256=payload_hash,
        payload=payload,
    )
    proof = FiscalProof(
        gaia_id=gaia_id,
        manifest_id=manifest.id,
        schema_version=DOMAIN_CLAIM_SCHEMA_VERSION,
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
        fiscal_domain=canonical_domain,
        verification_status=evidence_status,
        reporting_cadence=None,
    )
    publish_fiscal_event(
        session,
        state_id=state.id,
        event_type="new_source_detected",
        severity=FiscalEventSeverity.INFORMATIONAL,
        effective_at=effective_at,
        detected_at=published_at,
        evidence_status=evidence_status,
        evidence_ids=[gaia_id, source.sha256],
        explanation=f"A {canonical_domain} source-linked claim entered the Gaia fiscal ledger.",
    )

    if previous_claim is not None:
        revision = create_claim_revision(
            session,
            previous_claim=previous_claim,
            revised_claim=claim,
            source_revision=source.supersedes_document_id == previous_claim.source_document_id,
            detected_at=published_at,
        )
        publish_fiscal_event(
            session,
            state_id=state.id,
            event_type="claim_superseded",
            severity=(
                FiscalEventSeverity.MATERIAL
                if revision.material_change
                else FiscalEventSeverity.NOTABLE
            ),
            effective_at=effective_at,
            detected_at=published_at,
            evidence_status=evidence_status,
            evidence_ids=[previous_claim.gaia_id, claim.gaia_id],
            calculation={
                "value_delta": revision.value_delta_text,
                "value_change_percent": revision.value_change_percent_text,
                "material_change": revision.material_change,
            },
            explanation=(
                f"A previous {canonical_domain} claim was superseded; "
                "both versions remain retained."
            ),
        )
    return proof
