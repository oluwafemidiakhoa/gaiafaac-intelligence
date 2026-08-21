from __future__ import annotations

from datetime import UTC, date, datetime, time
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.ledger_models import FiscalState
from gaiafaac_api.database.models import State
from gaiafaac_api.fiscal_intelligence_schemas import (
    FiscalComparisonData,
    FiscalComparisonEnvelope,
    FiscalIndexReadiness,
    IntelligenceEvidence,
    JurisdictionIntelligenceData,
    JurisdictionIntelligenceEnvelope,
)
from gaiafaac_api.fiscal_ledger_schemas import JurisdictionIdentity, LedgerMeta
from gaiafaac_api.ledger.cross_domain_intelligence import derive_cross_domain_metrics
from gaiafaac_api.ledger.intelligence import (
    DEFAULT_INTELLIGENCE_CONFIG,
    derive_faac_metrics,
)

INTELLIGENCE_SCHEMA_VERSION = "1.1.0"


def _state_record(
    session: Session, *, jurisdiction_code: str, as_of: date | datetime | None = None
) -> tuple[FiscalState, State] | None:
    code = jurisdiction_code.strip().upper().removeprefix("NG-")
    state = session.scalar(select(State).where(State.code == code))
    if state is None:
        return None
    query = select(FiscalState).where(FiscalState.state_id == state.id)
    if as_of is not None:
        if isinstance(as_of, datetime):
            if as_of.tzinfo is None or as_of.utcoffset() is None:
                raise ValueError("Datetime as_of values must include a timezone.")
            cutoff = as_of.astimezone(UTC)
        else:
            cutoff = datetime.combine(as_of, time.max, tzinfo=UTC)
        query = query.where(FiscalState.effective_at <= cutoff)
    record = session.scalar(
        query.order_by(FiscalState.effective_at.desc(), FiscalState.created_at.desc()).limit(1)
    )
    return (record, state) if record is not None else None


def jurisdiction_intelligence(
    session: Session, *, jurisdiction_code: str, as_of: date | datetime | None = None
) -> JurisdictionIntelligenceEnvelope | None:
    row = _state_record(session, jurisdiction_code=jurisdiction_code, as_of=as_of)
    if row is None:
        return None
    fiscal_state, state = row
    faac_domain = fiscal_state.domains.get("faac", {})
    faac_claims = faac_domain.get("claims", []) if isinstance(faac_domain, dict) else []
    if isinstance(faac_domain, dict) and faac_domain.get("status") == "conflicting":
        faac_claims = []
    metrics = derive_faac_metrics([claim for claim in faac_claims if isinstance(claim, dict)])
    metrics.extend(
        derive_cross_domain_metrics(
            fiscal_state.domains,
            fiscal_period=fiscal_state.fiscal_period,
        )
    )
    coverage = (
        format(fiscal_state.evidence_coverage, "f")
        if fiscal_state.evidence_coverage is not None
        else None
    )
    observed_coverage = Decimal(coverage) if coverage is not None else None
    missing_components = [
        metric["key"] for metric in metrics if metric["status"] == "insufficient_evidence"
    ]
    coverage_insufficient = (
        observed_coverage is None
        or observed_coverage < DEFAULT_INTELLIGENCE_CONFIG.minimum_resilience_coverage
    )
    reason = (
        "Evidence coverage is below the documented minimum."
        if coverage_insufficient
        else (
            "Required resilience components remain unavailable."
            if missing_components
            else "All currently defined resilience inputs are available; composite scoring remains disabled until its methodology is separately governed."
        )
    )
    data = JurisdictionIntelligenceData(
        fiscal_state_id=fiscal_state.fiscal_state_id,
        jurisdiction=JurisdictionIdentity(code=f"NG-{state.code.upper()}", name=state.name),
        fiscal_period=fiscal_state.fiscal_period,
        effective_at=(
            fiscal_state.effective_at.replace(tzinfo=UTC)
            if fiscal_state.effective_at.tzinfo is None
            else fiscal_state.effective_at.astimezone(UTC)
        ),
        ledger_status=fiscal_state.ledger_status,
        metrics=metrics,
        resilience=FiscalIndexReadiness(
            reason=reason,
            required_coverage=format(DEFAULT_INTELLIGENCE_CONFIG.minimum_resilience_coverage, "f"),
            observed_coverage=coverage,
            missing_components=missing_components,
        ),
    )
    return JurisdictionIntelligenceEnvelope(
        data=data,
        evidence=IntelligenceEvidence(
            evidence_coverage=coverage,
            evidence_integrity=fiscal_state.evidence_integrity,
            source_count=len(fiscal_state.sources),
            meaning=(
                "Derived metrics use exact stored claims and documented minimum evidence. "
                "Unavailable metrics are not estimated, annualized, or converted to zero. "
                "Cross-domain ratios require verified claims from the same fiscal period "
                "with compatible units or currency."
            ),
        ),
        meta=LedgerMeta(
            schema_version=INTELLIGENCE_SCHEMA_VERSION,
            methodology_version=DEFAULT_INTELLIGENCE_CONFIG.methodology_version,
        ),
    )


def compare_jurisdictions(
    session: Session,
    *,
    jurisdiction_codes: list[str],
    as_of: date | datetime | None = None,
) -> FiscalComparisonEnvelope:
    codes = list(dict.fromkeys(code.strip().upper() for code in jurisdiction_codes))
    if not 2 <= len(codes) <= 6:
        raise ValueError("Select between two and six unique jurisdictions.")
    records = [
        jurisdiction_intelligence(session, jurisdiction_code=code, as_of=as_of) for code in codes
    ]
    available = [record for record in records if record is not None]
    periods = {record.data.fiscal_period for record in available}
    return FiscalComparisonEnvelope(
        data=FiscalComparisonData(
            jurisdictions=[record.data for record in available],
            comparable_fiscal_period=(
                next(iter(periods)) if len(available) == len(codes) and len(periods) == 1 else None
            ),
        ),
        evidence={
            "requested_jurisdictions": codes,
            "unavailable_jurisdictions": [
                code for code, record in zip(codes, records, strict=True) if record is None
            ],
            "meaning": (
                "Metrics are displayed side by side. No rank or difference is calculated when "
                "Fiscal State periods differ or a metric is unavailable."
            ),
        },
        meta=LedgerMeta(
            schema_version=INTELLIGENCE_SCHEMA_VERSION,
            methodology_version=DEFAULT_INTELLIGENCE_CONFIG.methodology_version,
        ),
    )
