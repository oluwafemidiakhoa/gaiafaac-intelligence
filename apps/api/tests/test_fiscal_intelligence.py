from gaiafaac_api.ledger.intelligence import (
    classify_faac_monthly_change,
    derive_faac_metrics,
)


def _claim(period: str, value: str, *, unit: str = "naira") -> dict[str, str]:
    return {
        "gaia_id": f"GF-FAAC-NG-LA-{period.replace('-', '')}-{value}",
        "fiscal_period": period,
        "value": value,
        "unit": unit,
        "currency": "NGN",
        "status": "verified",
    }


def test_derived_metrics_require_consecutive_verified_claims():
    metrics = {
        item["key"]: item
        for item in derive_faac_metrics([_claim("2026-01", "100"), _claim("2026-03", "150")])
    }

    assert metrics["faac_published_period_total"]["value"] == "250.00"
    assert metrics["faac_month_over_month_change"]["status"] == "insufficient_evidence"
    assert metrics["faac_momentum"]["status"] == "insufficient_evidence"


def test_derived_metrics_calculate_decimal_momentum_and_volatility():
    metrics = {
        item["key"]: item
        for item in derive_faac_metrics(
            [_claim(f"2026-{month:02d}", str(month * 100)) for month in range(1, 7)]
        )
    }

    assert metrics["faac_month_over_month_change"]["value"] == "20.000000"
    assert metrics["faac_momentum"]["value"] == "150.000000"
    assert metrics["faac_volatility"]["status"] == "calculated"


def test_incompatible_units_are_not_combined():
    metrics = derive_faac_metrics(
        [_claim("2026-01", "100"), _claim("2026-02", "200", unit="thousand_naira")]
    )

    assert all(item["status"] == "insufficient_evidence" for item in metrics)


def test_event_classifier_is_thresholded_and_non_causal():
    event = classify_faac_monthly_change(
        previous_period="2026-01",
        previous_value="100",
        current_period="2026-02",
        current_value="75",
    )

    assert event is not None
    assert event["event_type"] == "faac_decline"
    assert event["change_percent"] == "-25.000000"
    assert "cause" not in event["explanation"].lower()
    assert (
        classify_faac_monthly_change(
            previous_period="2026-01",
            previous_value="100",
            current_period="2026-03",
            current_value="200",
        )
        is None
    )
