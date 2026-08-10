from decimal import Decimal

from gaiafaac_api.pipeline.extraction.fct_extractor import (
    parse_fct_line,
    reconcile_fct_total,
)

# Human-verified from independent source-PDF audits. Test fixtures only.
APRIL_2024_FCT_CORRECT = Decimal("10084608167.23")
APRIL_2024_EMTL_TRAP = Decimal("147547159.58")


def test_parse_fct_line_extracts_all_row_numbers():
    line = (
        "5FCT-Abuja 3,297,820,008.22 (97,124,889.00) 3,200,695,119.22 "
        "2,632,340,746.29 178,551,513.81 4,586,213,607.09 10,597,800,986.41"
    )
    nums = parse_fct_line(line)
    assert len(nums) == 7
    assert nums[-1] == Decimal("10597800986.41")


def test_reconciles_verified_seven_value_layout():
    nums = [
        Decimal("3297820008.22"),
        Decimal("-97124889.00"),
        Decimal("3200695119.22"),
        Decimal("2632340746.29"),
        Decimal("178551513.81"),
        Decimal("4586213607.09"),
        Decimal("10597800986.41"),
    ]
    result = reconcile_fct_total(nums)
    assert result.status == "verified"
    assert result.confidence == 1.0
    assert result.value == Decimal("10597800986.41")
    assert "7-value" in result.note


def test_reconciles_january_2026_six_value_layout():
    nums = [
        Decimal("9886229766.22"),
        Decimal("-359874453.00"),
        Decimal("9526355313.22"),
        Decimal("381101343.33"),
        Decimal("8465070370.22"),
        Decimal("18372527026.77"),
    ]
    result = reconcile_fct_total(nums)
    assert result.status == "verified"
    assert result.value == Decimal("18372527026.77")
    assert "6-value" in result.note


def test_reconciles_march_2025_eight_value_layout():
    nums = [
        Decimal("6952597875.25"),
        Decimal("-371934302.00"),
        Decimal("6580663573.25"),
        Decimal("1780000000.00"),
        Decimal("412446249.08"),
        Decimal("351708776.28"),
        Decimal("6094292850.85"),
        Decimal("15219111449.46"),
    ]
    result = reconcile_fct_total(nums)
    assert result.status == "verified"
    assert result.value == Decimal("15219111449.46")
    assert "8-value" in result.note


def test_reconciles_july_2025_eight_value_layout():
    nums = [
        Decimal("9006362369.33"),
        Decimal("-371934302.00"),
        Decimal("8634428067.33"),
        Decimal("363462120.32"),
        Decimal("291643956.00"),
        Decimal("1000000000.00"),
        Decimal("6315074188.38"),
        Decimal("16604608332.03"),
    ]
    result = reconcile_fct_total(nums)
    assert result.status == "verified"
    assert result.value == Decimal("16604608332.03")


def test_refuses_truncated_row_and_never_returns_component():
    nums = [
        Decimal("2542899541.34"),
        Decimal("-248063295.00"),
        Decimal("2294836246.34"),
        Decimal("2523435091.05"),
        Decimal("147547159.58"),
    ]
    result = reconcile_fct_total(nums)
    assert result.value is None
    assert result.status == "review_required"
    assert "unsupported FCT row layout" in result.note
    assert result.value != APRIL_2024_EMTL_TRAP


def test_refuses_unknown_future_layout_even_if_last_value_is_large():
    nums = [Decimal("1000000000")] * 9
    result = reconcile_fct_total(nums)
    assert result.value is None
    assert result.status == "review_required"
    assert "9 values" in result.note


def test_refuses_supported_layout_when_components_do_not_reconcile():
    nums = [
        Decimal("1"),
        Decimal("0"),
        Decimal("1000000000"),
        Decimal("1000000000"),
        Decimal("1000000000"),
        Decimal("1000000000"),
        Decimal("5239729292.37"),
    ]
    result = reconcile_fct_total(nums)
    assert result.value is None
    assert result.status == "review_required"
    assert "does not reconcile" in result.note


def test_april_regression_correct_value_never_equals_the_trap():
    assert Decimal("10084608167.23") == APRIL_2024_FCT_CORRECT
    assert APRIL_2024_FCT_CORRECT != APRIL_2024_EMTL_TRAP
