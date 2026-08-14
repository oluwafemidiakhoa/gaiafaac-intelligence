from datetime import date
from decimal import Decimal

from sqlalchemy import select

from gaiafaac_api.database.enums import ReportedUnit, VerificationStatus
from gaiafaac_api.database.igr_models import IgrPeriodType, StateIgrRecord
from gaiafaac_api.database.models import ReportingPeriod, SourceDocument, State, StateAllocation
from gaiafaac_api.database.seeds import seed_states
from gaiafaac_api.services.fiscal_design import fiscal_design, latest_comparable_design_year


def _seed_state_evidence(session, *, months: int = 12, year: int = 2026):
    seed_states(session)
    state = session.scalars(select(State).where(State.is_fct.is_(False))).first()
    faac_source = SourceDocument(
        source_organization="OAGF",
        original_filename=f"design-faac-{year}.pdf",
        storage_path=f"design-faac-{year}.pdf",
        sha256=f"{year}".ljust(64, "a")[:64],
        mime_type="application/pdf",
        is_demo=False,
    )
    igr_source = SourceDocument(
        source_organization="NBS",
        original_filename=f"design-igr-{year}.xlsx",
        storage_path=f"design-igr-{year}.xlsx",
        sha256=f"{year}".ljust(64, "b")[:64],
        mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        is_demo=False,
    )
    session.add_all([faac_source, igr_source])
    session.flush()

    for month in range(1, months + 1):
        period = ReportingPeriod(
            revenue_month=date(year, month, 1),
            reporting_label=f"{year}-{month:02d}",
            is_demo=False,
            is_published=True,
        )
        session.add(period)
        session.flush()
        session.add(
            StateAllocation(
                reporting_period_id=period.id,
                state_id=state.id,
                source_document_id=faac_source.id,
                gross_total=Decimal("120.00"),
                total_deductions=Decimal("20.00"),
                net_allocation=Decimal("100.00"),
                reported_unit=ReportedUnit.NAIRA,
                is_demo=False,
                is_published=True,
            )
        )

    session.add(
        StateIgrRecord(
            state_id=state.id,
            source_document_id=igr_source.id,
            fiscal_year=year,
            period_type=IgrPeriodType.ANNUAL,
            quarter=None,
            period_start=date(year, 1, 1),
            period_end=date(year, 12, 31),
            igr_amount=Decimal("600.00"),
            igr_amount_original="600.00",
            reported_unit=ReportedUnit.NAIRA,
            verification_status=VerificationStatus.HUMAN_VERIFIED,
            is_demo=False,
            is_published=True,
        )
    )
    session.flush()
    return state


def test_fiscal_design_computes_deterministic_complete_year_scenarios(session):
    state = _seed_state_evidence(session)

    result = fiscal_design(
        session,
        state_slug=state.slug,
        year=2026,
        faac_shock_pct=Decimal("-25"),
        igr_shock_pct=Decimal("-10"),
        reserve_share_pct=Decimal("20"),
    )

    assert result is not None
    assert result.faac_complete_year is True
    assert result.annual_igr_available is True
    assert result.latest_comparable_year == 2026
    assert len(result.evidence) == 13
    assert result.scenario_gaia_id.startswith("GF-SCENARIO-NG-LA-2026-")
    assert "debt" in result.unsupported_dimensions

    by_key = {candidate.key: candidate for candidate in result.candidates}
    faac = by_key["faac_shock"]
    assert faac.status == "available"
    assert [metric.value for metric in faac.metrics] == ["1200.00", "900.00", "300.00"]

    igr = by_key["igr_buffer"]
    assert igr.status == "available"
    assert [metric.value for metric in igr.metrics] == ["600.00", "540.00", "108.00"]

    blended = by_key["blended_revenue"]
    assert blended.status == "available"
    assert [metric.value for metric in blended.metrics] == ["1800.00", "1440.00", "-360.00"]


def test_fiscal_design_refuses_to_blend_partial_faac_with_annual_igr(session):
    state = _seed_state_evidence(session, months=2)

    result = fiscal_design(session, state_slug=state.slug, year=2026)

    assert result is not None
    assert result.faac_complete_year is False
    assert result.latest_comparable_year is None
    by_key = {candidate.key: candidate for candidate in result.candidates}
    assert by_key["faac_shock"].status == "available"
    assert "not annualized" in by_key["faac_shock"].note
    assert by_key["blended_revenue"].status == "insufficient_data"
    assert by_key["blended_revenue"].metrics == []


def test_latest_comparable_design_year_falls_back_to_latest_complete_intersection(session):
    state = _seed_state_evidence(session, year=2025)
    _seed_state_evidence(session, months=2, year=2026)

    assert latest_comparable_design_year(session, state_slug=state.slug) == 2025

    result = fiscal_design(session, state_slug=state.slug, year=2026)
    assert result is not None
    assert result.latest_comparable_year == 2025


def test_fiscal_design_returns_none_for_unknown_state(session):
    assert fiscal_design(session, state_slug="unknown", year=2026) is None


def test_expanded_assumptions_are_recorded_but_not_calculated_without_evidence(session):
    state = _seed_state_evidence(session)

    result = fiscal_design(
        session,
        state_slug=state.slug,
        year=2026,
        debt_change_pct=Decimal("10"),
        inflation_assumption_pct=Decimal("7.5"),
    )

    assert result is not None
    expanded = next(item for item in result.candidates if item.key == "expanded_fiscal_position")
    assert expanded.status == "insufficient_data"
    assert expanded.metrics == []
    assert "Debt change: 10.00%." in result.assumptions
    assert "inflation_adjustment" in result.unsupported_dimensions
