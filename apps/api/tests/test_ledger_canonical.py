from datetime import UTC, datetime
from decimal import Decimal

import pytest

from gaiafaac_api.ledger import (
    GaiaObjectType,
    canonical_json,
    canonical_sha256,
    fiscal_state_id,
    gaia_object_id,
)


def test_canonical_json_is_order_independent_and_preserves_decimal_scale() -> None:
    first = {
        "amount": Decimal("60348388366.7700"),
        "label": "Cafe\u0301",
        "effective_at": datetime(2026, 8, 14, 1, 30, tzinfo=UTC),
    }
    second = {
        "effective_at": datetime(2026, 8, 14, 1, 30, tzinfo=UTC),
        "label": "Café",
        "amount": Decimal("60348388366.7700"),
    }

    assert canonical_json(first) == canonical_json(second)
    assert '"amount":"60348388366.7700"' in canonical_json(first)
    assert canonical_sha256(first) == canonical_sha256(second)


def test_canonical_json_rejects_float_and_naive_datetime() -> None:
    with pytest.raises(TypeError, match="floating-point"):
        canonical_json({"amount": 0.1})
    with pytest.raises(ValueError, match="timezone-aware"):
        canonical_json({"effective_at": datetime(2026, 8, 14)})


def test_gaia_ids_are_stable_and_content_versioned() -> None:
    digest = "a" * 64

    assert (
        gaia_object_id(
            GaiaObjectType.FAAC,
            jurisdiction="ng-la",
            fiscal_period="2026-06",
            integrity_hash=digest,
        )
        == "GF-FAAC-NG-LA-202606-AAAAAA"
    )
    assert (
        fiscal_state_id(
            jurisdiction="NG-LA",
            effective_at=datetime(2026, 8, 14, tzinfo=UTC),
            integrity_hash=digest,
        )
        == "GFS-NG-LA-20260814-AAAAAA"
    )
