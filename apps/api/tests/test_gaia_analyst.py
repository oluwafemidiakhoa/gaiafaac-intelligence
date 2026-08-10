from gaiafaac_api.fiscal_pulse_schemas import FiscalPulseResponse, FiscalPulseState
from gaiafaac_api.fiscal_watch_schemas import FiscalWatchEvent, FiscalWatchResponse
from gaiafaac_api.services import gaia_analyst as service


def _state(
    name: str,
    slug: str,
    code: str,
    *,
    annual_net: str,
    burden: float,
    momentum: str,
    momentum_pct: float,
    volatility: str,
    volatility_cv: float,
) -> FiscalPulseState:
    return FiscalPulseState(
        state_name=name,
        state_slug=slug,
        state_code=code,
        geopolitical_zone="South South",
        months_published=6,
        months_with_net=6,
        months_with_complete_financials=6,
        annual_gross="1000.00",
        annual_deductions="100.00",
        annual_net=annual_net,
        deduction_burden_pct=burden,
        net_retention_pct=90.0,
        momentum=momentum,
        momentum_pct=momentum_pct,
        volatility=volatility,
        volatility_cv_pct=volatility_cv,
        evidence_status="Verified",
    )


def _pulse() -> FiscalPulseResponse:
    return FiscalPulseResponse(
        year=2026,
        months_published=6,
        expected_months=12,
        coverage_status="partial_year",
        coverage_label="Partial 2026 series · 6 of 12 months published",
        latest_period_label="June 2026",
        total_net="3000.00",
        states=[
            _state(
                "Rivers",
                "rivers",
                "RI",
                annual_net="2000.00",
                burden=10.0,
                momentum="Improving",
                momentum_pct=12.0,
                volatility="High",
                volatility_cv=30.0,
            ),
            _state(
                "Lagos",
                "lagos",
                "LA",
                annual_net="1000.00",
                burden=20.0,
                momentum="Weakening",
                momentum_pct=-8.0,
                volatility="Moderate",
                volatility_cv=18.0,
            ),
        ],
        note="Derived only from published records.",
    )


def _watch() -> FiscalWatchResponse:
    return FiscalWatchResponse(
        year=2026,
        latest_revenue_month="2026-06-01",
        previous_revenue_month="2026-05-01",
        event_count=1,
        events=[
            FiscalWatchEvent(
                kind="large_monthly_move",
                severity="watch",
                state_name="Rivers",
                state_slug="rivers",
                state_code="RI",
                revenue_month="2026-06-01",
                headline="Rivers net FAAC allocation increased sharply month over month",
                detail="Net allocation moved +27.68% from the prior published month.",
                current_net="2000.00",
                previous_net="1500.00",
                change_pct=27.68,
                deduction_burden_pct=None,
                proof_path="/fiscal-proof/rivers/2026-06-01",
            )
        ],
        note="Deterministic monitoring only.",
    )


def _patch(monkeypatch):
    monkeypatch.setattr(service, "fiscal_pulse", lambda session, year: _pulse())
    monkeypatch.setattr(service, "fiscal_watch", lambda session, year: _watch())


def test_gaia_analyst_answers_latest_changes(monkeypatch):
    _patch(monkeypatch)
    result = service.gaia_analyst(None, question="What changed in the latest data?", year=2026)
    assert result.intent == "latest_changes"
    assert result.status == "answered"
    assert result.evidence[0].reference_path == "/fiscal-proof/rivers/2026-06-01"


def test_gaia_analyst_answers_rankings(monkeypatch):
    _patch(monkeypatch)
    result = service.gaia_analyst(
        None,
        question="Which states received the highest net allocation?",
        year=2026,
    )
    assert result.intent == "top_net"
    assert result.evidence[0].state_name == "Rivers"


def test_gaia_analyst_compares_two_states(monkeypatch):
    _patch(monkeypatch)
    result = service.gaia_analyst(None, question="Compare Rivers and Lagos", year=2026)
    assert result.intent == "compare"
    assert result.status == "answered"
    assert "Rivers" in result.answer
    assert "Lagos" in result.answer


def test_gaia_analyst_refuses_unsupported_claim(monkeypatch):
    _patch(monkeypatch)
    result = service.gaia_analyst(
        None,
        question="Which governor is managing public money best?",
        year=2026,
    )
    assert result.intent == "unsupported"
    assert result.status == "unsupported"
    assert result.evidence == []
