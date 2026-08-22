from gaiafaac_api.pipeline.state_financials.discovery import (
    StateFinancialEvidenceKind,
    get_state_financial_portals,
    parse_state_financial_listing,
    registered_state_financial_portals,
)


def test_registry_is_explicitly_partial_and_official():
    portals = registered_state_financial_portals()

    assert {portal.state_code for portal in portals} == {"OY", "ZA"}
    assert all(portal.listing_url.startswith("https://") for portal in portals)
    assert {
        kind for portal in portals for kind in portal.evidence_kinds
    } == {
        StateFinancialEvidenceKind.AUDITED_FINANCIAL_STATEMENT,
        StateFinancialEvidenceKind.CONTRACTOR_ARREARS_REGISTER,
    }


def test_oyo_accountant_general_discovers_audited_state_statements_only():
    portal = next(
        portal
        for portal in get_state_financial_portals("OY")
        if StateFinancialEvidenceKind.AUDITED_FINANCIAL_STATEMENT in portal.evidence_kinds
    )
    html = """
    <a href="/download/updated-oyo-state-audited-financial-reports-for-year-2025/">
      UPDATED OYO STATE AUDITED FINANCIAL REPORTS FOR YEAR 2025
    </a>
    <a href="/download/oyo-state-audited-financial-reports-for-year-2024/">
      OYO STATE AUDITED FINANCIAL REPORTS FOR YEAR 2024
    </a>
    <a href="/download/citizens-accountability-reports-year-2024/">
      CITIZENS’ ACCOUNTABILITY REPORTS YEAR 2024
    </a>
    <a href="/download/oyo-state-33-local-governments-financial-statement-fy2020/">
      OYO STATE 33 LOCAL GOVERNMENTS AUDITED FINANCIAL STATEMENTS FY2020
    </a>
    """

    publications = parse_state_financial_listing(portal, html)

    assert [(item.fiscal_year, item.evidence_kind) for item in publications] == [
        (2025, StateFinancialEvidenceKind.AUDITED_FINANCIAL_STATEMENT),
        (2024, StateFinancialEvidenceKind.AUDITED_FINANCIAL_STATEMENT),
    ]


def test_oyo_finance_discovers_explicit_contractor_arrears_register():
    portal = next(
        portal
        for portal in get_state_financial_portals("OY")
        if StateFinancialEvidenceKind.CONTRACTOR_ARREARS_REGISTER in portal.evidence_kinds
    )
    html = """
    <a href="/download/oyo-state-contractor-arrears-database-and-other-domestic-debt-2021/">
      OYO STATE CONTRACTOR ARREARS DATABASE AND OTHER DOMESTIC DEBT 2021
    </a>
    <a href="/download/oyo-state-2025-debt-sustainability-analysis/">
      OYO STATE 2025 DEBT SUSTAINABILITY ANALYSIS AND DEBT MANAGEMENT STRATEGY
    </a>
    """

    publications = parse_state_financial_listing(portal, html)

    assert len(publications) == 1
    assert publications[0].fiscal_year == 2021
    assert publications[0].evidence_kind is StateFinancialEvidenceKind.CONTRACTOR_ARREARS_REGISTER


def test_zamfara_discovers_audited_financial_statement_and_ignores_budget_files():
    portal = get_state_financial_portals("ZA")[0]
    html = """
    <a href="/wp-content/uploads/2026/07/Zamfara-State-Audited-2025-Financial-Statement.pdf">
      Zamfara State Audited 2025 Financial Statement
    </a>
    <a href="/wp-content/uploads/2026/04/Zamfara-State-2026-First-Quarter-BPR.pdf">
      Zamfara State 2026 First Quarter Budget Performance Report.pdf
    </a>
    """

    publications = parse_state_financial_listing(portal, html)

    assert len(publications) == 1
    assert publications[0].fiscal_year == 2025
    assert publications[0].evidence_kind is StateFinancialEvidenceKind.AUDITED_FINANCIAL_STATEMENT


def test_state_financial_listing_rejects_off_host_document_links():
    portal = get_state_financial_portals("ZA")[0]
    html = """
    <a href="https://example.com/Zamfara-State-Audited-2025-Financial-Statement.pdf">
      Zamfara State Audited 2025 Financial Statement
    </a>
    """

    assert parse_state_financial_listing(portal, html) == []


def test_unregistered_state_fails_closed():
    try:
        get_state_financial_portals("LA")
    except ValueError as error:
        assert "No verified state-financial portal" in str(error)
    else:
        raise AssertionError("Unregistered state-financial portal must fail closed")
