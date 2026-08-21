from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any


_RATIO_SPECS = (
    (
        "faac_dependence",
        "FAAC dependence",
        ("faac", ("faac_net_allocation",)),
        ("igr", ("igr", "igr_amount", "internally_generated_revenue")),
        "FAAC divided by FAAC plus IGR for the same fiscal period.",
    ),
    (
        "debt_burden",
        "Debt burden",
        ("debt", ("debt_stock", "total_debt_stock", "domestic_debt_stock")),
        ("budget", ("total_revenue", "approved_revenue", "budgeted_revenue")),
        "Debt stock divided by observed total revenue for the same fiscal period.",
    ),
    (
        "debt_service_pressure",
        "Debt-service pressure",
        ("debt_service", ("debt_service", "total_debt_service")),
        ("budget", ("total_revenue", "approved_revenue", "budgeted_revenue")),
        "Debt service divided by observed total revenue for the same fiscal period.",
    ),
    (
        "budget_execution",
        "Budget execution",
        ("expenditure", ("total_expenditure", "actual_expenditure")),
        ("budget", ("approved_expenditure", "total_budget", "approved_budget")),
        "Observed expenditure divided by the approved expenditure envelope for the same period.",
    ),
    (
        "capital_execution",
        "Capital execution",
        ("expenditure", ("capital_expenditure", "actual_capital_expenditure")),
        ("budget", ("capital_budget", "approved_capital_expenditure")),
        "Observed capital expenditure divided by approved capital expenditure for the same period.",
    ),
    (
        "liability_burden",
        "Liability burden",
        ("liabilities", ("total_liabilities", "liabilities")),
        ("budget", ("total_revenue", "approved_revenue", "budgeted_revenue")),
        "Observed liabilities divided by observed total revenue for the same fiscal period.",
    ),
)


def _claim(
    domains: dict[str, Any],
    domain_name: str,
    metrics: tuple[str, ...],
    fiscal_period: str,
) -> dict[str, Any] | None:
    domain = domains.get(domain_name)
    if not isinstance(domain, dict) or domain.get("status") != "verified":
        return None
    claims = domain.get("claims")
    if not isinstance(claims, list):
        return None
    matches = [
        item
        for item in claims
        if isinstance(item, dict)
        and item.get("status") == "verified"
        and item.get("fiscal_period") == fiscal_period
        and item.get("metric") in metrics
        and item.get("value") is not None
    ]
    return matches[-1] if len(matches) == 1 else None


def _decimal(value: object) -> Decimal | None:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None
    return result if result.is_finite() else None


def _compatible(left: dict[str, Any], right: dict[str, Any]) -> bool:
    left_currency = left.get("currency")
    right_currency = right.get("currency")
    if left_currency or right_currency:
        return bool(left_currency and right_currency and left_currency == right_currency)
    return left.get("unit") == right.get("unit")


def _insufficient(
    key: str, label: str, fiscal_period: str, explanation: str
) -> dict[str, object]:
    return {
        "key": key,
        "status": "insufficient_evidence",
        "value": None,
        "unit": "percent",
        "label": label,
        "fiscal_period": fiscal_period,
        "evidence_ids": [],
        "explanation": explanation,
    }


def derive_cross_domain_metrics(
    domains: dict[str, Any], *, fiscal_period: str
) -> list[dict[str, object]]:
    """Calculate transparent ratios from exact-period verified claims only."""

    metrics: list[dict[str, object]] = []
    for key, label, numerator_spec, denominator_spec, explanation in _RATIO_SPECS:
        numerator = _claim(domains, numerator_spec[0], numerator_spec[1], fiscal_period)
        denominator = _claim(domains, denominator_spec[0], denominator_spec[1], fiscal_period)
        if numerator is None or denominator is None:
            metrics.append(
                _insufficient(
                    key,
                    label,
                    fiscal_period,
                    f"{explanation} Required verified exact-period claims are unavailable.",
                )
            )
            continue
        numerator_value = _decimal(numerator.get("value"))
        denominator_value = _decimal(denominator.get("value"))
        if numerator_value is None or denominator_value is None or denominator_value <= 0:
            metrics.append(
                _insufficient(
                    key,
                    label,
                    fiscal_period,
                    f"{explanation} The retained denominator is missing, non-numeric, or non-positive.",
                )
            )
            continue
        if key == "faac_dependence":
            denominator_value += numerator_value
        if denominator_value <= 0 or not _compatible(numerator, denominator):
            metrics.append(
                _insufficient(
                    key,
                    label,
                    fiscal_period,
                    f"{explanation} Claim units or currencies are not directly comparable.",
                )
            )
            continue
        value = (numerator_value / denominator_value * Decimal("100")).quantize(
            Decimal("0.01")
        )
        metrics.append(
            {
                "key": key,
                "status": "calculated",
                "value": format(value, "f"),
                "unit": "percent",
                "label": label,
                "fiscal_period": fiscal_period,
                "evidence_ids": [str(numerator["gaia_id"]), str(denominator["gaia_id"])],
                "explanation": explanation,
            }
        )
    return metrics
