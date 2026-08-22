from gaiafaac_api.pipeline.state_budget.discovery import (
    get_budget_portal,
    parse_budget_listing,
    registered_budget_portals,
)


def test_registry_is_explicitly_partial_and_official():
    portals = registered_budget_portals()

    assert {portal.state_code for portal in portals} == {"OY", "ZA"}
    assert len(portals) < 37
    assert all(portal.listing_url.startswith("https://") for portal in portals)


def test_oyo_listing_keeps_approved_budget_and_rejects_adjacent_documents():
    portal = get_budget_portal("OY")
    html = """
    <a href="https://budget.oyostate.gov.ng/download/oyo-state-fy-2026-ncoa-approved-budget/">
      OYO STATE FY 2026 NCOA APPROVED BUDGET
    </a>
    <a href="/download/citizens-budget-2026/">CITIZENS' BUDGET 2026</a>
    <a href="/download/oyo-state-budget-performance-report-for-year-2026-second-quarter/">
      OYO STATE BUDGET PERFORMANCE REPORT FOR YEAR 2026 (SECOND QUARTER)
    </a>
    <a href="/download/oyo-state-fy-2026-appropriation-law/">
      OYO STATE FY 2026 APPROPRIATION LAW
    </a>
    """

    publications = parse_budget_listing(portal, html)

    assert len(publications) == 1
    assert publications[0].state_code == "OY"
    assert publications[0].fiscal_year == 2026
    assert publications[0].title == "OYO STATE FY 2026 NCOA APPROVED BUDGET"


def test_zamfara_listing_accepts_approved_budget_estimates():
    portal = get_budget_portal("ZA")
    html = """
    <a href="/wp-content/uploads/2026/02/ZAMFARA-STATE-2026-APPROVED-BUDGET-ESTIMATES.pdf">
      ZAMFARA STATE 2026 APPROVED BUDGET ESTIMATES
    </a>
    <a href="/wp-content/uploads/2026/02/206ZamfaraCB.pdf">
      2026 Zamfara State Citizens Budget
    </a>
    """

    publications = parse_budget_listing(portal, html)

    assert len(publications) == 1
    assert publications[0].state_code == "ZA"
    assert publications[0].fiscal_year == 2026


def test_budget_listing_rejects_off_host_document_links():
    portal = get_budget_portal("OY")
    html = """
    <a href="https://example.com/oyo-state-2026-approved-budget.pdf">
      OYO STATE 2026 APPROVED BUDGET
    </a>
    """

    assert parse_budget_listing(portal, html) == []


def test_unregistered_state_fails_closed():
    try:
        get_budget_portal("LA")
    except ValueError as error:
        assert "No verified state-budget portal" in str(error)
    else:
        raise AssertionError("Unregistered state portal must fail closed")
