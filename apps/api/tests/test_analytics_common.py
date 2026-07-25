from decimal import Decimal

from gaiafaac_api.pipeline.analytics.common import (
    decimal_mean,
    decimal_pstdev,
    deterministic_unit,
    seasonal_factor,
    state_base,
)


def test_deterministic_unit_is_stable_and_bounded() -> None:
    a = deterministic_unit("LA", 2097, 3)
    b = deterministic_unit("LA", 2097, 3)
    assert a == b
    assert Decimal("0") <= a < Decimal("1")
    assert deterministic_unit("LA", 2097, 3, salt="ded") != a


def test_state_base_is_stable_and_in_range() -> None:
    base = state_base("KN")
    assert base == state_base("KN")
    assert Decimal("1000000000") <= base < Decimal("6000000000")


def test_seasonal_factor_centres_near_one() -> None:
    assert seasonal_factor(6) == Decimal("1.00")
    assert seasonal_factor(1) < seasonal_factor(12)


def test_decimal_stats() -> None:
    values = [Decimal("100"), Decimal("200"), Decimal("300")]
    assert decimal_mean(values) == Decimal("200")
    assert decimal_pstdev(values).quantize(Decimal("0.0001")) == Decimal("81.6497")
