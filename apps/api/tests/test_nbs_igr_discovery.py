from gaiafaac_api.pipeline.nbs_igr.discovery import parse_nbs_igr_listing


def _row(href: str, title: str) -> str:
    link = (
        f'<a class="btn btn-success btn-sm summ" href="{href}"><i class="glyphicon-book"></i></a>'
    )
    return f"""
    <tr>
      <td>{title}</td>
      <td style="display:none">Economic Statistics</td>
      <td>Mon Oct 28 2024</td>
      <td>{link}</td>
    </tr>
    """


def test_parse_nbs_igr_listing_discovers_official_state_level_reports():
    html = f"""
    <html><body><table>
      {_row("/elibrary/read/1241579", "Internally Generated Revenue At State Level (2023)")}
      {
        _row(
            "https://www.nigerianstat.gov.ng/elibrary/read/1241400",
            "Internally Generated Revenue At State Level (2022)",
        )
    }
      {_row("/elibrary/read/999", "Consumer Price Index (2023)")}
    </table></body></html>
    """

    results = parse_nbs_igr_listing(html)

    assert [item.fiscal_year for item in results] == [2023, 2022]
    assert results[0].report_id == "1241579"
    assert results[0].report_url == "https://www.nigerianstat.gov.ng/elibrary/read/1241579"


def test_parse_nbs_igr_listing_rejects_off_host_reports():
    html = f"""
    <html><body><table>
      {
        _row(
            "https://evil.example/elibrary/read/1241579",
            "Internally Generated Revenue At State Level (2023)",
        )
    }
    </table></body></html>
    """

    assert parse_nbs_igr_listing(html) == []


def test_parse_nbs_igr_listing_rejects_non_report_paths():
    html = f"""
    <html><body><table>
      {_row("/download/1241579", "Internally Generated Revenue At State Level (2023)")}
    </table></body></html>
    """

    assert parse_nbs_igr_listing(html) == []


def test_parse_nbs_igr_listing_matches_title_and_link_in_the_same_row_only():
    """The real NBS eLibrary lists many unrelated reports between IGR entries. A report's
    title and its download link must be paired by row, not by document order."""
    html = f"""
    <html><body><table>
      {_row("/elibrary/read/1", "Cost of Healthy Diet September 2024")}
      {_row("/elibrary/read/1241579", "Internally Generated Revenue At State Level (2023)")}
      {_row("/elibrary/read/2", "Consumer Price Index (2024)")}
    </table></body></html>
    """

    results = parse_nbs_igr_listing(html)

    assert len(results) == 1
    assert results[0].report_id == "1241579"
