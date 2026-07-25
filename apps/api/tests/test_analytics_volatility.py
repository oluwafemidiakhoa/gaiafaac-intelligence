from decimal import Decimal

from sqlalchemy.orm import Session

from gaiafaac_api.pipeline.analytics.dataset import generate_analytics_dataset
from gaiafaac_api.pipeline.analytics.volatility import (
    coefficient_of_variation,
    compute_volatility,
)


def test_cv_pure_helper() -> None:
    assert coefficient_of_variation([]) is None
    assert coefficient_of_variation([Decimal("100"), Decimal("100")]) is None
    assert coefficient_of_variation([Decimal("0"), Decimal("0"), Decimal("0")]) is None
    cv = coefficient_of_variation([Decimal("100"), Decimal("200"), Decimal("300")])
    assert cv is not None
    assert cv.quantize(Decimal("0.0001")) == Decimal("0.4082")


def test_compute_volatility_covers_all_states(session: Session) -> None:
    generate_analytics_dataset(session)
    specs = compute_volatility(session)
    assert len(specs) == 37
    assert all(spec.indicator_name == "net_allocation_cv" for spec in specs)
    assert all(spec.value >= Decimal("0") for spec in specs)
