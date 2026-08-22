from gaiafaac_api.pipeline.state_budget.discovery import get_budget_portal
from gaiafaac_api.pipeline.state_budget.performance_discovery import (
    parse_budget_performance_listing,
)


def test_oyo_listing_discovers_quarterly_budget_performance_reports_only():
    portal = get_budget_portal("OY")
    html = """
    <a href="/download/oyo-state-budget-performance-report-for-year-2026-first-quarter/">
      OYO STATE BUDGET PERFORMANCE REPORT FOR YEAR 2026 (FIRST QUARTER)
    </a>
    <a href="/download/oyo-state-budget-performance-report-for-year-2026-second-quarter/">
      OYO STATE BUDGET PERFORMANCE REPORT FOR YEAR 2026 (SECOND QUARTER)
    </a>
    <a href="/download/oyo-state-fy-2026-ncoa-approved-budget/">
      OYO STATE FY 2026 NCOA APPROVED BUDGET
    </a>
    """

    publications = parse_budget_performance_listing(portal, html)

    assert [(item.fiscal_year, item.quarter) for item in publications] == [(2026, 2), (2026, 1)]
    assert all(item.state_code == "OY" for item in publications)


def test_performance_listing_accepts_q_notation_and_quarter_words():
    portal = get_budget_portal("ZA")
    html = """
    <a href="/reports/zamfara-2026-q1-budget-performance-report.pdf">
      Zamfara 2026 Q1 Budget Performance Report
    </a>
    <a href="/reports/zamfara-2026-third-quarter-budget-performance-report.pdf">
      Zamfara 2026 Third Quarter Budget Performance Report
    </a>
    """

    publications = parse_budget_performance_listing(portal, html)

    assert {(item.fiscal_year, item.quarter) for item in publications} == {(2026, 1), (2026, 3)}


def test_performance_listing_requires_exactly_one_quarter():
    portal = get_budget_portal("OY")
    html = """
    <a href="/download/oyo-2026-budget-performance-report/">
      OYO STATE 2026 BUDGET PERFORMANCE REPORT
    </a>
    <a href="/download/oyo-2026-q1-q2-budget-performance-report/">
      OYO STATE 2026 Q1 Q2 BUDGET PERFORMANCE REPORT
    </a>
    """

    assert parse_budget_performance_listing(portal, html) == []


def test_performance_listing_rejects_off_host_links():
    portal = get_budget_portal("OY")
    html = """
    <a href="https://example.com/oyo-2026-q2-budget-performance-report.pdf">
      OYO STATE 2026 Q2 BUDGET PERFORMANCE REPORT
    </a>
    """

    assert parse_budget_performance_listing(portal, html) == []
