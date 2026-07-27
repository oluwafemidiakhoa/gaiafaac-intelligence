import csv
from datetime import date
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from gaiafaac_api.database.enums import VerificationStatus
from gaiafaac_api.database.models import StateAllocation, ValidationResult
from gaiafaac_api.database.seeds import NIGERIAN_STATES, seed_states
from gaiafaac_api.pipeline.extraction.file_import import import_file
from gaiafaac_api.pipeline.extraction.oagf_pdf_adapter import _resolve_columns
from gaiafaac_api.pipeline.importer import ImportRequest


def _write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def test_import_file_derives_deductions_and_marks_real(session: Session, tmp_path: Path) -> None:
    seed_states(session)
    path = tmp_path / "real.csv"
    _write_csv(
        path,
        [
            {"state": name, "gross_total": "1000.00", "net_allocation": "900.00"}
            for name, *_ in NIGERIAN_STATES
        ],
        ["state", "gross_total", "net_allocation"],
    )

    result = import_file(
        session,
        ImportRequest(
            path=path,
            source_organization="OAGF",
            revenue_month=date(2026, 1, 1),
            faac_meeting_date=date(2026, 2, 1),
            publication_date=date(2026, 2, 1),
            reporting_label="Real January 2026",
            reported_unit="naira",
            is_demo=False,
        ),
    )

    assert result.records_extracted == 37
    assert result.blocking_finding_count == 0
    allocations = list(session.scalars(select(StateAllocation)))
    assert len(allocations) == 37
    assert all(a.is_demo is False and a.is_published is False for a in allocations)
    # deductions are derived as gross - net when the source has no deductions column
    assert all(a.total_deductions == a.gross_total - a.net_allocation for a in allocations)
    assert all(
        a.verification_status is VerificationStatus.AUTOMATICALLY_VALIDATED for a in allocations
    )
    published = session.scalar(
        select(func.count())
        .select_from(StateAllocation)
        .where(StateAllocation.is_published.is_(True))
    )
    assert published == 0


def test_import_file_flags_unknown_state(session: Session, tmp_path: Path) -> None:
    seed_states(session)
    path = tmp_path / "bad.csv"
    _write_csv(
        path,
        [
            {
                "state": "Atlantis",
                "gross_total": "1000.00",
                "net_allocation": "900.00",
                "reported_unit": "naira",
            }
        ],
        ["state", "gross_total", "net_allocation", "reported_unit"],
    )

    result = import_file(
        session,
        ImportRequest(
            path=path,
            source_organization="X",
            revenue_month=date(2026, 3, 1),
            reporting_label="Bad March 2026",
            is_demo=False,
        ),
    )

    codes = set(session.scalars(select(ValidationResult.rule_code)))
    assert "IMPORT_INVALID_STATE_ALIAS" in codes
    assert result.blocking_finding_count >= 1


def test_resolve_columns_finds_named_headers() -> None:
    table = [
        ["1", "2", "3", "18", "19"],
        ["S/n", "Beneficiaries", "Statutory Allocation", "Total Gross Amount", "Total Net Amount"],
        ["1", "Lagos", "x", "42,028,139,677.58", "31,638,718,887.15"],
    ]
    assert _resolve_columns(table) == (1, 3, 4, 1)
