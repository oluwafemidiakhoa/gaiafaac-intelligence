"""Evidence provenance and audit trail endpoints"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from gaiafaac_api.customer_auth import DatabaseSession
from gaiafaac_api.database.ledger_models import FiscalClaim, ClaimRevision

router = APIRouter(prefix="/evidence", tags=["evidence provenance"])


class SourceMetadata(BaseModel):
    """Source document metadata"""

    organization: str
    url: str | None = None
    documentVersion: str | None = None
    pageNumber: str | None = None
    sha256: str | None = None


class ReviewRecord(BaseModel):
    """Review and approval record"""

    reviewedAt: datetime | None = None
    reviewedBy: str | None = None
    approvedAt: datetime | None = None
    approvedBy: str | None = None
    reviewNotes: str | None = None


class RevisionRecord(BaseModel):
    """Revision history entry"""

    date: datetime
    changeDescription: str
    revisedBy: str
    sourceRevision: bool


class EvidenceProvenance(BaseModel):
    """Complete evidence trail for a data point"""

    gaiaId: str
    claimValue: str
    claimCurrency: str
    claimType: str
    jurisdiction: str
    period: str

    # Evidence
    verificationStatus: str  # "published", "draft", "demo", "conflicted", "pending"
    source: SourceMetadata
    review: ReviewRecord

    # History
    publishedAt: datetime | None = None
    createdAt: datetime
    revisions: list[RevisionRecord] = []

    # Conflicts
    conflictCount: int = 0
    conflictingClaims: list[str] = []  # Other GaiaIDs with conflicting values


@router.get("/provenance/{gaia_id}", response_model=EvidenceProvenance)
def get_evidence_provenance(
    gaia_id: str,
    session: DatabaseSession,
) -> EvidenceProvenance:
    """
    Get complete evidence provenance for a fiscal claim.

    Returns source document, verification status, review history, and revisions.
    This is the evidence trail backing every published number in Gaia.
    """
    # Query the fiscal claim
    claim = session.scalar(select(FiscalClaim).where(FiscalClaim.gaia_id == gaia_id))

    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    # Get revisions
    revisions = session.scalars(
        select(ClaimRevision)
        .where(ClaimRevision.original_claim_gaia_id == gaia_id)
        .order_by(ClaimRevision.created_at.desc())
    ).all()

    revision_records = [
        RevisionRecord(
            date=rev.created_at,
            changeDescription=f"Claim revised: {rev.change_reason or 'See details'}",
            revisedBy=rev.revised_by or "system",
            sourceRevision=rev.source_revision,
        )
        for rev in revisions
    ]

    # Count conflicting claims
    conflict_count = 0
    conflicting_ids = []
    if claim.conflicted:
        # Query other claims with same jurisdiction/period but different values
        conflicting = session.scalars(
            select(FiscalClaim).where(
                FiscalClaim.jurisdiction == claim.jurisdiction,
                FiscalClaim.allocation_period == claim.allocation_period,
                FiscalClaim.claim_type == claim.claim_type,
                FiscalClaim.gaia_id != gaia_id,
            )
        ).all()
        conflicting_ids = [c.gaia_id for c in conflicting if c.conflicted]
        conflict_count = len(conflicting_ids)

    return EvidenceProvenance(
        gaiaId=claim.gaia_id,
        claimValue=str(claim.claim_value),
        claimCurrency=claim.claim_currency or "₦",
        claimType=claim.claim_type,
        jurisdiction=claim.jurisdiction,
        period=claim.allocation_period.strftime("%Y-%m"),
        verificationStatus=claim.evidence_verification_status.value,
        source=SourceMetadata(
            organization=claim.source_organization or "Unknown",
            url=claim.source_url,
            documentVersion=claim.document_version,
            pageNumber=claim.source_page_number,
            sha256=claim.document_sha256,
        ),
        review=ReviewRecord(
            reviewedAt=claim.reviewed_at,
            reviewedBy=claim.reviewed_by,
            approvedAt=claim.approved_at,
            approvedBy=claim.approved_by,
            reviewNotes=claim.review_notes,
        ),
        publishedAt=claim.published_at,
        createdAt=claim.created_at,
        revisions=revision_records,
        conflictCount=conflict_count,
        conflictingClaims=conflicting_ids,
    )


@router.get("/audit-trail/{gaia_id}")
def get_audit_trail(
    gaia_id: str,
    session: DatabaseSession,
) -> dict:
    """
    Get detailed audit trail: who did what, when, and why.

    Supports institutional compliance, four-eyes verification, and dispute resolution.
    """
    claim = session.scalar(select(FiscalClaim).where(FiscalClaim.gaia_id == gaia_id))

    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    events = []

    # Event 1: Created
    events.append(
        {
            "timestamp": claim.created_at,
            "actor": claim.created_by or "system",
            "action": "CREATED",
            "description": f"Initial claim: {claim.claim_value} {claim.claim_currency}",
            "status": "draft",
        }
    )

    # Event 2: Reviewed
    if claim.reviewed_at:
        events.append(
            {
                "timestamp": claim.reviewed_at,
                "actor": claim.reviewed_by or "unknown",
                "action": "REVIEWED",
                "description": f"Reviewed and verified against source",
                "notes": claim.review_notes,
                "status": "in-review",
            }
        )

    # Event 3: Approved
    if claim.approved_at:
        events.append(
            {
                "timestamp": claim.approved_at,
                "actor": claim.approved_by or "unknown",
                "action": "APPROVED",
                "description": "Approved for publication (four-eyes control)",
                "status": "published",
            }
        )

    # Event 4+: Revisions
    revisions = session.scalars(
        select(ClaimRevision)
        .where(ClaimRevision.original_claim_gaia_id == gaia_id)
        .order_by(ClaimRevision.created_at)
    ).all()

    for rev in revisions:
        events.append(
            {
                "timestamp": rev.created_at,
                "actor": rev.revised_by or "system",
                "action": "REVISED",
                "description": f"Claim revised: {rev.change_reason}",
                "sourceRevision": rev.source_revision,
                "newGaiaId": rev.revised_claim_gaia_id,
                "status": "pending" if not claim.approved_at else "published",
            }
        )

    # Sort by timestamp
    events.sort(key=lambda e: e["timestamp"])

    return {
        "gaiaId": gaia_id,
        "jurisdiction": claim.jurisdiction,
        "period": claim.allocation_period.strftime("%Y-%m"),
        "currentValue": str(claim.claim_value),
        "currentStatus": claim.evidence_verification_status.value,
        "auditTrail": events,
        "isConflicted": claim.conflicted,
        "sourceDocument": {
            "organization": claim.source_organization,
            "url": claim.source_url,
            "sha256": claim.document_sha256,
        },
    }


@router.get("/conflicting-sources/{jurisdiction}/{period}/{claim_type}")
def get_conflicting_sources(
    jurisdiction: str,
    period: str,  # "YYYY-MM"
    claim_type: str,
    session: DatabaseSession,
) -> dict:
    """
    Get all conflicting sources for a specific jurisdiction/period/type.

    Used to display reconciliation findings when multiple sources disagree.
    """
    from datetime import datetime as dt

    try:
        period_date = dt.strptime(period, "%Y-%m")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid period format (use YYYY-MM)")

    conflicting_claims = session.scalars(
        select(FiscalClaim)
        .where(
            FiscalClaim.jurisdiction == jurisdiction,
            FiscalClaim.allocation_period == period_date,
            FiscalClaim.claim_type == claim_type,
            FiscalClaim.conflicted,
        )
        .order_by(FiscalClaim.source_organization)
    ).all()

    if not conflicting_claims:
        return {
            "jurisdiction": jurisdiction,
            "period": period,
            "claimType": claim_type,
            "status": "reconciled",
            "conflicts": [],
        }

    conflicts = [
        {
            "gaiaId": claim.gaia_id,
            "value": str(claim.claim_value),
            "currency": claim.claim_currency,
            "source": claim.source_organization,
            "sourceUrl": claim.source_url,
            "sourceHash": claim.document_sha256,
            "verificationStatus": claim.evidence_verification_status.value,
            "reportedAt": claim.created_at,
            "reviewNotes": claim.review_notes,
        }
        for claim in conflicting_claims
    ]

    return {
        "jurisdiction": jurisdiction,
        "period": period,
        "claimType": claim_type,
        "status": "conflicted",
        "conflictCount": len(conflicts),
        "conflicts": conflicts,
        "recommendation": (
            "Multiple authoritative sources report different values. "
            "Review source documents and contact jurisdictions for clarification."
        ),
    }
