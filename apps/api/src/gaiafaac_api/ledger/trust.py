from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Protocol

from gaiafaac_api.database.enums import EvidenceStatus

COVERAGE_METHODOLOGY_VERSION = "gaia-evidence-coverage-v1"
INTEGRITY_METHODOLOGY_VERSION = "gaia-evidence-integrity-v1"

_ZERO = Decimal("0")
_ONE = Decimal("1")
_HUNDRED = Decimal("100")


class ClaimLike(Protocol):
    object_type: str
    fiscal_period: str


class VerificationLike(Protocol):
    source_verified: bool
    reconciled: bool | None
    human_reviewed: bool


@dataclass(frozen=True)
class EvidenceCoverageConfig:
    verified_weight: Decimal = _ONE
    partial_weight: Decimal = Decimal("0.5")
    methodology_version: str = COVERAGE_METHODOLOGY_VERSION


@dataclass(frozen=True)
class EvidenceIntegrityConfig:
    source_authenticity_weight: Decimal = Decimal("0.20")
    reconciliation_weight: Decimal = Decimal("0.20")
    verification_weight: Decimal = Decimal("0.20")
    temporal_completeness_weight: Decimal = Decimal("0.10")
    domain_completeness_weight: Decimal = Decimal("0.15")
    cross_source_agreement_weight: Decimal = Decimal("0.05")
    freshness_weight: Decimal = Decimal("0.10")
    minimum_available_weight: Decimal = Decimal("0.75")
    freshness_window_days: int = 90
    methodology_version: str = INTEGRITY_METHODOLOGY_VERSION

    def __post_init__(self) -> None:
        weights = self.weights()
        if any(weight < _ZERO for weight in weights.values()):
            raise ValueError("Evidence Integrity weights cannot be negative.")
        if sum(weights.values(), _ZERO) != _ONE:
            raise ValueError("Evidence Integrity weights must sum exactly to 1.0.")
        if not (_ZERO < self.minimum_available_weight <= _ONE):
            raise ValueError("Minimum available weight must be within (0, 1].")
        if self.freshness_window_days <= 0:
            raise ValueError("Freshness window must be positive.")

    def weights(self) -> dict[str, Decimal]:
        return {
            "source_authenticity": self.source_authenticity_weight,
            "reconciliation": self.reconciliation_weight,
            "human_verification": self.verification_weight,
            "temporal_completeness": self.temporal_completeness_weight,
            "domain_completeness": self.domain_completeness_weight,
            "cross_source_agreement": self.cross_source_agreement_weight,
            "data_freshness": self.freshness_weight,
        }


def _mean(values: Iterable[Decimal]) -> Decimal | None:
    items = list(values)
    if not items:
        return None
    return sum(items, _ZERO) / Decimal(len(items))


def _score(value: Decimal | None) -> dict[str, str | None]:
    if value is None:
        return {"score": None, "status": "insufficient_evidence"}
    bounded = max(_ZERO, min(_HUNDRED, value))
    return {
        "score": format(bounded.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), ".2f"),
        "status": "calculated",
    }


def calculate_evidence_coverage(
    domains: Mapping[str, Mapping[str, Any]],
    *,
    config: EvidenceCoverageConfig | None = None,
) -> dict[str, Any]:
    """Calculate equal-domain coverage without treating unavailable evidence as zero money."""

    selected = config or EvidenceCoverageConfig()
    if not domains:
        return {
            "score": None,
            "percent": None,
            "status": "insufficient_evidence",
            "methodology_version": selected.methodology_version,
            "domain_weights": {},
        }

    domain_weights: dict[str, str] = {}
    total = _ZERO
    for domain in sorted(domains):
        status = str(domains[domain].get("status", EvidenceStatus.UNAVAILABLE.value))
        if status == EvidenceStatus.VERIFIED.value:
            weight = selected.verified_weight
        elif status == EvidenceStatus.PARTIAL.value:
            weight = selected.partial_weight
        else:
            weight = _ZERO
        domain_weights[domain] = format(weight, "f")
        total += weight

    score = (total / Decimal(len(domains))).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    return {
        "score": format(score, ".4f"),
        "percent": format((score * _HUNDRED).quantize(Decimal("0.01")), ".2f"),
        "status": "calculated",
        "methodology_version": selected.methodology_version,
        "domain_weights": domain_weights,
    }


def _temporal_completeness(claims: Iterable[ClaimLike], effective_at: datetime) -> Decimal | None:
    expected_year = str(effective_at.year)
    months: set[int] = set()
    for claim in claims:
        if claim.object_type != "faac" or not claim.fiscal_period.startswith(f"{expected_year}-"):
            continue
        month_text = claim.fiscal_period[5:7]
        if month_text.isdigit() and 1 <= int(month_text) <= 12:
            months.add(int(month_text))
    if not months:
        return None
    expected_months = effective_at.month
    return min(_ONE, Decimal(len(months)) / Decimal(expected_months)) * _HUNDRED


def _freshness(
    sources: Iterable[Mapping[str, Any]], effective_at: datetime, window_days: int
) -> Decimal | None:
    scores: list[Decimal] = []
    for source in sources:
        raw_date = source.get("publication_date")
        if not isinstance(raw_date, str):
            continue
        try:
            publication_date = date.fromisoformat(raw_date)
        except ValueError:
            continue
        age = (effective_at.date() - publication_date).days
        if age < 0:
            continue
        remaining = max(0, window_days - age)
        scores.append(Decimal(remaining) / Decimal(window_days) * _HUNDRED)
    return _mean(scores)


def calculate_evidence_integrity(
    *,
    claims: Iterable[ClaimLike],
    verifications: Iterable[VerificationLike],
    domains: Mapping[str, Mapping[str, Any]],
    coverage: Mapping[str, Any],
    sources: Iterable[Mapping[str, Any]],
    unresolved_conflict_count: int,
    effective_at: datetime,
    config: EvidenceIntegrityConfig | None = None,
) -> dict[str, Any]:
    """Return a reproducible evidence-quality score, never a fiscal or credit rating."""

    selected = config or EvidenceIntegrityConfig()
    claim_items = list(claims)
    verification_items = list(verifications)
    source_items = list(sources)

    source_authenticity = _mean(
        _HUNDRED if item.source_verified else _ZERO for item in verification_items
    )
    reconciliation = _mean(
        _HUNDRED if item.reconciled else _ZERO
        for item in verification_items
        if item.reconciled is not None
    )
    human_verification = _mean(
        _HUNDRED if item.human_reviewed else _ZERO for item in verification_items
    )
    temporal_completeness = _temporal_completeness(claim_items, effective_at)
    coverage_score = coverage.get("score")
    domain_completeness = (
        Decimal(str(coverage_score)) * _HUNDRED if coverage_score is not None else None
    )
    publishers = {
        str(source["publisher"]).strip().casefold()
        for source in source_items
        if source.get("publisher")
    }
    cross_source_agreement = (
        _ZERO if unresolved_conflict_count else (_HUNDRED if len(publishers) >= 2 else None)
    )
    data_freshness = _freshness(source_items, effective_at, selected.freshness_window_days)

    raw_components = {
        "source_authenticity": source_authenticity,
        "reconciliation": reconciliation,
        "human_verification": human_verification,
        "temporal_completeness": temporal_completeness,
        "domain_completeness": domain_completeness,
        "cross_source_agreement": cross_source_agreement,
        "data_freshness": data_freshness,
    }
    components = {name: _score(value) for name, value in raw_components.items()}
    weights = selected.weights()
    available_weight = sum(
        (weights[name] for name, value in raw_components.items() if value is not None), _ZERO
    )
    required_components_available = all(
        raw_components[name] is not None
        for name in ("source_authenticity", "human_verification", "domain_completeness")
    )

    overall: Decimal | None = None
    if required_components_available and available_weight >= selected.minimum_available_weight:
        weighted_total = sum(
            (
                raw_components[name] * weights[name]
                for name in raw_components
                if raw_components[name] is not None
            ),
            _ZERO,
        )
        overall = weighted_total / available_weight

    result = _score(overall)
    return {
        **result,
        "methodology_version": selected.methodology_version,
        "available_weight": format(available_weight, "f"),
        "minimum_available_weight": format(selected.minimum_available_weight, "f"),
        "components": components,
        "note": (
            "Evidence Integrity measures Gaia's evidence quality, not fiscal health or credit risk."
        ),
    }
