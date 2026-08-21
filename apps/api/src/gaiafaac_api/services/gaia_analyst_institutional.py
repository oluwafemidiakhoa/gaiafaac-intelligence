from __future__ import annotations

import re
from datetime import UTC, datetime, time

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.models import State
from gaiafaac_api.gaia_analyst_schemas import GaiaAnalystEvidence, GaiaAnalystResponse
from gaiafaac_api.services.fiscal_intelligence import jurisdiction_intelligence
from gaiafaac_api.services.gaia_analyst_igr import gaia_analyst as legacy_gaia_analyst
from gaiafaac_api.services.temporal_intelligence import temporal_fiscal_snapshot

_DATE = re.compile(r"\b(20\d{2})-(0[1-9]|1[0-2])-([0-2]\d|3[01])\b")
_METRIC_HINTS = {
    "dependence": "faac_dependence",
    "debt burden": "debt_burden",
    "debt-service pressure": "debt_service_pressure",
    "debt service pressure": "debt_service_pressure",
    "budget execution": "budget_execution",
    "capital execution": "capital_execution",
    "liability burden": "liability_burden",
    "momentum": "faac_momentum",
    "volatility": "faac_volatility",
    "coverage": "faac_published_period_total",
}
_DOMAIN_HINTS = {
    "faac": "faac",
    "igr": "igr",
    "internal revenue": "igr",
    "debt service": "debt_service",
    "debt-service": "debt_service",
    "debt": "debt",
    "budget": "budget",
    "expenditure": "expenditure",
    "spending": "expenditure",
    "liabilities": "liabilities",
    "liability": "liabilities",
}


def _question_tokens(question: str) -> set[str]:
    return {token for token in re.split(r"[^a-z0-9]+", question.lower()) if token}


def _state(session: Session, question: str) -> State | None:
    lowered = question.lower()
    tokens = _question_tokens(question)
    states = session.scalars(select(State).order_by(State.name.desc())).all()
    for state in states:
        named = state.name.lower() in lowered or state.slug.lower() in lowered
        coded = state.code.lower() in tokens
        fct = state.code == "FC" and bool(
            {"fct", "abuja"} & tokens or "federal capital territory" in lowered
        )
        if named or coded or fct:
            return state
    return None


def _metric_key(question: str) -> str | None:
    lowered = question.lower()
    return next((metric for hint, metric in _METRIC_HINTS.items() if hint in lowered), None)


def _domain(question: str) -> str | None:
    lowered = question.lower()
    return next((domain for hint, domain in _DOMAIN_HINTS.items() if hint in lowered), None)


def _known_date(question: str) -> datetime | None:
    match = _DATE.search(question)
    if match is None:
        return None
    try:
        value = datetime.strptime(match.group(0), "%Y-%m-%d").date()
    except ValueError:
        return None
    return datetime.combine(value, time.max, tzinfo=UTC)


def _ledger_metric_answer(
    session: Session,
    *,
    question: str,
    year: int,
    state: State,
    metric_key: str,
) -> GaiaAnalystResponse:
    intelligence = jurisdiction_intelligence(session, jurisdiction_code=f"NG-{state.code}")
    if intelligence is None:
        return GaiaAnalystResponse(
            question=question,
            year=year,
            intent="ledger_metric",
            status="insufficient_data",
            answer=f"No published Fiscal State is available for {state.name}.",
            coverage_label="Fiscal State unavailable",
            evidence=[],
            caveat="Gaia Analyst does not invent missing fiscal evidence.",
            suggested_questions=[],
        )
    metric = next((item for item in intelligence.data.metrics if item.key == metric_key), None)
    if metric is None:
        return legacy_gaia_analyst(session, question=question, year=year)
    available = metric.status == "calculated" and metric.value is not None
    evidence = [
        GaiaAnalystEvidence(
            state_name=state.name,
            state_slug=state.slug,
            label=metric.label,
            value=metric.value or "Unavailable",
            metric=metric.key,
            reference_path=f"/jurisdictions/NG-{state.code}",
            reference_label="Open Fiscal State",
            evidence_domain="ledger",
            period_label=metric.fiscal_period,
            gaia_object_id=intelligence.data.fiscal_state_id,
            evidence_status=str(intelligence.data.ledger_status),
            relevant_date=intelligence.data.effective_at.date().isoformat(),
        )
    ]
    return GaiaAnalystResponse(
        question=question,
        year=year,
        intent="ledger_metric",
        status="answered" if available else "insufficient_data",
        answer=(
            f"{metric.label} for {state.name} is {metric.value} {metric.unit}."
            if available
            else (
                f"{metric.label} for {state.name} cannot be calculated from the current verified "
                f"evidence. {metric.explanation}"
            )
        ),
        coverage_label=f"Fiscal State · {intelligence.data.fiscal_period}",
        evidence=evidence,
        caveat=(
            "This answer is deterministic arithmetic over the cited Fiscal State. Missing, "
            "conflicting, cross-period or currency-incompatible evidence is not estimated."
        ),
        suggested_questions=[
            f"What is the debt burden for {state.name}?",
            f"What is the debt service pressure for {state.name}?",
            f"What is the budget execution rate for {state.name}?",
        ],
    )


def _temporal_answer(
    session: Session,
    *,
    question: str,
    year: int,
    state: State,
    known_as_of: datetime,
    domain: str | None,
) -> GaiaAnalystResponse:
    snapshot = temporal_fiscal_snapshot(
        session,
        jurisdiction_code=f"NG-{state.code}",
        effective_as_of=known_as_of,
        known_as_of=known_as_of,
    )
    if snapshot is None:
        return GaiaAnalystResponse(
            question=question,
            year=year,
            intent="temporal_metric",
            status="insufficient_data",
            answer=f"No temporal fiscal evidence is available for {state.name}.",
            coverage_label=f"Known as of {known_as_of.date().isoformat()}",
            evidence=[],
            caveat="No missing historical value was inferred.",
            suggested_questions=[],
        )
    claims = (
        snapshot.data.domains.get(domain, [])
        if domain is not None
        else [claim for items in snapshot.data.domains.values() for claim in items]
    )
    if not claims:
        label = domain.replace("_", " ") if domain else "fiscal"
        return GaiaAnalystResponse(
            question=question,
            year=year,
            intent="temporal_metric",
            status="insufficient_data",
            answer=(
                f"Gaia had no governed {label} claim for {state.name} that was both effective and "
                f"known by {known_as_of.date().isoformat()}."
            ),
            coverage_label=f"Known as of {known_as_of.date().isoformat()}",
            evidence=[],
            caveat="Future revisions are not backfilled into this historical knowledge view.",
            suggested_questions=[],
        )
    evidence = [
        GaiaAnalystEvidence(
            state_name=state.name,
            state_slug=state.slug,
            label=claim.metric.replace("_", " ").title(),
            value=f"{claim.value or 'Unavailable'} {claim.currency or claim.unit}",
            metric=claim.metric,
            reference_path=None,
            reference_label=None,
            evidence_domain="ledger",
            period_label=claim.fiscal_period,
            source_organization=claim.source_publisher,
            source_sha256=claim.source_sha256,
            gaia_object_id=claim.gaia_id,
            evidence_status=str(claim.evidence_status),
            relevant_date=claim.effective_at.date().isoformat(),
        )
        for claim in claims[:10]
    ]
    claim_summary = "; ".join(
        f"{item.metric.replace('_', ' ')} = {item.value or 'Unavailable'} {item.currency or item.unit}"
        for item in claims[:5]
    )
    return GaiaAnalystResponse(
        question=question,
        year=year,
        intent="temporal_metric",
        status="answered",
        answer=(
            f"As Gaia knew on {known_as_of.date().isoformat()}, {state.name} had: {claim_summary}."
        ),
        coverage_label=(
            f"Bitemporal snapshot · {len(claims)} governed claim{'s' if len(claims) != 1 else ''}"
        ),
        evidence=evidence,
        caveat=(
            "This answer uses only claims published by the requested knowledge date and effective "
            "by that date. Later revisions are intentionally excluded."
        ),
        suggested_questions=[
            f"What did Gaia know about {state.name} debt as of {known_as_of.date().isoformat()}?",
            f"What is the latest debt burden for {state.name}?",
        ],
    )


def gaia_analyst(session: Session, *, question: str, year: int) -> GaiaAnalystResponse:
    state = _state(session, question)
    lowered = question.lower()
    known_as_of = _known_date(question)
    temporal_language = any(
        phrase in lowered
        for phrase in ("as of", "what did gaia know", "known on", "known by", "at that time")
    )
    if state is not None and known_as_of is not None and temporal_language:
        return _temporal_answer(
            session,
            question=question,
            year=year,
            state=state,
            known_as_of=known_as_of,
            domain=_domain(question),
        )

    metric_key = _metric_key(question)
    ledger_language = any(
        phrase in lowered
        for phrase in (
            "dependence",
            "debt burden",
            "debt service pressure",
            "debt-service pressure",
            "budget execution",
            "capital execution",
            "liability burden",
            "resilience",
            "ledger",
        )
    )
    if state is not None and metric_key is not None and ledger_language:
        return _ledger_metric_answer(
            session,
            question=question,
            year=year,
            state=state,
            metric_key=metric_key,
        )
    return legacy_gaia_analyst(session, question=question, year=year)
