"""Evidence integrity audit and institutional decision support"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from enum import Enum

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from gaiafaac_api.database.ledger_models import FiscalClaim


class DataIntegrityIssue(str, Enum):
    """Issues detected during audit"""

    MISSING_DATA = "missing_data"  # Expected data not found
    CONFLICTING_SOURCES = "conflicting_sources"  # Multiple sources disagree
    UNVERIFIED = "unverified"  # Data not reviewed/approved
    STALE_SOURCE = "stale_source"  # Source document > 30 days old
    INCOMPLETE_COVERAGE = "incomplete_coverage"  # Coverage gap in period/jurisdiction
    ANOMALOUS_VALUE = "anomalous_value"  # Unusual change or outlier
    BROKEN_AUDIT_TRAIL = "broken_audit_trail"  # Missing review/approval steps
    SOURCE_MISMATCH = "source_mismatch"  # Reported value doesn't match source


class AuditFinding:
    """Single audit finding"""

    def __init__(
        self,
        issue_type: DataIntegrityIssue,
        severity: str,  # "critical", "high", "medium", "low"
        jurisdiction: str,
        period: str,
        description: str,
        affected_gaia_ids: list[str],
        recommendation: str,
        auto_fix_available: bool = False,
    ):
        self.issue_type = issue_type
        self.severity = severity
        self.jurisdiction = jurisdiction
        self.period = period
        self.description = description
        self.affected_gaia_ids = affected_gaia_ids
        self.recommendation = recommendation
        self.auto_fix_available = auto_fix_available
        self.detected_at = datetime.now(timezone.utc)


class EvidenceAuditService:
    """Comprehensive institutional data audit"""

    def __init__(self, session: Session):
        self.session = session
        self.findings: list[AuditFinding] = []

    def audit_all(self) -> dict:
        """Run complete integrity audit across all evidence"""
        self.findings = []

        # Run all checks
        self._audit_verification_status()
        self._audit_data_conflicts()
        self._audit_coverage_gaps()
        self._audit_anomalies()
        self._audit_source_freshness()
        self._audit_audit_trails()

        # Aggregate results
        return self._generate_audit_report()

    def audit_jurisdiction(self, jurisdiction: str) -> dict:
        """Audit specific jurisdiction's data"""
        self.findings = []
        self.jurisdiction_filter = jurisdiction

        self._audit_verification_status()
        self._audit_data_conflicts()
        self._audit_coverage_gaps()
        self._audit_anomalies()

        return self._generate_audit_report()

    def _audit_verification_status(self) -> None:
        """Find unverified data"""
        unverified = self.session.scalars(
            select(FiscalClaim).where(
                FiscalClaim.evidence_verification_status.in_(["draft", "pending"])
            )
        ).all()

        if len(unverified) > 0:
            jurisdictions = list(set(c.jurisdiction for c in unverified))
            self.findings.append(
                AuditFinding(
                    issue_type=DataIntegrityIssue.UNVERIFIED,
                    severity="high",
                    jurisdiction=", ".join(jurisdictions[:3]),
                    period="Mixed",
                    description=f"{len(unverified)} fiscal claims awaiting review/approval",
                    affected_gaia_ids=[c.gaia_id for c in unverified[:10]],
                    recommendation="Prioritize review queue. Unverified data cannot be used for institutional decisions.",
                    auto_fix_available=False,
                )
            )

    def _audit_data_conflicts(self) -> None:
        """Find conflicting sources"""
        conflicted = self.session.scalars(select(FiscalClaim).where(FiscalClaim.conflicted)).all()

        if len(conflicted) > 0:
            self.findings.append(
                AuditFinding(
                    issue_type=DataIntegrityIssue.CONFLICTING_SOURCES,
                    severity="high",
                    jurisdiction="Multiple",
                    period="Mixed",
                    description=f"{len(conflicted)} conflicts detected between authoritative sources",
                    affected_gaia_ids=[c.gaia_id for c in conflicted[:10]],
                    recommendation="Review conflicting source documents. Contact jurisdictions for clarification on reported values.",
                    auto_fix_available=False,
                )
            )

    def _audit_coverage_gaps(self) -> None:
        """Find missing data periods"""
        # Get all states
        all_states = self.session.execute(select(func.distinct(FiscalClaim.jurisdiction))).scalars()

        # Get last 12 months
        now = datetime.now(timezone.utc)
        months_to_check = [
            (now - timedelta(days=30 * i)).replace(day=1, hour=0, minute=0, second=0)
            for i in range(12)
        ]

        gaps = []
        for state in all_states:
            for month in months_to_check:
                count = self.session.scalar(
                    select(func.count(FiscalClaim.id)).where(
                        and_(
                            FiscalClaim.jurisdiction == state,
                            FiscalClaim.allocation_period >= month,
                            FiscalClaim.allocation_period < month + timedelta(days=32),
                        )
                    )
                )
                if count == 0:
                    gaps.append((state, month.strftime("%Y-%m")))

        if len(gaps) > 10:
            self.findings.append(
                AuditFinding(
                    issue_type=DataIntegrityIssue.INCOMPLETE_COVERAGE,
                    severity="medium",
                    jurisdiction="All",
                    period="Mixed",
                    description=f"{len(gaps)} gaps detected (missing periods for {len(set(g[0] for g in gaps))} jurisdictions)",
                    affected_gaia_ids=[],
                    recommendation="Import missing data from source institutions or mark as unavailable. Coverage gaps prevent complete analysis.",
                    auto_fix_available=False,
                )
            )

    def _audit_anomalies(self) -> None:
        """Detect unusual values or changes"""
        # Get recent significant changes
        recent_revisions = self.session.execute(
            select(FiscalClaim).order_by(FiscalClaim.updated_at.desc()).limit(1000)
        ).scalars()

        anomalies = []
        for claim in recent_revisions:
            if claim.claim_value and hasattr(claim, "previous_value"):
                if claim.previous_value:
                    pct_change = abs(
                        (claim.claim_value - claim.previous_value) / claim.previous_value * 100
                    )
                    if pct_change > 50:  # >50% change
                        anomalies.append(claim.gaia_id)

        if len(anomalies) > 5:
            self.findings.append(
                AuditFinding(
                    issue_type=DataIntegrityIssue.ANOMALOUS_VALUE,
                    severity="medium",
                    jurisdiction="Multiple",
                    period="Recent",
                    description=f"{len(anomalies)} claims with >50% changes detected",
                    affected_gaia_ids=anomalies[:10],
                    recommendation="Review materiality. Unusual changes may indicate data correction or source updates. Verify against official sources.",
                    auto_fix_available=False,
                )
            )

    def _audit_source_freshness(self) -> None:
        """Check if sources are recent"""
        stale_sources = self.session.scalars(
            select(FiscalClaim).where(
                FiscalClaim.created_at < datetime.now(timezone.utc) - timedelta(days=30)
            )
        ).all()

        if len(stale_sources) > 100:
            self.findings.append(
                AuditFinding(
                    issue_type=DataIntegrityIssue.STALE_SOURCE,
                    severity="low",
                    jurisdiction="All",
                    period=">30 days old",
                    description=f"{len(stale_sources)} claims from sources older than 30 days",
                    affected_gaia_ids=[],
                    recommendation="Consider refreshing from primary sources. No action required unless accuracy concerns arise.",
                    auto_fix_available=False,
                )
            )

    def _audit_audit_trails(self) -> None:
        """Check for broken audit chains"""
        incomplete_reviews = self.session.scalars(
            select(FiscalClaim).where(
                FiscalClaim.reviewed_at.is_(None),
                FiscalClaim.evidence_verification_status == "published",
            )
        ).all()

        if len(incomplete_reviews) > 0:
            self.findings.append(
                AuditFinding(
                    issue_type=DataIntegrityIssue.BROKEN_AUDIT_TRAIL,
                    severity="critical",
                    jurisdiction="Multiple",
                    period="Mixed",
                    description=f"{len(incomplete_reviews)} published claims missing review records (audit trail broken)",
                    affected_gaia_ids=[c.gaia_id for c in incomplete_reviews[:10]],
                    recommendation="CRITICAL: Requires data remediation. Published claims must have complete review/approval audit trail.",
                    auto_fix_available=False,
                )
            )

    def _generate_audit_report(self) -> dict:
        """Generate audit report with recommendations"""
        critical = [f for f in self.findings if f.severity == "critical"]
        high = [f for f in self.findings if f.severity == "high"]
        medium = [f for f in self.findings if f.severity == "medium"]

        integrity_score = max(
            0,
            100 - (len(critical) * 25 + len(high) * 10 + len(medium) * 3),
        )

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "integrity_score": integrity_score,
            "findings_summary": {
                "critical": len(critical),
                "high": len(high),
                "medium": len(medium),
                "low": len([f for f in self.findings if f.severity == "low"]),
            },
            "findings": [
                {
                    "issue": f.issue_type.value,
                    "severity": f.severity,
                    "jurisdiction": f.jurisdiction,
                    "period": f.period,
                    "description": f.description,
                    "affected_count": len(f.affected_gaia_ids),
                    "recommendation": f.recommendation,
                    "auto_fix_available": f.auto_fix_available,
                }
                for f in sorted(
                    self.findings,
                    key=lambda x: {
                        "critical": 0,
                        "high": 1,
                        "medium": 2,
                        "low": 3,
                    }[x.severity],
                )
            ],
            "institutional_readiness": {
                "can_publish_reports": integrity_score >= 80,
                "can_support_decisions": integrity_score >= 70,
                "requires_review": len(critical) > 0,
                "next_actions": self._get_next_actions(critical, high),
            },
        }

    def _get_next_actions(self, critical: list, high: list) -> list[str]:
        """Recommend immediate actions"""
        actions = []

        if critical:
            actions.append("URGENT: Fix broken audit trails before any institutional decisions")

        if any(f.issue_type == DataIntegrityIssue.CONFLICTING_SOURCES for f in high):
            actions.append("Resolve source conflicts through review board")

        if any(f.issue_type == DataIntegrityIssue.UNVERIFIED for f in high):
            actions.append("Process review queue: unverified claims cannot be published")

        if any(f.issue_type == DataIntegrityIssue.INCOMPLETE_COVERAGE for f in high):
            actions.append("Import missing periods from OAGF/jurisdictions")

        if not actions:
            actions.append("Data integrity acceptable. Proceed with institutional workflows.")

        return actions


def get_integrity_score_for_jurisdiction(session: Session, jurisdiction: str) -> dict:
    """Quick integrity score for a jurisdiction"""
    audit = EvidenceAuditService(session)
    audit.jurisdiction_filter = jurisdiction

    total_claims = session.scalar(
        select(func.count(FiscalClaim.id)).where(FiscalClaim.jurisdiction == jurisdiction)
    )

    published = session.scalar(
        select(func.count(FiscalClaim.id)).where(
            and_(
                FiscalClaim.jurisdiction == jurisdiction,
                FiscalClaim.evidence_verification_status == "published",
            )
        )
    )

    verified = session.scalar(
        select(func.count(FiscalClaim.id)).where(
            and_(
                FiscalClaim.jurisdiction == jurisdiction,
                FiscalClaim.reviewed_at.is_not(None),
            )
        )
    )

    conflicted = session.scalar(
        select(func.count(FiscalClaim.id)).where(
            and_(
                FiscalClaim.jurisdiction == jurisdiction,
                FiscalClaim.conflicted,
            )
        )
    )

    score = (
        (published / total_claims * 50 if total_claims else 0)
        + (verified / total_claims * 30 if total_claims else 0)
        - (conflicted / total_claims * 20 if total_claims else 0)
    )

    return {
        "jurisdiction": jurisdiction,
        "integrity_score": int(max(0, score)),
        "total_claims": total_claims,
        "published_count": published,
        "verified_count": verified,
        "conflicted_count": conflicted,
        "ready_for_publication": published > 0,
        "ready_for_decisions": score >= 70,
    }
