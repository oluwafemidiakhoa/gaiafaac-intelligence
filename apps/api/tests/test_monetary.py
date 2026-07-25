from decimal import Decimal

import pytest

from gaiafaac_api.database.enums import ReportedUnit
from gaiafaac_api.pipeline.errors import MonetaryParseError
from gaiafaac_api.pipeline.monetary import parse_money, parse_reported_unit


@pytest.mark.parametrize(
    ("original", "unit", "expected"),
    [
        ("₦1,234.50", ReportedUnit.NAIRA, Decimal("1234.50")),
        ("1 2 34.50", ReportedUnit.NAIRA, Decimal("1234.50")),
        ("(1,200)", ReportedUnit.NAIRA, Decimal("-1200.00")),
        ("1.25", ReportedUnit.MILLION_NAIRA, Decimal("1250000.00")),
        ("nil", ReportedUnit.BILLION_NAIRA, Decimal("0.00")),
        ("—", ReportedUnit.NAIRA, None),
        ("", ReportedUnit.UNSPECIFIED, None),
    ],
)
def test_parse_money_preserves_exact_values(
    original: str, unit: ReportedUnit, expected: Decimal | None
) -> None:
    parsed = parse_money(original, unit)

    assert parsed.original_text == original
    assert parsed.value == expected
    assert parsed.reported_unit is unit


@pytest.mark.parametrize(
    "value",
    [
        "12 bananas",
        "(100",
        "1.2.3",
        "12,34",
        "1NGN2",
        "1.234",
        "99999999999999999999999",
    ],
)
def test_parse_money_rejects_invalid_values(value: str) -> None:
    with pytest.raises(MonetaryParseError):
        parse_money(value, ReportedUnit.NAIRA)


def test_parse_money_never_infers_a_unit() -> None:
    with pytest.raises(MonetaryParseError, match="unit is required"):
        parse_money("₦100", ReportedUnit.UNSPECIFIED)


def test_parse_reported_unit_uses_explicit_aliases_only() -> None:
    assert parse_reported_unit("NGN") is ReportedUnit.NAIRA
    assert parse_reported_unit("million naira") is ReportedUnit.MILLION_NAIRA
    with pytest.raises(MonetaryParseError):
        parse_reported_unit("crore")
