from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.models import ReportingPeriod
from gaiafaac_api.decision_packet_schemas import (
    DecisionPacketMonth,
    DecisionPacketResponse,
    DecisionPacketWatchEvent,
)
from gaiafaac_api.services.fiscal_proof import get_fiscal_proof
from gaiafaac_api.services.fiscal_pulse import fiscal_pulse
from gaiafaac_api.services.fiscal_watch import fiscal_watch


def decision_packet(
    session: Session,
    *,
    state_slug: str,
    year: int,
) -> DecisionPacketResponse | None:
    pulse = fiscal_pulse(session, year)
    state = next((item for item in pulse.states if item.state_slug == state_slug), None)
    if state is None:
        return None

    periods = list(
        session.scalars(
            select(ReportingPeriod)
            .where(
                ReportingPeriod.is_published.is_(True),
                ReportingPeriod.is_demo.is_(False),
                ReportingPeriod.revenue_month >= date(year, 1, 1),
                ReportingPeriod.revenue_month < date(year + 1, 1, 1),
            )
            .order_by(ReportingPeriod.revenue_month)
        )
    )

    months: list[DecisionPacketMonth] = []
    for period in periods:
        proof = get_fiscal_proof(
            session,
            state_slug=state_slug,
            revenue_month=period.revenue_month,
        )
        if proof is None:
            continue
        months.append(
            DecisionPacketMonth(
                revenue_month=proof.revenue_month,
                reporting_label=proof.reporting_label,
                gross_total=proof.financials.gross_total,
                total_deductions=proof.financials.total_deductions,
                net_allocation=proof.financials.net_allocation,
                reconciliation_status=proof.financials.reconciliation_status,
                proof_id=proof.proof_id,
                proof_path=(
                    f"/fiscal-proof/{proof.state_slug}/{proof.revenue_month.isoformat()}"
                ),
                source_organization=proof.source.source_organization,
                source_sha256=proof.source.sha256,
                human_verified=proof.verification.human_verified,
            )
        )

    watch = fiscal_watch(session, year)
    watch_events = [
        DecisionPacketWatchEvent(
            kind=event.kind,
            severity=event.severity,
            headline=event.headline,
            detail=event.detail,
            proof_path=event.proof_path,
        )
        for event in watch.events
        if event.state_slug == state_slug
    ]

    return DecisionPacketResponse(
        state_name=state.state_name,
        state_slug=state.state_slug,
        state_code=state.state_code,
        geopolitical_zone=state.geopolitical_zone,
        year=year,
        coverage_label=pulse.coverage_label,
        months_published=state.months_published,
        annual_gross=state.annual_gross,
        annual_deductions=state.annual_deductions,
        annual_net=state.annual_net,
        deduction_burden_pct=state.deduction_burden_pct,
        net_retention_pct=state.net_retention_pct,
        momentum=state.momentum,
        momentum_pct=state.momentum_pct,
        volatility=state.volatility,
        volatility_cv_pct=state.volatility_cv_pct,
        evidence_status=state.evidence_status,
        watch_events=watch_events,
        months=months,
        disclaimer=(
            "Decision Packets summarize only published, non-demo GaiaFAAC evidence. "
            "They are descriptive evidence dossiers, not credit ratings, investment advice, "
            "solvency assessments, corruption indicators, or predictions."
        ),
    )
