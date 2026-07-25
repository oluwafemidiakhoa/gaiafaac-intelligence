import csv
from pathlib import Path

from gaiafaac_api.pipeline.extraction.csv_adapter import GenericCsvAdapter


def _write(path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "state",
                "gross_total",
                "total_deductions",
                "net_allocation",
                "reported_unit",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "state": "Lagos",
                "gross_total": "1,000.00",
                "total_deductions": "100.00",
                "net_allocation": "900.00",
                "reported_unit": "naira",
            }
        )


def test_csv_adapter_supports_csv() -> None:
    adapter = GenericCsvAdapter()
    assert adapter.supports(Path("x.csv"), "application/octet-stream") is True
    assert adapter.supports(Path("x.xlsx"), "text/csv") is True
    assert adapter.supports(Path("x.pdf"), "application/pdf") is False


def test_csv_adapter_extracts_original_text_and_rows(tmp_path: Path) -> None:
    path = tmp_path / "alloc.csv"
    _write(path)
    table = GenericCsvAdapter().extract(path)

    assert table.adapter_name == "generic_csv"
    assert len(table.rows) == 1
    row = table.rows[0]
    assert row.submitted_state == "Lagos"
    assert row.reported_unit == "naira"
    assert row.source_row == 2
    assert row.original_text("gross_total") == "1,000.00"
    assert row.cells["gross_total"].column == "gross_total"
