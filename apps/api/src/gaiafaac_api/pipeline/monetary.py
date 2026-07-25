from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from gaiafaac_api.database.enums import ReportedUnit
from gaiafaac_api.pipeline.errors import MonetaryParseError

_MISSING_VALUES = {"", "-", "–", "—", "n/a", "na", "null"}
_ZERO_VALUES = {"nil", "none"}
_UNIT_MULTIPLIERS = {
    ReportedUnit.NAIRA: Decimal("1"),
    ReportedUnit.THOUSAND_NAIRA: Decimal("1000"),
    ReportedUnit.MILLION_NAIRA: Decimal("1000000"),
    ReportedUnit.BILLION_NAIRA: Decimal("1000000000"),
}
_NUMBER_PATTERN = re.compile(r"^[+-]?(?:\d+(?:\.\d+)?|\.\d+)$")
_GROUPED_NUMBER_PATTERN = re.compile(r"^[+-]?\d{1,3}(?:,\d{3})+(?:\.\d+)?$")


@dataclass(frozen=True)
class ParsedMoney:
    original_text: str
    value: Decimal | None
    reported_unit: ReportedUnit


def parse_reported_unit(value: str) -> ReportedUnit:
    normalized = re.sub(r"[\s-]+", "_", value.strip().casefold())
    aliases = {
        "ngn": ReportedUnit.NAIRA,
        "n": ReportedUnit.NAIRA,
        "naira": ReportedUnit.NAIRA,
        "thousand": ReportedUnit.THOUSAND_NAIRA,
        "thousands": ReportedUnit.THOUSAND_NAIRA,
        "thousand_naira": ReportedUnit.THOUSAND_NAIRA,
        "million": ReportedUnit.MILLION_NAIRA,
        "millions": ReportedUnit.MILLION_NAIRA,
        "million_naira": ReportedUnit.MILLION_NAIRA,
        "billion": ReportedUnit.BILLION_NAIRA,
        "billions": ReportedUnit.BILLION_NAIRA,
        "billion_naira": ReportedUnit.BILLION_NAIRA,
        "unspecified": ReportedUnit.UNSPECIFIED,
    }
    try:
        return aliases[normalized]
    except KeyError as error:
        raise MonetaryParseError(f"Unsupported reported monetary unit: {value!r}") from error


def parse_money(original: str | None, reported_unit: ReportedUnit) -> ParsedMoney:
    """Parse an explicitly-unitized monetary string into exact naira."""
    text = "" if original is None else str(original)
    stripped = text.strip()
    lowered = stripped.casefold()
    if lowered in _MISSING_VALUES:
        return ParsedMoney(text, None, reported_unit)
    if reported_unit is ReportedUnit.UNSPECIFIED:
        raise MonetaryParseError("A monetary unit is required for every non-blank value")
    if lowered in _ZERO_VALUES:
        return ParsedMoney(text, Decimal("0.00"), reported_unit)

    negative = stripped.startswith("(") and stripped.endswith(")")
    if negative:
        stripped = stripped[1:-1].strip()
    elif stripped.startswith("(") or stripped.endswith(")"):
        raise MonetaryParseError(f"Unbalanced accounting parentheses: {text!r}")

    if stripped.startswith("₦"):
        stripped = stripped[1:].strip()
    elif stripped[:3].casefold() == "ngn":
        stripped = stripped[3:].strip()
    if stripped[-3:].casefold() == "ngn":
        stripped = stripped[:-3].strip()
    normalized = stripped.replace(" ", "")
    if "," in normalized:
        if not _GROUPED_NUMBER_PATTERN.fullmatch(normalized):
            raise MonetaryParseError(f"Invalid comma grouping in monetary value: {text!r}")
        normalized = normalized.replace(",", "")
    if not normalized or not _NUMBER_PATTERN.fullmatch(normalized):
        raise MonetaryParseError(f"Invalid monetary value: {text!r}")
    try:
        value = Decimal(normalized)
    except InvalidOperation as error:
        raise MonetaryParseError(f"Invalid monetary value: {text!r}") from error
    if negative:
        value = -value
    value *= _UNIT_MULTIPLIERS[reported_unit]
    if not value.is_finite() or (value and value.copy_abs().adjusted() > 21):
        raise MonetaryParseError(f"Monetary value exceeds NUMERIC(24, 2): {text!r}")
    try:
        quantized = value.quantize(Decimal("0.01"))
    except InvalidOperation as error:
        raise MonetaryParseError(f"Invalid monetary precision: {text!r}") from error
    if quantized != value:
        raise MonetaryParseError(f"Monetary value has precision smaller than one kobo: {text!r}")
    return ParsedMoney(text, quantized, reported_unit)
