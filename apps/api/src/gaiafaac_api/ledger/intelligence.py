from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Any


@dataclass(frozen=True)
class FiscalIntelligenceConfig:
    methodology_version: str = "gaia-fiscal-intelligence-v1"
    event_methodology_version: str = "gaia-fiscal-event-classification-v1"
    monthly_move_threshold_percent: Decimal = Decimal("25.000000")
    momentum_threshold_percent: Decimal = Decimal("5.000000")
    volatility_low_threshold_percent: Decimal = Decimal("10.000000")
    volatility_high_threshold_percent: Decimal = Decimal("25.000000")
    minimum_resilience_coverage: Decimal = Decimal("0.75")

    def __post_init__(self) -> None:
        if self.monthly_move_threshold_percent <= 0:
            raise ValueError("Monthly event threshold must be positive.")
        if not Decimal("0") <= self.minimum_resilience_coverage <= Decimal("1"):
            raise ValueError("Minimum resilience coverage must be between zero and one.")


DEFAULT_INTELLIGENCE_CONFIG = FiscalIntelligenceConfig()
_HUNDRED = Decimal("100")
_SIX_PLACES = Decimal("0.000001")
_TWO_PLACES = Decimal("0.01")


def _percent(value: Decimal) -> str:
    return format(value.quantize(_SIX_PLACES, rounding=ROUND_HALF_UP), "f")


def _month(value: str) -> date | None:
    try:
        year, month = value.split("-")
        return date(int(year), int(month), 1)
    except (TypeError, ValueError):
        return None


def consecutive_months(periods: list[str]) -> bool:
    parsed = [_month(period) for period in periods]
    if any(item is None for item in parsed):
        return False
    concrete = [item for item in parsed if item is not None]
    return all(
        (right.year * 12 + right.month) - (left.year * 12 + left.month) == 1
        for left, right in zip(concrete, concrete[1:], strict=False)
    )


def classify_faac_monthly_change(
    *,
    previous_period: str,
    previous_value: str | None,
    current_period: str,
    current_value: str | None,
    config: FiscalIntelligenceConfig = DEFAULT_INTELLIGENCE_CONFIG,
) -> dict[str, Any] | None:
    if (
        previous_value is None
        or current_value is None
        or not consecutive_months([previous_period, current_period])
    ):
        return None
    previous = Decimal(previous_value)
    current = Decimal(current_value)
    if previous == 0:
        return None
    change = (current - previous) / abs(previous) * _HUNDRED
    if abs(change) < config.monthly_move_threshold_percent:
        return None
    change_text = _percent(change)
    direction = "increased" if change > 0 else "decreased"
    return {
        "event_type": "faac_spike" if change > 0 else "faac_decline",
        "change_percent": change_text,
        "previous_period": previous_period,
        "current_period": current_period,
        "previous_value": previous_value,
        "current_value": current_value,
        "threshold_percent": format(config.monthly_move_threshold_percent, "f"),
        "explanation": (
            f"FAAC net allocation {direction} {abs(Decimal(change_text)):.6f}% "
            "from the prior consecutive published month."
        ),
    }


def derive_faac_metrics(
    claims: list[dict[str, Any]],
    *,
    config: FiscalIntelligenceConfig = DEFAULT_INTELLIGENCE_CONFIG,
) -> list[dict[str, Any]]:
    eligible = sorted(
        (
            claim
            for claim in claims
            if claim.get("status") == "verified"
            and isinstance(claim.get("value"), str)
            and _month(str(claim.get("fiscal_period"))) is not None
        ),
        key=lambda claim: str(claim["fiscal_period"]),
    )
    units = {(claim.get("currency"), claim.get("unit")) for claim in eligible}
    compatible = len(units) <= 1
    if not compatible:
        eligible = []
    evidence_ids = [str(claim["gaia_id"]) for claim in eligible]
    values = [Decimal(str(claim["value"])) for claim in eligible]
    periods = [str(claim["fiscal_period"]) for claim in eligible]
    metrics: list[dict[str, Any]] = []
    display_unit = (
        str(eligible[0].get("currency") or eligible[0].get("unit")) if eligible else "unavailable"
    )

    if values:
        metrics.append(
            {
                "key": "faac_published_period_total",
                "status": "calculated",
                "value": format(sum(values, Decimal("0")).quantize(_TWO_PLACES), "f"),
                "unit": display_unit,
                "label": "FAAC total across included verified months",
                "fiscal_period": f"{periods[0]} to {periods[-1]}",
                "evidence_ids": evidence_ids,
                "explanation": (
                    f"Exact sum of {len(values)} verified monthly net-allocation claims; "
                    "missing months are not inferred or annualized."
                ),
            }
        )
    else:
        metrics.append(
            {
                "key": "faac_published_period_total",
                "status": "insufficient_evidence",
                "value": None,
                "unit": "unavailable",
                "label": "FAAC total across included verified months",
                "fiscal_period": None,
                "evidence_ids": [],
                "explanation": (
                    "Verified monthly FAAC claims use incompatible units or currencies."
                    if not compatible
                    else "No verified monthly FAAC claims are present in this Fiscal State."
                ),
            }
        )

    if len(values) >= 2 and consecutive_months(periods[-2:]) and values[-2] != 0:
        change = (values[-1] - values[-2]) / abs(values[-2]) * _HUNDRED
        metrics.append(
            {
                "key": "faac_month_over_month_change",
                "status": "calculated",
                "value": _percent(change),
                "unit": "percent",
                "label": "FAAC month-over-month change",
                "fiscal_period": periods[-1],
                "evidence_ids": evidence_ids[-2:],
                "explanation": "Exact change between the latest two consecutive verified months.",
            }
        )
    else:
        metrics.append(
            {
                "key": "faac_month_over_month_change",
                "status": "insufficient_evidence",
                "value": None,
                "unit": "percent",
                "label": "FAAC month-over-month change",
                "fiscal_period": periods[-1] if periods else None,
                "evidence_ids": evidence_ids[-2:],
                "explanation": (
                    "Two consecutive verified monthly claims with a non-zero prior "
                    "value are required."
                ),
            }
        )

    recent_periods = periods[-6:]
    recent_values = values[-6:]
    momentum_calculated = False
    if len(recent_values) == 6 and consecutive_months(recent_periods):
        previous_mean = sum(recent_values[:3], Decimal("0")) / Decimal("3")
        current_mean = sum(recent_values[3:], Decimal("0")) / Decimal("3")
        if previous_mean != 0:
            momentum = (current_mean - previous_mean) / abs(previous_mean) * _HUNDRED
            label = (
                "increasing"
                if momentum > config.momentum_threshold_percent
                else ("decreasing" if momentum < -config.momentum_threshold_percent else "stable")
            )
            metrics.append(
                {
                    "key": "faac_momentum",
                    "status": "calculated",
                    "value": _percent(momentum),
                    "unit": "percent",
                    "label": f"FAAC momentum · {label}",
                    "fiscal_period": f"{recent_periods[0]} to {recent_periods[-1]}",
                    "evidence_ids": evidence_ids[-6:],
                    "explanation": (
                        "Compares the exact mean of the latest three verified months with the "
                        "preceding three consecutive verified months."
                    ),
                }
            )
            momentum_calculated = True
    if not momentum_calculated:
        metrics.append(
            {
                "key": "faac_momentum",
                "status": "insufficient_evidence",
                "value": None,
                "unit": "percent",
                "label": "FAAC momentum",
                "fiscal_period": periods[-1] if periods else None,
                "evidence_ids": evidence_ids[-6:],
                "explanation": "Six consecutive verified monthly claims are required.",
            }
        )

    volatility_values = values[-12:]
    volatility_periods = periods[-12:]
    if len(volatility_values) >= 3 and consecutive_months(volatility_periods):
        average = sum(volatility_values, Decimal("0")) / Decimal(len(volatility_values))
        if average > 0:
            variance = sum(
                ((value - average) ** 2 for value in volatility_values), Decimal("0")
            ) / Decimal(len(volatility_values))
            coefficient = variance.sqrt() / average * _HUNDRED
            label = (
                "low"
                if coefficient < config.volatility_low_threshold_percent
                else (
                    "moderate" if coefficient < config.volatility_high_threshold_percent else "high"
                )
            )
            metrics.append(
                {
                    "key": "faac_volatility",
                    "status": "calculated",
                    "value": _percent(coefficient),
                    "unit": "percent_cv",
                    "label": f"FAAC volatility · {label}",
                    "fiscal_period": f"{volatility_periods[0]} to {volatility_periods[-1]}",
                    "evidence_ids": evidence_ids[-12:],
                    "explanation": (
                        "Population coefficient of variation over consecutive verified "
                        "monthly claims."
                    ),
                }
            )
            return metrics
    metrics.append(
        {
            "key": "faac_volatility",
            "status": "insufficient_evidence",
            "value": None,
            "unit": "percent_cv",
            "label": "FAAC volatility",
            "fiscal_period": periods[-1] if periods else None,
            "evidence_ids": evidence_ids[-12:],
            "explanation": (
                "At least three consecutive verified monthly claims with a positive "
                "mean are required."
            ),
        }
    )
    return metrics
