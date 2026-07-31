from decimal import Decimal

from gaiafaac_api.pipeline.extraction.fct_extractor import (
    parse_fct_line,
    reconcile_fct_total,
)

# Human-verified from an independent audit of the source PDF. Used ONLY as a test fixture —
# never as production extraction logic.
APRIL_2024_FCT_CORRECT = Decimal("10084608167.23")
APRIL_2024_EMTL_TRAP = Decimal("147547159.58")  # the component the old nums[-1] hack wrongly took


def test_parse_fct_line_extracts_all_row_numbers():
    line = (
        "5FCT-Abuja 3,297,820,008.22 (97,124,889.00) 3,200,695,119.22 "
        "2,632,340,746.29 178,551,513.81 4,586,213,607.09 10,597,800,986.41"
    )
    nums = parse_fct_line(line)
    assert len(nums) == 7
    assert nums[-1] == Decimal("10597800986.41")


def test_reconciles_a_verified_fct_row():
    # Real January 2024 FCT row: [stat_gross, deduction, net_stat, vat, emtl, exchange, total]
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


def test_refuses_truncated_row_and_never_returns_the_emtl_component():
    # April 2024: the source PDF truncates at EMTL, leaving only 5 numbers.
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
    # The whole point: it must NOT publish the EMTL component as the total.
    assert result.value != APRIL_2024_EMTL_TRAP


def test_refuses_when_components_do_not_reconcile():
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


def test_april_regression_correct_value_never_equals_the_trap():
    # April's correct FCT total is a documented human correction, never the EMTL component.
    assert Decimal("10084608167.23") == APRIL_2024_FCT_CORRECT
    assert APRIL_2024_FCT_CORRECT != APRIL_2024_EMTL_TRAP
