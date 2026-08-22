from gaiafaac_api.pipeline.nbs_igr.discovery import parse_nbs_igr_listing


def test_parse_nbs_igr_listing_discovers_official_state_level_reports():
    html = """
    <html><body>
      <a href="/elibrary/read/1241579">Internally Generated Revenue At State Level (2023)</a>
      <a href="https://www.nigerianstat.gov.ng/elibrary/read/1241400">
        Internally Generated Revenue At State Level (2022)
      </a>
      <a href="/elibrary/read/999">Consumer Price Index (2023)</a>
    </body></html>
    """

    results = parse_nbs_igr_listing(html)

    assert [item.fiscal_year for item in results] == [2023, 2022]
    assert results[0].report_id == "1241579"
    assert results[0].report_url == "https://www.nigerianstat.gov.ng/elibrary/read/1241579"


def test_parse_nbs_igr_listing_rejects_off_host_reports():
    html = """
    <html><body>
      <a href="https://evil.example/elibrary/read/1241579">
        Internally Generated Revenue At State Level (2023)
      </a>
    </body></html>
    """

    assert parse_nbs_igr_listing(html) == []


def test_parse_nbs_igr_listing_rejects_non_report_paths():
    html = """
    <html><body>
      <a href="/download/1241579">Internally Generated Revenue At State Level (2023)</a>
    </body></html>
    """

    assert parse_nbs_igr_listing(html) == []
