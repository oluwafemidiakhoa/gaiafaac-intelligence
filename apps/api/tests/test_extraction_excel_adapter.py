from pathlib import Path

from openpyxl import Workbook

from gaiafaac_api.pipeline.extraction.excel_adapter import GenericExcelAdapter

_HEADERS = ["state", "gross_total", "total_deductions", "net_allocation", "reported_unit"]


def _write(path: Path, money_row: list[object]) -> None:
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.append(_HEADERS)
    worksheet.append(money_row)
    workbook.save(path)


def test_excel_adapter_supports_xlsx() -> None:
    adapter = GenericExcelAdapter()
    assert adapter.supports(Path("x.xlsx"), "application/octet-stream") is True
    assert adapter.supports(Path("x.csv"), "application/pdf") is False


def test_excel_text_money_preserved_without_review(tmp_path: Path) -> None:
    path = tmp_path / "text.xlsx"
    _write(path, ["Lagos", "1,000.00", "100.00", "900.00", "naira"])
    table = GenericExcelAdapter().extract(path)

    assert table.adapter_name == "generic_excel"
    assert table.requires_review is False
    assert len(table.rows) == 1
    row = table.rows[0]
    assert row.submitted_state == "Lagos"
    assert row.reported_unit == "naira"
    assert row.source_row == 2
    assert row.original_text("gross_total") == "1,000.00"


def test_excel_numeric_money_flags_review(tmp_path: Path) -> None:
    path = tmp_path / "numeric.xlsx"
    _write(path, ["Kano", 2000.5, 200.0, 1800.5, "naira"])
    table = GenericExcelAdapter().extract(path)

    assert table.requires_review is True
    assert table.warnings
