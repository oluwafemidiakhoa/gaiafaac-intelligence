"""Institutional audit and data quality endpoints"""

from datetime import datetime
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from gaiafaac_api.customer_auth import DatabaseSession
from gaiafaac_api.services.evidence_audit import (
    EvidenceAuditService,
    get_integrity_score_for_jurisdiction,
)

router = APIRouter(prefix="/institutional", tags=["institutional audit"])


class AuditFindingSummary(BaseModel):
    """Summary of audit finding"""

    issue: str
    severity: Literal["critical", "high", "medium", "low"]
    jurisdiction: str
    period: str
    description: str
    affected_count: int
    recommendation: str
    auto_fix_available: bool


class IntegrityScoreResponse(BaseModel):
    """Data integrity score"""

    jurisdiction: str
    integrity_score: int  # 0-100
    total_claims: int
    published_count: int
    verified_count: int
    conflicted_count: int
    ready_for_publication: bool
    ready_for_decisions: bool


class AuditReport(BaseModel):
    """Complete institutional audit report"""

    timestamp: str
    integrity_score: int
    findings_summary: dict
    findings: list[AuditFindingSummary]
    institutional_readiness: dict


class ComparisonMetrics(BaseModel):
    """Comparative metrics across jurisdictions"""

    metric: str
    jurisdiction: str
    value: float
    period: str
    previous_period_value: float | None
    percent_change: float | None
    benchmark_average: float
    status: Literal["normal", "anomaly", "high", "low"]


@router.get("/audit/complete", response_model=AuditReport)
def run_complete_audit(session: DatabaseSession) -> AuditReport:
    """
    Run comprehensive institutional audit across all evidence.

    Detects:
    - Unverified data
    - Conflicting sources
    - Coverage gaps
    - Anomalous values
    - Stale sources
    - Broken audit trails

    Returns integrity score and actionable recommendations.
    """
    audit_service = EvidenceAuditService(session)
    return audit_service.audit_all()


@router.get("/audit/jurisdiction/{jurisdiction}", response_model=AuditReport)
def audit_jurisdiction(
    jurisdiction: str,
    session: DatabaseSession,
) -> AuditReport:
    """Audit specific jurisdiction's data integrity"""
    audit_service = EvidenceAuditService(session)
    return audit_service.audit_jurisdiction(jurisdiction)


@router.get(
    "/integrity-score/{jurisdiction}",
    response_model=IntegrityScoreResponse,
)
def get_jurisdiction_integrity_score(
    jurisdiction: str,
    session: DatabaseSession,
) -> IntegrityScoreResponse:
    """
    Quick integrity score for a jurisdiction (0-100).

    Score factors:
    - Published claims (50%)
    - Verified/reviewed claims (30%)
    - Conflicted sources penalty (-20%)

    Used to determine if data is ready for publication or institutional decisions.
    """
    return get_integrity_score_for_jurisdiction(session, jurisdiction)


@router.get("/readiness-matrix")
def get_institutional_readiness(session: DatabaseSession) -> dict:
    """
    Matrix showing which jurisdictions are ready for institutional use.

    Returns readiness status for:
    - Publication (integrity_score >= 80)
    - Decision support (integrity_score >= 70)
    - Requires review (has critical findings)
    """
    from sqlalchemy import select, func, and_
    from gaiafaac_api.database.ledger_models import FiscalClaim

    # Get all jurisdictions
    jurisdictions = session.execute(
        select(func.distinct(FiscalClaim.jurisdiction)).order_by(
            FiscalClaim.jurisdiction
        )
    ).scalars()

    readiness = {
        "timestamp": datetime.now().isoformat(),
        "jurisdictions": [],
        "summary": {
            "ready_for_publication": 0,
            "ready_for_decisions": 0,
            "requires_review": 0,
            "not_ready": 0,
        },
    }

    for jurisdiction in jurisdictions:
        score_data = get_integrity_score_for_jurisdiction(session, jurisdiction)

        status = "not_ready"
        if score_data["integrity_score"] >= 80:
            status = "ready_for_publication"
            readiness["summary"]["ready_for_publication"] += 1
        elif score_data["integrity_score"] >= 70:
            status = "ready_for_decisions"
            readiness["summary"]["ready_for_decisions"] += 1
        else:
            if score_data["conflicted_count"] > 0:
                status = "requires_review"
                readiness["summary"]["requires_review"] += 1
            else:
                readiness["summary"]["not_ready"] += 1

        readiness["jurisdictions"].append(
            {
                "name": jurisdiction,
                "integrity_score": score_data["integrity_score"],
                "status": status,
                "published_claims": score_data["published_count"],
                "verified_claims": score_data["verified_count"],
                "conflicts": score_data["conflicted_count"],
            }
        )

    return readiness


@router.get("/risk-indicators")
def get_risk_indicators(session: DatabaseSession) -> dict:
    """
    Institutional risk dashboard: what needs immediate attention?

    Identifies:
    - Unresolved conflicts (by jurisdiction)
    - Unverified high-value claims
    - Data gaps impacting decisions
    - Source quality issues
    """
    from sqlalchemy import select, func, and_
    from gaiafaac_api.database.ledger_models import FiscalClaim

    # 1. Unresolved conflicts
    conflicts = session.execute(
        select(
            FiscalClaim.jurisdiction,
            func.count(FiscalClaim.id),
        )
        .where(FiscalClaim.conflicted)
        .group_by(FiscalClaim.jurisdiction)
        .order_by(func.count(FiscalClaim.id).desc())
    ).all()

    # 2. Unverified high-value claims
    unverified_high_value = session.scalars(
        select(FiscalClaim)
        .where(
            and_(
                FiscalClaim.reviewed_at.is_(None),
                FiscalClaim.claim_value > 1_000_000_000,  # ₦1B+
            )
        )
        .order_by(FiscalClaim.claim_value.desc())
        .limit(10)
    ).all()

    # 3. Coverage gaps by jurisdiction/period
    from datetime import datetime as dt, timedelta

    now = dt.now()
    last_30_days = now - timedelta(days=30)

    stale = session.scalars(
        select(FiscalClaim).where(FiscalClaim.updated_at < last_30_days)
    ).all()

    return {
        "timestamp": datetime.now().isoformat(),
        "critical_risks": [
            {
                "risk_type": "unresolved_conflicts",
                "count": sum(c[1] for c in conflicts),
                "jurisdictions": {c[0]: c[1] for c in conflicts},
                "recommendation": "Resolve conflicts before publication",
            },
            {
                "risk_type": "unverified_high_value",
                "count": len(unverified_high_value),
                "total_naira": sum(
                    c.claim_value for c in unverified_high_value if c.claim_value
                ),
                "details": [
                    {
                        "jurisdiction": c.jurisdiction,
                        "value": str(c.claim_value),
                        "days_pending": (now - c.created_at).days,
                    }
                    for c in unverified_high_value
                ],
                "recommendation": "Prioritize review for high-value claims",
            },
            {
                "risk_type": "stale_data",
                "count": len(stale),
                "days_stale": 30,
                "recommendation": "Refresh from primary sources",
            },
        ],
        "overall_risk_level": (
            "critical"
            if len(unverified_high_value) > 5 or sum(c[1] for c in conflicts) > 20
            else "high"
            if len(unverified_high_value) > 0 or sum(c[1] for c in conflicts) > 10
            else "medium"
            if len(unverified_high_value) > 0 or len(stale) > 100
            else "low"
        ),
    }


@router.get("/data-lineage/{gaia_id}")
def get_data_lineage(
    gaia_id: str,
    session: DatabaseSession,
) -> dict:
    """
    Complete data lineage: source document → extraction → validation → publication

    Shows:
    - Original document (URL, hash, version)
    - Extracted values and assumptions
    - Validation results
    - Review/approval chain
    - Publication status
    - Any revisions
    """
    from gaiafaac_api.database.ledger_models import FiscalClaim, ClaimRevision

    claim = session.scalar(select(FiscalClaim).where(FiscalClaim.gaia_id == gaia_id))

    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    # Get revision history
    revisions = session.scalars(
        select(ClaimRevision)
        .where(ClaimRevision.original_claim_gaia_id == gaia_id)
        .order_by(ClaimRevision.created_at)
    ).all()

    lineage_events = []

    # Event: Source Document
    lineage_events.append(
        {
            "stage": "source_document",
            "timestamp": claim.created_at,
            "actor": claim.created_by or "automated_import",
            "organization": claim.source_organization,
            "document_url": claim.source_url,
            "document_hash_sha256": claim.document_sha256,
            "document_version": claim.document_version,
            "page_number": claim.source_page_number,
        }
    )

    # Event: Extracted Value
    lineage_events.append(
        {
            "stage": "extracted",
            "timestamp": claim.created_at,
            "value": str(claim.claim_value),
            "currency": claim.claim_currency,
            "period": claim.allocation_period.isoformat(),
            "extraction_method": "pdf_table" if claim.source_url else "manual_entry",
        }
    )

    # Event: Reviewed
    if claim.reviewed_at:
        lineage_events.append(
            {
                "stage": "reviewed",
                "timestamp": claim.reviewed_at,
                "reviewer": claim.reviewed_by,
                "review_notes": claim.review_notes,
                "status": "passed" if claim.approved_at else "flagged",
            }
        )

    # Event: Approved
    if claim.approved_at:
        lineage_events.append(
            {
                "stage": "approved",
                "timestamp": claim.approved_at,
                "approver": claim.approved_by,
                "comment": "Approved for publication",
            }
        )

    # Events: Revisions
    for rev in revisions:
        lineage_events.append(
            {
                "stage": "revised",
                "timestamp": rev.created_at,
                "revised_by": rev.revised_by,
                "reason": rev.change_reason,
                "source_changed": rev.source_revision,
                "new_gaia_id": rev.revised_claim_gaia_id,
            }
        )

    return {
        "gaia_id": gaia_id,
        "current_value": str(claim.claim_value),
        "current_status": claim.evidence_verification_status.value,
        "jurisdiction": claim.jurisdiction,
        "lineage": lineage_events,
        "audit_trail_complete": (
            claim.reviewed_at is not None
            and claim.approved_at is not None
            and claim.published_at is not None
        ),
    }


@router.get("/institutional-decision-brief/{jurisdiction}/{period}")
def get_decision_brief(
    jurisdiction: str,
    period: str,  # YYYY-MM
    session: DatabaseSession,
) -> dict:
    """
    Executive decision brief for a jurisdiction and period.

    Provides:
    - Key fiscal metrics with evidence badges
    - Year-over-year comparisons
    - Anomaly flags
    - Data integrity assessment
    - Conflicting sources (if any)
    - Recommended actions
    """
    from datetime import datetime as dt
    from sqlalchemy import select, and_

    try:
        period_date = dt.strptime(period, "%Y-%m")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid period (use YYYY-MM)")

    # Get all claims for this jurisdiction/period
    claims = session.scalars(
        select(FiscalClaim).where(
            and_(
                FiscalClaim.jurisdiction == jurisdiction,
                FiscalClaim.allocation_period == period_date,
            )
        )
    ).all()

    if not claims:
        raise HTTPException(
            status_code=404, detail=f"No data for {jurisdiction} in {period}"
        )

    # Compute metrics
    total_revenue = sum(c.claim_value for c in claims if c.claim_value and "revenue" in c.claim_type.lower())
    total_allocation = sum(
        c.claim_value
        for c in claims
        if c.claim_value and "allocation" in c.claim_type.lower()
    )
    conflicts_count = sum(1 for c in claims if c.conflicted)
    unverified_count = sum(1 for c in claims if c.evidence_verification_status != "published")

    # Get previous period for comparison
    from dateutil.relativedelta import relativedelta

    prev_period = period_date - relativedelta(months=1)
    prev_claims = session.scalars(
        select(FiscalClaim).where(
            and_(
                FiscalClaim.jurisdiction == jurisdiction,
                FiscalClaim.allocation_period == prev_period,
            )
        )
    ).all()

    prev_revenue = sum(
        c.claim_value
        for c in prev_claims
        if c.claim_value and "revenue" in c.claim_type.lower()
    )

    return {
        "jurisdiction": jurisdiction,
        "period": period,
        "metrics": {
            "total_revenue": {
                "value": str(total_revenue) if total_revenue else "0",
                "currency": "₦",
                "previous_period": str(prev_revenue) if prev_revenue else "0",
                "change_percent": (
                    (total_revenue - prev_revenue) / prev_revenue * 100
                    if prev_revenue and total_revenue
                    else 0
                ),
                "verification_status": (
                    "published" if sum(1 for c in claims if c.evidence_verification_status == "published") > 0 else "draft"
                ),
            },
            "total_allocation": {
                "value": str(total_allocation) if total_allocation else "0",
                "currency": "₦",
            },
        },
        "data_quality": {
            "total_claims": len(claims),
            "verified_claims": len([c for c in claims if c.reviewed_at]),
            "published_claims": len([c for c in claims if c.evidence_verification_status == "published"]),
            "conflicts": conflicts_count,
            "unverified": unverified_count,
            "ready_for_decision": conflicts_count == 0 and unverified_count == 0,
        },
        "recommendations": [
            "Data ready for institutional decisions"
            if conflicts_count == 0 and unverified_count == 0
            else f"Resolve {conflicts_count} conflicts and verify {unverified_count} claims before decisions",
        ],
    }
