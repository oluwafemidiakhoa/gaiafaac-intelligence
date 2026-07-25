from decimal import Decimal

from sqlalchemy.orm import Session

from gaiafaac_api.pipeline.analytics.dataset import generate_analytics_dataset
from gaiafaac_api.pipeline.analytics.dependency import component_shares, compute_dependency


def test_component_shares_and_hhi() -> None:
    assert component_shares([]) is None
    result = component_shares([("statutory_allocation", Decimal("75")), ("vat", Decimal("25"))])
    assert result is not None
    shares, hhi = result
    assert shares["statutory_allocation"] == Decimal("0.750000")
    assert shares["vat"] == Decimal("0.250000")
    assert hhi == Decimal("0.625000")


def test_compute_dependency_emits_shares_and_hhi(session: Session) -> None:
    generate_analytics_dataset(session)
    specs = compute_dependency(session)
    names = {spec.indicator_name for spec in specs}
    assert "net_concentration_hhi" in names
    assert "statutory_allocation_net_share" in names
    hhi_specs = [spec for spec in specs if spec.indicator_name == "net_concentration_hhi"]
    assert len(hhi_specs) == 37
    assert all(Decimal("0") < spec.value <= Decimal("1") for spec in hhi_specs)
