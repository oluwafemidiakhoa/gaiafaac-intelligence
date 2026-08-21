from gaiafaac_api.ledger.cross_domain_intelligence import derive_cross_domain_metrics


def _claim(gaia_id, metric, value, *, period="2026", currency="NGN"):
    return {
        "gaia_id": gaia_id,
        "metric": metric,
        "fiscal_period": period,
        "value": value,
        "unit": "naira",
        "currency": currency,
        "status": "verified",
    }


def test_cross_domain_ratios_require_exact_verified_evidence():
    domains = {
        "faac": {
            "status": "verified",
            "claims": [_claim("faac", "faac_net_allocation", "75")],
        },
        "igr": {
            "status": "verified",
            "claims": [_claim("igr", "internally_generated_revenue", "25")],
        },
        "debt": {
            "status": "verified",
            "claims": [_claim("debt", "total_debt_stock", "200")],
        },
        "debt_service": {
            "status": "verified",
            "claims": [_claim("service", "debt_service", "10")],
        },
        "budget": {
            "status": "verified",
            "claims": [
                _claim("revenue", "total_revenue", "100"),
                _claim("budget", "approved_budget", "120"),
                _claim("capital-budget", "capital_budget", "40"),
            ],
        },
        "expenditure": {
            "status": "verified",
            "claims": [
                _claim("spend", "actual_expenditure", "90"),
                _claim("capital-spend", "actual_capital_expenditure", "20"),
            ],
        },
        "liabilities": {
            "status": "verified",
            "claims": [_claim("liability", "total_liabilities", "30")],
        },
    }
    results = {item["key"]: item for item in derive_cross_domain_metrics(domains, fiscal_period="2026")}
    assert results["faac_dependence"]["value"] == "75.00"
    assert results["debt_burden"]["value"] == "200.00"
    assert results["debt_service_pressure"]["value"] == "10.00"
    assert results["budget_execution"]["value"] == "75.00"
    assert results["capital_execution"]["value"] == "50.00"
    assert results["liability_burden"]["value"] == "30.00"
    assert results["debt_burden"]["evidence_ids"] == ["debt", "revenue"]


def test_cross_domain_ratio_fails_closed_on_period_mismatch():
    domains = {
        "debt": {
            "status": "verified",
            "claims": [_claim("debt", "total_debt_stock", "200", period="2026Q2")],
        },
        "budget": {
            "status": "verified",
            "claims": [_claim("revenue", "total_revenue", "100", period="2026")],
        },
    }
    results = {item["key"]: item for item in derive_cross_domain_metrics(domains, fiscal_period="2026Q2")}
    assert results["debt_burden"]["status"] == "insufficient_evidence"
    assert results["debt_burden"]["value"] is None


def test_cross_domain_ratio_fails_closed_on_currency_mismatch():
    domains = {
        "debt_service": {
            "status": "verified",
            "claims": [_claim("service", "debt_service", "10", currency="USD")],
        },
        "budget": {
            "status": "verified",
            "claims": [_claim("revenue", "total_revenue", "100", currency="NGN")],
        },
    }
    results = {item["key"]: item for item in derive_cross_domain_metrics(domains, fiscal_period="2026")}
    assert results["debt_service_pressure"]["status"] == "insufficient_evidence"
    assert "not directly comparable" in results["debt_service_pressure"]["explanation"]
