import csv
from datetime import date
from pathlib import Path

from gaiafaac_api.database.seeds import seed_states
from gaiafaac_api.pipeline.extraction.file_import import import_file
from gaiafaac_api.pipeline.importer import ImportRequest
from gaiafaac_api.services.review_queue import list_pending_reviews


def _write_csv(path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            ["state", "gross_total", "total_deductions", "net_allocation", "reported_unit"]
        )
        writer.writerow(["Lagos", "1000.00", "100.00", "900.00", "naira"])
        writer.writerow(["Kano", "2000.00", "200.00", "1800.00", "naira"])


def _import(session, path, *, label, is_demo=False):
    return import_file(
        session,
        ImportRequest(
            path=path,
            source_organization="OAGF",
            revenue_month=date(2024, 1, 1),
            reporting_label=label,
            reported_unit="naira",
            is_demo=is_demo,
        ),
    )


def test_lists_pending_real_period_metadata_only(session, tmp_path):
    seed_states(session)
    csv_path = tmp_path / "jan.csv"
    _write_csv(csv_path)
    _import(session, csv_path, label="OAGF Jan 2024")

    items = list_pending_reviews(session)
    assert len(items) == 1
    item = items[0]
    assert item.reporting_label == "OAGF Jan 2024"
    assert item.expected_states == 37
    assert item.covered_states == 2
    assert item.blocking_count >= 1  # MISSING_STATES

    # Metadata only — no allocation figures or financial fields leak through the schema.
    payload = item.model_dump()
    assert not hasattr(item, "allocations")
    assert "allocations" not in payload
    assert "gross_total" not in payload
    assert "total_deductions" not in payload
    assert "net_allocation" not in payload


def test_excludes_demo_and_published(session, tmp_path):
    seed_states(session)
    demo_csv = tmp_path / "demo.csv"
    _write_csv(demo_csv)
    _import(session, demo_csv, label="DEMO period", is_demo=True)
    assert list_pending_reviews(session) == []
