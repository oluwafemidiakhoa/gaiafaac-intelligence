from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.models import State
from gaiafaac_api.gaia_analyst_schemas import GaiaAnalystEvidence, GaiaAnalystResponse
from gaiafaac_api.igr_schemas import PublishedIgrRecord
from gaiafaac_api.services.fiscal_intelligence import jurisdiction_intelligence
from gaiafaac_api.services.gaia_analyst import gaia_analyst as gaia_analyst_fa
from gaiafaac_api.services.published_data import get_published_overview, latest_published_period
from gaiafaac_api.services.published_igr import latest_published_igr, published_igr

_LEDGER_METRIC_LABELS = {
    "faac_dependence": "FAAC dependence",
    "faac_momentum": "FAAC momentum",
    "faac_volatility": "FAAC volatility",
    "debt_service_pressure": "Debt-service pressure",
    "faac_published_period_total": "Published FAAC total",
}
_DEBT_METRIC_KEYS = {"debt_service_pressure"}

_TOP_N = 5


@dataclass(frozen=True)
class _StateRef:
    name: str
    slug: str
    code: str


def _tokens(value: str) -> set[str]:
    return {token for token in re.split(r"[^a-z0-9]+", value.lower()) if token}


def _is_igr_question(question: str) -> bool:
    tokens = _tokens(question)
    return (
        "igr" in tokens
        or {"internally", "generated", "revenue"}.issubset(tokens)
        or {"internal", "revenue"}.issubset(tokens)
    )


def _state_refs(session: Session, records: list[PublishedIgrRecord]) -> list[_StateRef]:
    refs = {
        record.state_slug: _StateRef(record.state_name, record.state_slug, record.state_code)
        for record in records
    }
    for state in session.scalars(select(State).order_by(State.name)).all():
        refs.setdefault(state.slug, _StateRef(state.name, state.slug, state.code))
    return list(refs.values())


def _match_states(question: str, refs: list[_StateRef]) -> list[_StateRef]:
    lowered = question.lower()
    question_tokens = _tokens(question)
    matches: list[_StateRef] = []
    for state in refs:
        named = state.name.lower() in lowered or state.slug.lower() in lowered
        coded = state.code.lower() in question_tokens
        fct = state.code == "FC" and bool(
            {"fct", "abuja"} & question_tokens or "federal capital territory" in lowered
        )
        token_named = _tokens(state.name).issubset(question_tokens)
        if named or coded or fct or token_named:
            matches.append(state)
    unique: list[_StateRef] = []
    seen: set[str] = set()
    for state in matches:
        if state.slug not in seen:
            unique.append(state)
            seen.add(state.slug)
    return unique


def _money(record: PublishedIgrRecord) -> str:
    amount = f"{Decimal(record.igr_amount):,.2f}"
    if record.reported_unit.lower() in {"naira", "ngn"}:
        return f"NGN {amount}"
    return f"{amount} {record.reported_unit}"


def _period_label(record: PublishedIgrRecord) -> str:
    if record.period_type == "annual":
        return f"{record.fiscal_year} annual"
    if record.period_type == "quarterly" and record.quarter is not None:
        return f"{record.fiscal_year} Q{record.quarter}"
    return f"{record.period_start.isoformat()} to {record.period_end.isoformat()}"


def _period_key(record: PublishedIgrRecord) -> tuple[object, ...]:
    return record.period_type, record.quarter, record.period_start, record.period_end


def _evidence(record: PublishedIgrRecord) -> GaiaAnalystEvidence:
    label = _period_label(record)
    return GaiaAnalystEvidence(
        state_name=record.state_name,
        state_slug=record.state_slug,
        label=f"{label} IGR",
        value=_money(record),
        metric="igr_amount",
        reference_path=f"/states/{record.state_slug}",
        reference_label="Open state record",
        evidence_domain="igr",
        period_label=label,
        source_organization=record.source.organization,
        source_sha256=record.source.sha256,
    )


def _caveat() -> str:
    return (
        "IGR answers use only published, non-demo, human-verified records. Gaia Analyst does not "
        "infer missing periods, annualize partial-year values, borrow evidence from another year, "
        "or compare mismatched fiscal periods."
    )


def _faac_money(value: str | None) -> str:
    if value is None:
        return "unavailable"
    return f"NGN {Decimal(value):,.2f}"


def _faac_snapshot(
    session: Session, *, state: _StateRef, year: int
) -> tuple[str, GaiaAnalystEvidence] | None:
    """The latest verified FAAC net allocation for a state, if one is published for `year`."""
    period = latest_published_period(session)
    if period is None or period.revenue_month.year != year:
        return None
    overview = get_published_overview(session, period)
    if overview is None:
        return None
    allocation = next(
        (item for item in overview.allocations if item.state_slug == state.slug), None
    )
    if allocation is None or allocation.net_allocation is None:
        return None
    label = period.revenue_month.strftime("%B %Y")
    money = _faac_money(allocation.net_allocation)
    text = f"the latest verified FAAC net allocation is {money} ({label})"
    evidence = GaiaAnalystEvidence(
        state_name=state.name,
        state_slug=state.slug,
        label=f"{label} net FAAC allocation",
        value=money,
        metric="latest_net_allocation",
        reference_path=f"/states/{state.slug}",
        reference_label="Open state record",
        evidence_domain="faac",
        period_label=label,
        source_organization=overview.source.source_organization,
        source_sha256=overview.source.sha256,
        relevant_date=period.revenue_month.isoformat(),
    )
    return text, evidence


def _igr_snapshot(session: Session, *, state: _StateRef) -> tuple[str, GaiaAnalystEvidence] | None:
    """The latest published IGR record for a state, regardless of its fiscal period."""
    record = latest_published_igr(session, state_slug=state.slug)
    if record is None:
        return None
    text = f"the latest published IGR is {_money(record)} ({_period_label(record)})"
    return text, _evidence(record)


def _ledger_metric_fallback(
    session: Session,
    *,
    question: str,
    year: int,
    state: _StateRef,
    requested_key: str,
    reason: str,
) -> GaiaAnalystResponse:
    """A composite ledger metric (e.g. FAAC dependence) could not be calculated as a single
    ratio. Rather than dead-end, surface whatever real component evidence is verified so the
    question isn't left with nothing - without inventing or combining mismatched periods."""
    parts: list[str] = []
    evidence: list[GaiaAnalystEvidence] = []
    faac = _faac_snapshot(session, state=state, year=year)
    if faac is not None:
        parts.append(faac[0])
        evidence.append(faac[1])
    if requested_key in _DEBT_METRIC_KEYS:
        why = "no verified DMO debt evidence has been published yet"
    else:
        igr = _igr_snapshot(session, state=state)
        if igr is not None:
            parts.append(igr[0])
            evidence.append(igr[1])
        why = (
            "combining FAAC and IGR across mismatched monthly and annual periods "
            "is not done automatically"
        )
    label = _LEDGER_METRIC_LABELS.get(requested_key, requested_key)
    if evidence:
        answer = (
            f"Gaia does not yet calculate a single {label} ratio for {state.name} ({why}). "
            f"Here is what is verified instead: {'; '.join(parts)}."
        )
        coverage_label = f"{label} · component evidence only"
    else:
        answer = reason
        coverage_label = f"{label} unavailable"
    return _response(
        question=question,
        year=year,
        intent="ledger_metric",
        status="insufficient_data",
        answer=answer,
        coverage_label=coverage_label,
        evidence=evidence,
    )


def _suggestions(year: int) -> list[str]:
    return [
        f"What is Lagos IGR in {year}?",
        "What is the latest published IGR for Lagos?",
        f"Which states had the highest IGR in {year}?",
        f"Which states had the lowest IGR in {year}?",
        f"Compare Rivers and Lagos IGR in {year}.",
        f"What changed in the latest published FAAC data for {year}?",
    ]


def _response(
    *,
    question: str,
    year: int,
    intent: str,
    status: str,
    answer: str,
    coverage_label: str,
    evidence: list[GaiaAnalystEvidence],
) -> GaiaAnalystResponse:
    return GaiaAnalystResponse(
        question=question,
        year=year,
        intent=intent,
        status=status,
        answer=answer,
        coverage_label=coverage_label,
        evidence=evidence,
        caveat=_caveat(),
        suggested_questions=_suggestions(year),
    )


def _comparable_group(records: list[PublishedIgrRecord]) -> list[PublishedIgrRecord]:
    groups: dict[tuple[object, ...], dict[str, PublishedIgrRecord]] = {}
    for record in records:
        groups.setdefault(_period_key(record), {})[record.state_slug] = record
    candidates = [list(group.values()) for group in groups.values()]
    if not candidates:
        return []
    return max(
        candidates,
        key=lambda group: (len(group), group[0].period_end, group[0].period_start),
    )


def _common_pair(
    records: list[PublishedIgrRecord], first_slug: str, second_slug: str
) -> tuple[PublishedIgrRecord, PublishedIgrRecord] | None:
    first = {_period_key(record): record for record in records if record.state_slug == first_slug}
    second = {_period_key(record): record for record in records if record.state_slug == second_slug}
    pairs = [(first[key], second[key]) for key in first.keys() & second.keys()]
    return (
        max(pairs, key=lambda pair: (pair[0].period_end, pair[0].period_start)) if pairs else None
    )


def _state_record(records: list[PublishedIgrRecord], state_slug: str) -> PublishedIgrRecord | None:
    candidates = [record for record in records if record.state_slug == state_slug]
    if not candidates:
        return None
    annual = [record for record in candidates if record.period_type == "annual"]
    return max(annual or candidates, key=lambda record: (record.period_end, record.period_start))


def _igr_answer(session: Session, *, question: str, year: int) -> GaiaAnalystResponse:
    lowered = question.strip().lower()
    published = published_igr(session, year=year)
    records = published.records
    states = _match_states(question, _state_refs(session, records))
    coverage = f"Published {year} IGR · {len(records)} verified records"

    if "latest" in lowered:
        if not states:
            return _response(
                question=question,
                year=year,
                intent="igr_latest",
                status="unsupported",
                answer="Name a state when asking for the latest published IGR record.",
                coverage_label=coverage,
                evidence=[],
            )
        record = latest_published_igr(session, state_slug=states[0].slug)
        if record is None:
            return _response(
                question=question,
                year=year,
                intent="igr_latest",
                status="insufficient_data",
                answer=f"No published, human-verified IGR evidence exists for {states[0].name}.",
                coverage_label="No published IGR record",
                evidence=[],
            )
        label = _period_label(record)
        answer = f"The latest published IGR for {record.state_name} is {label}: {_money(record)}."
        return _response(
            question=question,
            year=year,
            intent="igr_latest",
            status="answered",
            answer=answer,
            coverage_label=f"Latest published IGR · {label}",
            evidence=[_evidence(record)],
        )

    if any(token in lowered for token in ("compare", "versus", " vs ", "difference")):
        if len(states) < 2:
            return _response(
                question=question,
                year=year,
                intent="igr_compare",
                status="unsupported",
                answer="Name two states when asking Gaia Analyst to compare IGR.",
                coverage_label=coverage,
                evidence=[],
            )
        pair = _common_pair(records, states[0].slug, states[1].slug)
        if pair is None:
            return _response(
                question=question,
                year=year,
                intent="igr_compare",
                status="insufficient_data",
                answer=(
                    f"No common published IGR period is available for {states[0].name} and "
                    f"{states[1].name} in {year}."
                ),
                coverage_label=coverage,
                evidence=[],
            )
        first, second = pair
        if first.reported_unit != second.reported_unit:
            answer = "The matching IGR records use different reported units and are not compared."
            return _response(
                question=question,
                year=year,
                intent="igr_compare",
                status="insufficient_data",
                answer=answer,
                coverage_label=coverage,
                evidence=[_evidence(first), _evidence(second)],
            )
        label = _period_label(first)
        return _response(
            question=question,
            year=year,
            intent="igr_compare",
            status="answered",
            answer=(
                f"For {label}, {first.state_name} reported {_money(first)} in IGR, versus "
                f"{_money(second)} for {second.state_name}."
            ),
            coverage_label=f"Published {label} IGR · 2 states",
            evidence=[_evidence(first), _evidence(second)],
        )

    ranking_intent = None
    reverse = False
    if any(token in lowered for token in ("highest", "top", "largest", "most")):
        ranking_intent = "igr_top"
        reverse = True
    elif any(token in lowered for token in ("lowest", "least", "smallest")):
        ranking_intent = "igr_lowest"

    if ranking_intent is not None:
        comparable = _comparable_group(records)
        if not comparable:
            return _response(
                question=question,
                year=year,
                intent=ranking_intent,
                status="insufficient_data",
                answer=f"No published IGR evidence is available for {year}.",
                coverage_label=coverage,
                evidence=[],
            )
        if len({record.reported_unit for record in comparable}) != 1:
            answer = "The comparable IGR records use different reported units and are not ranked."
            return _response(
                question=question,
                year=year,
                intent=ranking_intent,
                status="insufficient_data",
                answer=answer,
                coverage_label=coverage,
                evidence=[],
            )
        ranked = sorted(
            comparable,
            key=lambda record: Decimal(record.igr_amount),
            reverse=reverse,
        )[:_TOP_N]
        label = _period_label(ranked[0])
        direction = "highest" if reverse else "lowest"
        answer = (
            f"The {direction} published IGR values for {label} are: "
            + "; ".join(f"{record.state_name} {_money(record)}" for record in ranked)
            + "."
        )
        return _response(
            question=question,
            year=year,
            intent=ranking_intent,
            status="answered",
            answer=answer,
            coverage_label=f"Published {label} IGR · {len(comparable)} states",
            evidence=[_evidence(record) for record in ranked],
        )

    if states:
        record = _state_record(records, states[0].slug)
        if record is None:
            return _response(
                question=question,
                year=year,
                intent="igr_state",
                status="insufficient_data",
                answer=(
                    f"No published, human-verified IGR evidence is available for "
                    f"{states[0].name} in {year}."
                ),
                coverage_label=coverage,
                evidence=[],
            )
        label = _period_label(record)
        return _response(
            question=question,
            year=year,
            intent="igr_state",
            status="answered",
            answer=f"{record.state_name} has a published {label} IGR record of {_money(record)}.",
            coverage_label=f"Published {label} IGR · {record.state_name}",
            evidence=[_evidence(record)],
        )

    return _response(
        question=question,
        year=year,
        intent="unsupported",
        status="unsupported",
        answer=(
            "Gaia Analyst can answer published IGR questions for a named state, rank states within "
            "a comparable fiscal period, or compare two states with matching period evidence."
        ),
        coverage_label=coverage,
        evidence=[],
    )


def gaia_analyst(session: Session, *, question: str, year: int) -> GaiaAnalystResponse:
    tokens = _tokens(question)
    metric_keys = {
        "dependence": "faac_dependence",
        "momentum": "faac_momentum",
        "volatility": "faac_volatility",
        "pressure": "debt_service_pressure",
        "coverage": "faac_published_period_total",
    }
    requested_key = next((value for key, value in metric_keys.items() if key in tokens), None)
    ledger_language = bool(tokens & {"ledger", "evidence", "dependence", "resilience", "pressure"})
    if requested_key is not None and ledger_language:
        refs = _state_refs(session, [])
        states = _match_states(question, refs)
        if not states:
            return _response(
                question=question,
                year=year,
                intent="ledger_metric",
                status="insufficient_data",
                answer="Name a jurisdiction to inspect its published Fiscal State intelligence.",
                coverage_label="Jurisdiction required",
                evidence=[],
            )
        intelligence = jurisdiction_intelligence(session, jurisdiction_code=f"NG-{states[0].code}")
        if intelligence is None:
            return _ledger_metric_fallback(
                session,
                question=question,
                year=year,
                state=states[0],
                requested_key=requested_key,
                reason=f"No published Fiscal State is available for {states[0].name}.",
            )
        metric = next(item for item in intelligence.data.metrics if item.key == requested_key)
        available = metric.status == "calculated" and metric.value is not None
        if not available:
            return _ledger_metric_fallback(
                session,
                question=question,
                year=year,
                state=states[0],
                requested_key=requested_key,
                reason=(
                    f"{metric.label} for {states[0].name} cannot be calculated from "
                    f"the current verified evidence. {metric.explanation}"
                ),
            )
        return _response(
            question=question,
            year=year,
            intent="ledger_metric",
            status="answered",
            answer=f"{metric.label} for {states[0].name} is {metric.value} {metric.unit}.",
            coverage_label=f"Fiscal State · {intelligence.data.fiscal_period}",
            evidence=[
                GaiaAnalystEvidence(
                    state_name=states[0].name,
                    state_slug=states[0].slug,
                    label=metric.label,
                    value=metric.value or "Unavailable",
                    metric=metric.key,
                    reference_path=f"/jurisdictions/NG-{states[0].code}",
                    reference_label="Open Fiscal State",
                    evidence_domain="ledger",
                    period_label=metric.fiscal_period,
                    gaia_object_id=intelligence.data.fiscal_state_id,
                    evidence_status=intelligence.data.ledger_status,
                    relevant_date=intelligence.data.effective_at.date().isoformat(),
                )
            ],
        )
    if _is_igr_question(question):
        return _igr_answer(session, question=question, year=year)
    return gaia_analyst_fa(session, question=question, year=year)
