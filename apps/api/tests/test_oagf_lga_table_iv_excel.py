from pathlib import Path

from openpyxl import Workbook

from gaiafaac_api.pipeline.extraction.oagf_lga_table_iv_excel import (
    extract_oagf_table_iv_excel,
)


def _write_workbook(path: Path, row_count: int) -> None:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Table IV"
    worksheet.append(
        [
            "State",
            "Local Government Councils",
            "Net Statutory Allocation",
            "Deduction",
            "Value Added Tax",
            "Total Net Allocation",
        ]
    )
    for index in range(1, row_count + 1):
        worksheet.append(
            [
                "Test State",
                f"Local Government {index}",
                "1000000.00",
                "10000.00",
                "250000.00",
                f"{1240000 + index}.00",
            ]
        )
    workbook.save(path)
    workbook.close()


def test_excel_table_iv_accepts_complete_774_jurisdiction_batch(tmp_path: Path) -> None:
    source = tmp_path / "official-table-iv.xlsx"
    _write_workbook(source, 774)

    result = extract_oagf_table_iv_excel(source)

    assert len(result.rows) == 774
    assert result.requires_review is False
    assert result.warnings == []
    assert result.rows[0].local_government_name == "Local Government 1"
    assert result.rows[0].page is None
    assert result.rows[-1].total_net_allocation == 1240774


def test_excel_table_iv_fails_closed_on_incomplete_coverage(tmp_path: Path) -> None:
    source = tmp_path / "incomplete-table-iv.xlsx"
    _write_workbook(source, 10)

    result = extract_oagf_table_iv_excel(source)

    assert len(result.rows) == 10
    assert result.requires_review is True
    assert any("expected 774 jurisdictions, extracted 10" in warning for warning in result.warnings)
