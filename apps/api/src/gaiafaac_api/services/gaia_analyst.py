from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from gaiafaac_api.fiscal_pulse_schemas import FiscalPulseState
from gaiafaac_api.gaia_analyst_schemas import GaiaAnalystEvidence, GaiaAnalystResponse
from gaiafaac_api.services.fiscal_pulse import fiscal_pulse
from gaiafaac_api.services.fiscal_watch import fiscal_watch
from gaiafaac_api.services.published_data import get_published_overview, latest_published_period

_TOP_N = 5


@dataclass(frozen=True)
class _StateMatch:
    first: FiscalPulseState | None
    second: FiscalPulseState | None


@dataclass(frozen=True)
class _LatestStateNet:
    state_name: str
    state_slug: str
    value: str
    revenue_month: date
    reporting_label: str


def _slug_tokens(value: str) -> set[str]:
    return {token for token in re.split(r"[^a-z0-9]+", value.lower()) if token}


def _state_matches(question: str, states: list[FiscalPulseState]) -> _StateMatch:
    lowered = question.lower()
    question_tokens = _slug_tokens(lowered)
    matches: list[FiscalPulseState] = []
    for state in states:
        named = state.state_name.lower() in lowered or state.state_slug.lower() in lowered
        coded = state.state_code.lower() in question_tokens
        fct = state.state_code == "FC" and bool(
            {"fct", "abuja"} & question_tokens or "federal capital territory" in lowered
        )
        state_tokens = _slug_tokens(state.state_name)
        token_named = bool(state_tokens and state_tokens.issubset(question_tokens))
        if named or coded or fct or token_named:
            matches.append(state)
    unique: list[FiscalPulseState] = []
    seen: set[str] = set()
    for state in matches:
        if state.state_slug not in seen:
            unique.append(state)
            seen.add(state.state_slug)
    return _StateMatch(
        first=unique[0] if unique else None,
        second=unique[1] if len(unique) > 1 else None,
    )


def _money(value: str | None) -> str:
    if value is None:
        return "unavailable"
    return f"NGN {Decimal(value):,.2f}"


def _evidence(
    state: FiscalPulseState,
    *,
    label: str,
    value: str,
    metric: str,
) -> GaiaAnalystEvidence:
    return GaiaAnalystEvidence(
        state_name=state.state_name,
        state_slug=state.state_slug,
        label=label,
        value=value,
        metric=metric,
        reference_path=f"/states/{state.state_slug}",
        reference_label="Open state record",
    )


def _latest_state_net(
    session: Session, *, state: FiscalPulseState, year: int
) -> _LatestStateNet | None:
    period = latest_published_period(session)
    if period is None or period.revenue_month.year != year:
        return None
    overview = get_published_overview(session, period)
    if overview is None:
        return None
    allocation = next(
        (item for item in overview.allocations if item.state_slug == state.state_slug),
        None,
    )
    if allocation is None or allocation.net_allocation is None:
        return None
    return _LatestStateNet(
        state_name=allocation.state_name,
        state_slug=allocation.state_slug,
        value=allocation.net_allocation,
        revenue_month=period.revenue_month,
        reporting_label=period.reporting_label,
    )


def _unsupported(question: str, year: int, coverage_label: str) -> GaiaAnalystResponse:
    return GaiaAnalystResponse(
        question=question,
        year=year,
        intent="unsupported",
        status="unsupported",
        answer=(
            "Gaia Analyst v1 cannot answer that question from its deterministic evidence set yet. "
            "Try asking about latest changes, rankings, deduction burden, volatility, momentum, "
            "or a comparison between two states."
        ),
        coverage_label=coverage_label,
        evidence=[],
        caveat=(
            "No external facts or causal explanations are substituted when the published ledger "
            "does not support the requested claim."
        ),
        suggested_questions=_suggested_questions(year),
    )


def _suggested_questions(year: int) -> list[str]:
    return [
        f"What changed in the latest published FAAC data for {year}?",
        f"What is Lagos's latest verified FAAC net allocation in {year}?",
        f"Which states received the highest net FAAC allocation in {year}?",
        f"Which states had the highest deduction burden in {year}?",
        f"Which states were the most volatile in {year}?",
        f"Which states have weakening momentum in {year}?",
        f"Compare Rivers and Lagos in {year}.",
    ]


def gaia_analyst(session: Session, *, question: str, year: int) -> GaiaAnalystResponse:
    pulse = fiscal_pulse(session, year)
    watch = fiscal_watch(session, year)
    lowered = question.strip().lower()

    if not pulse.states:
        return GaiaAnalystResponse(
            question=question,
            year=year,
            intent="unsupported",
            status="insufficient_data",
            answer=f"No published GaiaFAAC state allocation data is available for {year}.",
            coverage_label=pulse.coverage_label,
            evidence=[],
            caveat=pulse.note,
            suggested_questions=_suggested_questions(year),
        )

    state_match = _state_matches(lowered, pulse.states)
    asks_for_net = any(token in _slug_tokens(lowered) for token in ("net", "allocation", "faac"))

    if state_match.first is not None and "latest" in lowered and asks_for_net:
        latest = _latest_state_net(session, state=state_match.first, year=year)
        if latest is None:
            return GaiaAnalystResponse(
                question=question,
                year=year,
                intent="latest_state_net",
                status="insufficient_data",
                answer=(
                    f"No complete published {year} FAAC allocation is available for "
                    f"{state_match.first.state_name}."
                ),
                coverage_label=pulse.coverage_label,
                evidence=[],
                caveat=pulse.note,
                suggested_questions=_suggested_questions(year),
            )
        period_label = latest.revenue_month.strftime("%B %Y")
        return GaiaAnalystResponse(
            question=question,
            year=year,
            intent="latest_state_net",
            status="answered",
            answer=(
                f"{latest.state_name}'s latest verified net FAAC allocation is "
                f"{_money(latest.value)} for {period_label}."
            ),
            coverage_label=f"Latest complete published FAAC period · {period_label}",
            evidence=[
                GaiaAnalystEvidence(
                    state_name=latest.state_name,
                    state_slug=latest.state_slug,
                    label=f"{period_label} net FAAC allocation",
                    value=_money(latest.value),
                    metric="latest_net_allocation",
                    reference_path=(
                        f"/fiscal-proof/{latest.state_slug}/{latest.revenue_month.isoformat()}"
                    ),
                    reference_label="Verify with Fiscal Proof",
                    period_label=period_label,
                    relevant_date=latest.revenue_month.isoformat(),
                )
            ],
            caveat=(
                "This answer uses the latest complete, published jurisdiction allocation period "
                "for the requested year and does not substitute partial or unpublished data."
            ),
            suggested_questions=_suggested_questions(year),
        )

    if any(token in lowered for token in ("latest", "changed", "change", "watch", "alert")):
        if not watch.events:
            return GaiaAnalystResponse(
                question=question,
                year=year,
                intent="latest_changes",
                status="answered",
                answer=(
                    "No Fiscal Watch thresholds were triggered in the latest published month "
                    f"for {year}."
                ),
                coverage_label=pulse.coverage_label,
                evidence=[],
                caveat=watch.note,
                suggested_questions=_suggested_questions(year),
            )
        evidence = [
            GaiaAnalystEvidence(
                state_name=event.state_name,
                state_slug=event.state_slug,
                label=event.headline,
                value=event.detail,
                metric=event.kind,
                reference_path=event.proof_path,
                reference_label="Verify with Fiscal Proof",
            )
            for event in watch.events
        ]
        answer = " ".join(event.headline + "." for event in watch.events)
        return GaiaAnalystResponse(
            question=question,
            year=year,
            intent="latest_changes",
            status="answered",
            answer=answer,
            coverage_label=pulse.coverage_label,
            evidence=evidence,
            caveat=watch.note,
            suggested_questions=_suggested_questions(year),
        )

    if (
        state_match.first is not None
        and state_match.second is not None
        and any(token in lowered for token in ("compare", "versus", " vs ", "difference"))
    ):
        first = state_match.first
        second = state_match.second
        answer = (
            f"{first.state_name} has {_money(first.annual_net)} net allocation "
            "across the published "
            f"{year} months, versus {_money(second.annual_net)} for {second.state_name}. "
            f"Momentum is {first.momentum} for {first.state_name} and {second.momentum} for "
            f"{second.state_name}; volatility is {first.volatility} and {second.volatility}, "
            "respectively."
        )
        evidence = [
            _evidence(
                first, label="Published-period net", value=_money(first.annual_net), metric="net"
            ),
            _evidence(
                second, label="Published-period net", value=_money(second.annual_net), metric="net"
            ),
            _evidence(first, label="Momentum", value=first.momentum, metric="momentum"),
            _evidence(second, label="Momentum", value=second.momentum, metric="momentum"),
        ]
        return GaiaAnalystResponse(
            question=question,
            year=year,
            intent="compare",
            status="answered",
            answer=answer,
            coverage_label=pulse.coverage_label,
            evidence=evidence,
            caveat=pulse.note,
            suggested_questions=_suggested_questions(year),
        )

    if any(token in lowered for token in ("deduction", "deductions", "burden")):
        ranked = [state for state in pulse.states if state.deduction_burden_pct is not None]
        ranked.sort(key=lambda state: state.deduction_burden_pct or 0, reverse=True)
        ranked = ranked[:_TOP_N]
        evidence = [
            _evidence(
                state,
                label="Deduction burden",
                value=f"{state.deduction_burden_pct:.2f}%",
                metric="deduction_burden_pct",
            )
            for state in ranked
        ]
        answer = (
            "The highest deduction burdens are: "
            + "; ".join(f"{state.state_name} {state.deduction_burden_pct:.2f}%" for state in ranked)
            + "."
        )
        return GaiaAnalystResponse(
            question=question,
            year=year,
            intent="highest_deduction_burden",
            status="answered",
            answer=answer,
            coverage_label=pulse.coverage_label,
            evidence=evidence,
            caveat=pulse.note,
            suggested_questions=_suggested_questions(year),
        )

    if any(token in lowered for token in ("volatile", "volatility", "unstable")):
        ranked = [state for state in pulse.states if state.volatility_cv_pct is not None]
        ranked.sort(key=lambda state: state.volatility_cv_pct or 0, reverse=True)
        ranked = ranked[:_TOP_N]
        evidence = [
            _evidence(
                state,
                label="Volatility coefficient of variation",
                value=f"{state.volatility_cv_pct:.2f}%",
                metric="volatility_cv_pct",
            )
            for state in ranked
        ]
        answer = (
            "The most volatile published allocation series are: "
            + "; ".join(
                f"{state.state_name} {state.volatility_cv_pct:.2f}% ({state.volatility})"
                for state in ranked
            )
            + "."
        )
        return GaiaAnalystResponse(
            question=question,
            year=year,
            intent="most_volatile",
            status="answered",
            answer=answer,
            coverage_label=pulse.coverage_label,
            evidence=evidence,
            caveat=pulse.note,
            suggested_questions=_suggested_questions(year),
        )

    if any(token in lowered for token in ("momentum", "improving", "weakening", "stable")):
        requested_label = None
        if "weakening" in lowered:
            requested_label = "Weakening"
        elif "improving" in lowered:
            requested_label = "Improving"
        elif "stable" in lowered:
            requested_label = "Stable"
        ranked = [
            state
            for state in pulse.states
            if state.momentum_pct is not None
            and (requested_label is None or state.momentum == requested_label)
        ]
        ranked.sort(
            key=lambda state: state.momentum_pct or 0, reverse=requested_label != "Weakening"
        )
        ranked = ranked[:_TOP_N]
        evidence = [
            _evidence(
                state,
                label="Momentum",
                value=f"{state.momentum} ({state.momentum_pct:+.2f}%)",
                metric="momentum_pct",
            )
            for state in ranked
        ]
        if not ranked:
            answer = f"No states match that momentum condition in the published {year} data."
        else:
            answer = (
                "Momentum results: "
                + "; ".join(
                    f"{state.state_name} {state.momentum} ({state.momentum_pct:+.2f}%)"
                    for state in ranked
                )
                + "."
            )
        return GaiaAnalystResponse(
            question=question,
            year=year,
            intent="momentum",
            status="answered",
            answer=answer,
            coverage_label=pulse.coverage_label,
            evidence=evidence,
            caveat=pulse.note,
            suggested_questions=_suggested_questions(year),
        )

    if any(token in lowered for token in ("lowest", "least", "smallest")):
        ranked = [state for state in pulse.states if state.annual_net is not None]
        ranked.sort(key=lambda state: Decimal(state.annual_net or "0"))
        ranked = ranked[:_TOP_N]
        evidence = [
            _evidence(
                state, label="Published-period net", value=_money(state.annual_net), metric="net"
            )
            for state in ranked
        ]
        answer = (
            "The lowest net allocations across the published period are: "
            + "; ".join(f"{state.state_name} {_money(state.annual_net)}" for state in ranked)
            + "."
        )
        return GaiaAnalystResponse(
            question=question,
            year=year,
            intent="lowest_net",
            status="answered",
            answer=answer,
            coverage_label=pulse.coverage_label,
            evidence=evidence,
            caveat=pulse.note,
            suggested_questions=_suggested_questions(year),
        )

    if any(token in lowered for token in ("highest", "top", "largest", "most")) and any(
        token in lowered for token in ("allocation", "net", "received", "receive")
    ):
        ranked = [state for state in pulse.states if state.annual_net is not None][:_TOP_N]
        evidence = [
            _evidence(
                state, label="Published-period net", value=_money(state.annual_net), metric="net"
            )
            for state in ranked
        ]
        answer = (
            "The highest net allocations across the published period are: "
            + "; ".join(f"{state.state_name} {_money(state.annual_net)}" for state in ranked)
            + "."
        )
        return GaiaAnalystResponse(
            question=question,
            year=year,
            intent="top_net",
            status="answered",
            answer=answer,
            coverage_label=pulse.coverage_label,
            evidence=evidence,
            caveat=pulse.note,
            suggested_questions=_suggested_questions(year),
        )

    return _unsupported(question, year, pulse.coverage_label)
