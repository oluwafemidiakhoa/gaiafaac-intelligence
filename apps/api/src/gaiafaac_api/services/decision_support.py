"""Institutional decision support: anomaly detection, recommendations, intelligence"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from enum import Enum

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from gaiafaac_api.database.ledger_models import FiscalClaim


class AnomalyType(str, Enum):
    """Anomalies detected for institutional decision-makers"""

    UNUSUAL_DECLINE = "unusual_decline"  # Revenue down >20%
    UNUSUAL_GROWTH = "unusual_growth"  # Revenue up >50%
    DEVIATION_FROM_PEER = "deviation_from_peer"  # Outlier vs peer states
    MISSING_DATA = "missing_data"  # Gap in expected data
    SOURCE_DISAGREEMENT = "source_disagreement"  # Authorities disagree
    TREND_REVERSAL = "trend_reversal"  # Opposite direction from recent history


class Anomaly:
    """Single detected anomaly"""

    def __init__(
        self,
        anomaly_type: AnomalyType,
        jurisdiction: str,
        period: str,
        metric: str,
        severity: str,  # "critical", "high", "medium", "low"
        current_value: Decimal,
        expected_value: Decimal | None,
        percent_variance: float,
        description: str,
        recommendation: str,
        supporting_data: dict,
    ):
        self.anomaly_type = anomaly_type
        self.jurisdiction = jurisdiction
        self.period = period
        self.metric = metric
        self.severity = severity
        self.current_value = current_value
        self.expected_value = expected_value
        self.percent_variance = percent_variance
        self.description = description
        self.recommendation = recommendation
        self.supporting_data = supporting_data
        self.detected_at = datetime.now(UTC)


class DecisionSupportService:
    """AI-powered institutional decision support"""

    def __init__(self, session: Session):
        self.session = session
        self.anomalies: list[Anomaly] = []

    def analyze_jurisdiction(self, jurisdiction: str, months_back: int = 12) -> dict:
        """
        Comprehensive analysis for institutional decision-makers.

        Includes:
        - Anomaly detection
        - Peer comparisons
        - Trend analysis
        - Risk indicators
        - Actionable recommendations
        """
        self.anomalies = []
        now = datetime.now(UTC)

        # Get data for analysis
        all_claims = self.session.scalars(
            select(FiscalClaim)
            .where(
                and_(
                    FiscalClaim.jurisdiction == jurisdiction,
                    FiscalClaim.allocation_period >= now - timedelta(days=30 * months_back),
                )
            )
            .order_by(FiscalClaim.allocation_period)
        ).all()

        if not all_claims:
            return {
                "jurisdiction": jurisdiction,
                "status": "no_data",
                "message": "Insufficient data for analysis",
            }

        # Run analysis
        self._detect_trend_anomalies(jurisdiction, all_claims)
        self._detect_peer_deviations(jurisdiction, all_claims)
        self._detect_conflicts(jurisdiction, all_claims)
        self._detect_data_gaps(jurisdiction, months_back)

        return self._generate_decision_brief(jurisdiction, all_claims)

    def _detect_trend_anomalies(self, jurisdiction: str, claims: list) -> None:
        """Detect unusual trends in data"""
        by_metric = {}
        for claim in claims:
            key = claim.claim_type
            if key not in by_metric:
                by_metric[key] = []
            by_metric[key].append(claim)

        for metric, metric_claims in by_metric.items():
            metric_claims.sort(key=lambda c: c.allocation_period)

            if len(metric_claims) >= 3:
                recent = metric_claims[-1].claim_value or Decimal("0")
                previous = metric_claims[-2].claim_value or Decimal("0")
                older = metric_claims[-3].claim_value or Decimal("0")

                if previous > 0:
                    pct_change = (recent - previous) / previous * 100
                    avg_change = ((previous - older) / older * 100) if older > 0 else 0

                    # Detect reversals
                    if (previous > older and recent < previous) or (
                        previous < older and recent > previous
                    ):
                        self.anomalies.append(
                            Anomaly(
                                anomaly_type=AnomalyType.TREND_REVERSAL,
                                jurisdiction=jurisdiction,
                                period=metric_claims[-1].allocation_period.strftime("%Y-%m"),
                                metric=metric,
                                severity="medium",
                                current_value=recent,
                                expected_value=previous,
                                percent_variance=pct_change,
                                description=f"{metric} reversed direction: was {'increasing' if previous > older else 'decreasing'}, now {'decreasing' if recent < previous else 'increasing'}",
                                recommendation="Investigate cause of trend reversal. Check for policy changes, economic shifts, or data reporting changes.",
                                supporting_data={
                                    "previous_value": str(previous),
                                    "older_value": str(older),
                                    "trend": (
                                        "up_then_down" if recent < previous else "down_then_up"
                                    ),
                                },
                            )
                        )

                    # Detect unusual changes
                    if abs(pct_change) > 50 and abs(pct_change) > abs(avg_change) * 1.5:
                        severity = "critical" if abs(pct_change) > 100 else "high"
                        anomaly_type = (
                            AnomalyType.UNUSUAL_GROWTH
                            if pct_change > 0
                            else AnomalyType.UNUSUAL_DECLINE
                        )

                        self.anomalies.append(
                            Anomaly(
                                anomaly_type=anomaly_type,
                                jurisdiction=jurisdiction,
                                period=metric_claims[-1].allocation_period.strftime("%Y-%m"),
                                metric=metric,
                                severity=severity,
                                current_value=recent,
                                expected_value=previous,
                                percent_variance=pct_change,
                                description=f"{metric} changed {pct_change:.1f}% (significant vs historical {avg_change:.1f}% average)",
                                recommendation="Verify data source. Confirm if this represents actual change in revenue or data reporting adjustment.",
                                supporting_data={
                                    "current": str(recent),
                                    "previous": str(previous),
                                    "percent_change": pct_change,
                                    "historical_avg_change": avg_change,
                                },
                            )
                        )

    def _detect_peer_deviations(self, jurisdiction: str, claims: list) -> None:
        """Compare against peer states"""
        # Get latest period
        latest_period = max(c.allocation_period for c in claims)

        # Get all jurisdictions' data for same period
        peer_data = self.session.execute(
            select(
                FiscalClaim.jurisdiction,
                func.sum(FiscalClaim.claim_value),
            )
            .where(
                and_(
                    FiscalClaim.allocation_period == latest_period,
                    FiscalClaim.claim_type.like("%revenue%"),
                )
            )
            .group_by(FiscalClaim.jurisdiction)
        ).all()

        if len(peer_data) < 5:
            return  # Need min peers for comparison

        values = [p[1] for p in peer_data if p[1]]
        if not values:
            return

        avg = sum(values) / len(values)
        std_dev = (sum((v - avg) ** 2 for v in values) / len(values)) ** 0.5

        jurisdiction_value = next((p[1] for p in peer_data if p[0] == jurisdiction), None)

        if jurisdiction_value and std_dev > 0:
            z_score = abs(jurisdiction_value - avg) / std_dev

            if z_score > 2:  # More than 2 std devs from mean
                self.anomalies.append(
                    Anomaly(
                        anomaly_type=AnomalyType.DEVIATION_FROM_PEER,
                        jurisdiction=jurisdiction,
                        period=latest_period.strftime("%Y-%m"),
                        metric="revenue",
                        severity="high" if z_score > 3 else "medium",
                        current_value=jurisdiction_value,
                        expected_value=avg,
                        percent_variance=(jurisdiction_value - avg) / avg * 100,
                        description=f"{jurisdiction} revenue is {abs((jurisdiction_value - avg) / avg * 100):.1f}% {'above' if jurisdiction_value > avg else 'below'} peer average",
                        recommendation="Compare revenue sources and economic fundamentals with peer states. May indicate unique economic position or data quality issue.",
                        supporting_data={
                            "peer_count": len(peer_data),
                            "peer_average": str(avg),
                            "z_score": round(z_score, 2),
                            "std_deviation": str(std_dev),
                        },
                    )
                )

    def _detect_conflicts(self, jurisdiction: str, claims: list) -> None:
        """Identify conflicting sources"""
        conflicted = [c for c in claims if c.conflicted]

        if len(conflicted) > 0:
            self.anomalies.append(
                Anomaly(
                    anomaly_type=AnomalyType.SOURCE_DISAGREEMENT,
                    jurisdiction=jurisdiction,
                    period="mixed",
                    metric="data_quality",
                    severity="high",
                    current_value=Decimal(len(conflicted)),
                    expected_value=Decimal(0),
                    percent_variance=100,
                    description=f"{len(conflicted)} claims have conflicting sources",
                    recommendation="Contact jurisdictions and authoritative sources to resolve disagreements. Do not make decisions until conflicts are resolved.",
                    supporting_data={
                        "conflict_count": len(conflicted),
                        "gaia_ids": [c.gaia_id for c in conflicted[:5]],
                    },
                )
            )

    def _detect_data_gaps(self, jurisdiction: str, months_back: int) -> None:
        """Identify missing expected data"""
        now = datetime.now(UTC)
        expected_months = set()

        for i in range(months_back):
            month = (now - timedelta(days=30 * i)).replace(day=1)
            expected_months.add(month)

        existing_claims = self.session.scalars(
            select(FiscalClaim).where(FiscalClaim.jurisdiction == jurisdiction)
        ).all()

        existing_months = set(c.allocation_period for c in existing_claims)
        missing_months = expected_months - existing_months

        if len(missing_months) > 2:
            self.anomalies.append(
                Anomaly(
                    anomaly_type=AnomalyType.MISSING_DATA,
                    jurisdiction=jurisdiction,
                    period="mixed",
                    metric="data_completeness",
                    severity="medium",
                    current_value=Decimal(len(existing_months)),
                    expected_value=Decimal(len(expected_months)),
                    percent_variance=(len(existing_months) / len(expected_months) - 1) * 100,
                    description=f"Missing data for {len(missing_months)} months ({len(missing_months) / len(expected_months) * 100:.0f}% gap)",
                    recommendation="Import missing data from source institutions or mark periods as data unavailable.",
                    supporting_data={
                        "missing_count": len(missing_months),
                        "coverage_percent": round(
                            len(existing_months) / len(expected_months) * 100, 1
                        ),
                    },
                )
            )

    def _generate_decision_brief(self, jurisdiction: str, claims: list) -> dict:
        """Generate executive decision brief"""
        # Calculate metrics
        total_revenue = sum(
            c.claim_value for c in claims if c.claim_value and "revenue" in c.claim_type.lower()
        )
        total_faac = sum(
            c.claim_value for c in claims if c.claim_value and "faac" in c.claim_type.lower()
        )
        faac_dependence = (total_faac / total_revenue * 100) if total_revenue and total_faac else 0

        # Group anomalies by severity
        critical = [a for a in self.anomalies if a.severity == "critical"]
        high = [a for a in self.anomalies if a.severity == "high"]
        medium = [a for a in self.anomalies if a.severity == "medium"]

        # Decision readiness
        can_make_decision = (
            len(critical) == 0
            and len(high) <= 1
            and not any(a.anomaly_type == AnomalyType.SOURCE_DISAGREEMENT for a in self.anomalies)
        )

        return {
            "jurisdiction": jurisdiction,
            "timestamp": datetime.now(UTC).isoformat(),
            "key_metrics": {
                "total_revenue": str(total_revenue) if total_revenue else "0",
                "total_faac": str(total_faac) if total_faac else "0",
                "faac_dependence_percent": round(faac_dependence, 1),
                "data_sources": len(set(c.source_organization for c in claims)),
                "verified_claims": len([c for c in claims if c.reviewed_at]),
                "total_claims": len(claims),
            },
            "anomalies": {
                "critical": len(critical),
                "high": len(high),
                "medium": len(medium),
                "details": [
                    {
                        "type": a.anomaly_type.value,
                        "severity": a.severity,
                        "metric": a.metric,
                        "description": a.description,
                        "recommendation": a.recommendation,
                        "variance_percent": round(a.percent_variance, 1),
                    }
                    for a in sorted(
                        self.anomalies,
                        key=lambda x: {
                            "critical": 0,
                            "high": 1,
                            "medium": 2,
                        }[x.severity],
                    )
                ],
            },
            "decision_readiness": {
                "can_make_institutional_decision": can_make_decision,
                "blockers": (
                    [a.anomaly_type.value for a in critical]
                    if critical
                    else ([a.anomaly_type.value for a in high] if high else [])
                ),
                "recommendation": (
                    "CRITICAL: Resolve anomalies before making decisions"
                    if critical
                    else (
                        "Proceed with caution; see high-severity items"
                        if high
                        else "Clear to proceed with institutional decisions"
                    )
                ),
            },
            "next_actions": self._recommend_actions(critical, high, medium, can_make_decision),
        }

    def _recommend_actions(
        self, critical: list, high: list, medium: list, can_decide: bool
    ) -> list[str]:
        """Recommend next actions for decision-maker"""
        actions = []

        if critical:
            actions.append(f"URGENT: Resolve {len(critical)} critical anomalies before proceeding")

        if any(a.anomaly_type == AnomalyType.SOURCE_DISAGREEMENT for a in high):
            actions.append("Contact jurisdictions to resolve source conflicts")

        if any(a.anomaly_type == AnomalyType.MISSING_DATA for a in high + medium):
            actions.append("Import missing data periods for complete analysis")

        if can_decide:
            actions.append("Ready for institutional decisions (loan approvals, budgeting, etc.)")

        return actions
