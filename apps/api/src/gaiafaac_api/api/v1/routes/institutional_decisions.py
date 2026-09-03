"""Institutional decision support endpoints"""

from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import and_, func, select

from gaiafaac_api.customer_auth import DatabaseSession
from gaiafaac_api.database.ledger_models import FiscalClaim
from gaiafaac_api.services.decision_support import DecisionSupportService

router = APIRouter(prefix="/decisions", tags=["institutional decisions"])


class AnomalyDetail(BaseModel):
    """Detected anomaly"""

    type: str
    severity: str
    metric: str
    description: str
    recommendation: str
    variance_percent: float


class DecisionBrief(BaseModel):
    """Institutional decision support brief"""

    jurisdiction: str
    timestamp: str
    key_metrics: dict
    anomalies: dict
    decision_readiness: dict
    next_actions: list[str]


@router.get("/analysis/{jurisdiction}", response_model=DecisionBrief)
def analyze_jurisdiction_for_decision(
    jurisdiction: str,
    months: int = 12,
    session: DatabaseSession = None,
) -> DecisionBrief:
    """
    AI-powered decision support analysis for institutional decision-makers.

    Detects:
    - Unusual trends (growth, decline, reversals)
    - Peer deviations (outliers vs similar states)
    - Source conflicts (authorities disagreeing)
    - Data gaps (missing periods)

    Returns actionable intelligence with clear "ready to decide" assessment.

    **Use cases:**
    - Loan committees: Is this state's fiscal position sustainable?
    - Investors: Which states have anomalies that need investigation?
    - Auditors: What changed materially and why?
    - Policymakers: Which jurisdictions need fiscal support?
    """
    decision_service = DecisionSupportService(session)
    return decision_service.analyze_jurisdiction(jurisdiction, months)


@router.get("/risk-summary")
def get_risk_summary_all_jurisdictions(
    session: DatabaseSession,
) -> dict:
    """
    Risk summary across all jurisdictions.

    Quickly identify which states are:
    - Ready for institutional decisions
    - Have high-severity anomalies
    - Have data quality issues
    - Require attention before decisions
    """
    jurisdictions = session.execute(
        select(func.distinct(FiscalClaim.jurisdiction)).order_by(FiscalClaim.jurisdiction)
    ).scalars()

    decision_service = DecisionSupportService(session)
    risk_matrix = []

    for jurisdiction in jurisdictions:
        analysis = decision_service.analyze_jurisdiction(jurisdiction, 12)

        if analysis.get("status") == "no_data":
            continue

        risk_matrix.append(
            {
                "jurisdiction": jurisdiction,
                "decision_ready": analysis["decision_readiness"]["can_make_institutional_decision"],
                "anomalies": {
                    "critical": analysis["anomalies"]["critical"],
                    "high": analysis["anomalies"]["high"],
                    "medium": analysis["anomalies"]["medium"],
                },
                "faac_dependence": analysis["key_metrics"].get("faac_dependence_percent", 0),
                "blockers": analysis["decision_readiness"]["blockers"],
            }
        )

    # Sort by decision readiness
    ready = [r for r in risk_matrix if r["decision_ready"]]
    caution = [r for r in risk_matrix if not r["decision_ready"] and r["anomalies"]["high"] > 0]
    review = [r for r in risk_matrix if not r["decision_ready"] and r["anomalies"]["critical"] > 0]

    return {
        "timestamp": analysis["timestamp"] if analysis else None,
        "summary": {
            "ready_for_decisions": len(ready),
            "proceed_with_caution": len(caution),
            "requires_review": len(review),
        },
        "ready_for_decisions": ready,
        "proceed_with_caution": caution,
        "requires_review": review,
    }


@router.post("/decision-packet/{jurisdiction}")
def generate_decision_packet(
    jurisdiction: str,
    period: str,  # YYYY-MM
    decision_type: str = "general",  # loan, investment, audit, policy
    session: DatabaseSession = None,
) -> dict:
    """
    Generate comprehensive decision packet for institutional use.

    Includes:
    - All relevant fiscal metrics with evidence
    - Anomalies and risks flagged
    - Peer comparisons
    - Audit trail for compliance
    - Data integrity score
    - Reviewer sign-off requirements

    **Decision types:**
    - `loan`: For loan approvals (lenders' focus: sustainability, FAAC dependence)
    - `investment`: For investment decisions (investors' focus: growth, trends)
    - `audit`: For audit committees (focus: controls, changes, conflicts)
    - `policy`: For policymakers (focus: trends, peer comparison, anomalies)

    Output can be exported as PDF with digital signatures for institutional records.
    """
    try:
        period_date = datetime.strptime(period, "%Y-%m")
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid period (use YYYY-MM)") from e

    # Get analysis
    decision_service = DecisionSupportService(session)
    analysis = decision_service.analyze_jurisdiction(jurisdiction, 12)

    # Get all claims for this period
    claims = session.scalars(
        select(FiscalClaim).where(
            and_(
                FiscalClaim.jurisdiction == jurisdiction,
                FiscalClaim.allocation_period == period_date,
            )
        )
    ).all()

    # Tailor output to decision type
    packet = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "jurisdiction": jurisdiction,
            "period": period,
            "decision_type": decision_type,
            "preparer": "Gaia Fiscal Intelligence",
            "requires_review": len(analysis["anomalies"]["critical"]) > 0,
            "requires_approval": True,
        },
        "executive_summary": {
            "decision_ready": analysis["decision_readiness"]["can_make_institutional_decision"],
            "recommendation": analysis["decision_readiness"]["recommendation"],
            "blockers": analysis["decision_readiness"]["blockers"],
        },
        "key_metrics": analysis["key_metrics"],
        "analysis": analysis,
        "fiscal_claims": [
            {
                "gaia_id": c.gaia_id,
                "type": c.claim_type,
                "value": str(c.claim_value),
                "currency": c.claim_currency,
                "source": c.source_organization,
                "source_url": c.source_url,
                "verification_status": c.evidence_verification_status.value,
                "reviewed_by": c.reviewed_by,
                "approved_by": c.approved_by,
            }
            for c in claims
        ],
        "compliance": {
            "audit_trail_complete": all(c.reviewed_at and c.approved_at for c in claims),
            "all_verified": all(
                c.evidence_verification_status.value == "published" for c in claims
            ),
            "conflicts_resolved": not any(c.conflicted for c in claims),
            "data_sources": len(set(c.source_organization for c in claims)),
        },
        "institutional_approvals": {
            "reviewer_1": {"status": "pending", "name": None, "date": None},
            "reviewer_2": {"status": "pending", "name": None, "date": None},
            "publisher": {"status": "pending", "name": None, "date": None},
        },
    }

    # Customize based on decision type
    if decision_type == "loan":
        packet["focus"] = "Sustainability Assessment"
        packet["lender_concern"] = (
            f"FAAC dependence: {analysis['key_metrics'].get('faac_dependence_percent', 0):.1f}%"
        )

    elif decision_type == "investment":
        packet["focus"] = "Growth & Trend Analysis"
        packet["trend_items"] = [
            a
            for a in analysis["anomalies"]["details"]
            if "growth" in a["type"] or "decline" in a["type"]
        ]

    elif decision_type == "audit":
        packet["focus"] = "Controls & Changes Audit"
        packet["conflict_items"] = [
            a for a in analysis["anomalies"]["details"] if "conflict" in a["type"]
        ]

    return packet


@router.get("/comparable-analysis/{jurisdiction}/{period}")
def get_comparable_jurisdictions(
    jurisdiction: str,
    period: str,
    metric: str = "revenue",
    session: DatabaseSession = None,
) -> dict:
    """
    Compare jurisdiction against peers.

    Shows:
    - Where it ranks among similar states
    - Metrics that distinguish it
    - What's anomalous vs peer average
    - Which peers to benchmark against
    """
    from datetime import datetime as dt

    from sqlalchemy import and_, func, select

    try:
        period_date = dt.strptime(period, "%Y-%m")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid period (use YYYY-MM)")

    from gaiafaac_api.database.ledger_models import FiscalClaim

    # Get target jurisdiction data
    target = session.scalar(
        select(
            func.sum(FiscalClaim.claim_value),
        )
        .where(
            and_(
                FiscalClaim.jurisdiction == jurisdiction,
                FiscalClaim.allocation_period == period_date,
                FiscalClaim.claim_type.like(f"%{metric}%"),
            )
        )
        .group_by(FiscalClaim.jurisdiction)
    )

    # Get all jurisdictions
    peers = session.execute(
        select(
            FiscalClaim.jurisdiction,
            func.sum(FiscalClaim.claim_value),
            func.count(FiscalClaim.id),
        )
        .where(
            and_(
                FiscalClaim.allocation_period == period_date,
                FiscalClaim.claim_type.like(f"%{metric}%"),
            )
        )
        .group_by(FiscalClaim.jurisdiction)
        .order_by(func.sum(FiscalClaim.claim_value).desc())
    ).all()

    if not target:
        raise HTTPException(status_code=404, detail="No data for this jurisdiction/period")

    values = [p[1] for p in peers if p[1]]
    avg = sum(values) / len(values) if values else 0

    # Rank target
    ranking = next(
        (i + 1 for i, p in enumerate(peers) if p[0] == jurisdiction),
        None,
    )

    return {
        "jurisdiction": jurisdiction,
        "period": period,
        "metric": metric,
        "rank": ranking,
        "total_peers": len(peers),
        "value": str(target) if target else "0",
        "peer_average": str(avg),
        "peer_range": {
            "highest": str(peers[0][1]) if peers else "0",
            "lowest": str(peers[-1][1]) if peers else "0",
        },
        "percentile": round(
            (ranking - 1) / len(peers) * 100 if ranking else 0,
            1,
        ),
        "peers": [
            {
                "rank": i + 1,
                "jurisdiction": p[0],
                "value": str(p[1]),
                "is_target": p[0] == jurisdiction,
                "percent_vs_avg": round((p[1] - avg) / avg * 100, 1) if avg else 0,
            }
            for i, p in enumerate(peers[:10])
        ],
    }
