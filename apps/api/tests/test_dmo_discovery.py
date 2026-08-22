from gaiafaac_api.pipeline.dmo.discovery import parse_dmo_subnational_listing


def test_parse_dmo_subnational_listing_classifies_official_debt_publications():
    html = """
    <html><body>
      <a href="/files/domestic-march-2026.pdf">
        States and FCT Domestic Debt Stock as at March 31, 2026
      </a>
      <a href="https://www.dmo.gov.ng/files/external-december-2025.pdf">
        States, FCT and Federal Government's External Debt Stock as at December 31, 2025
      </a>
      <a href="/files/other.pdf">Federal Government Debt Stock</a>
    </body></html>
    """

    results = parse_dmo_subnational_listing(html)

    assert len(results) == 2
    assert results[0].debt_kind == "domestic"
    assert results[0].as_of_date.isoformat() == "2026-03-31"
    assert results[0].document_url == "https://www.dmo.gov.ng/files/domestic-march-2026.pdf"
    assert results[1].debt_kind == "external"
    assert results[1].as_of_date.isoformat() == "2025-12-31"


def test_parse_dmo_subnational_listing_rejects_non_dmo_download_links():
    html = """
    <a href="https://example.com/fake.pdf">
      States and FCT Domestic Debt Stock as at March 31, 2026
    </a>
    """

    assert parse_dmo_subnational_listing(html) == []
