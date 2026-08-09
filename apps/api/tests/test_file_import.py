import csv
from datetime import date
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from gaiafaac_api.database.enums import VerificationStatus
from gaiafaac_api.database.models import StateAllocation, ValidationResult
from gaiafaac_api.database.seeds import NIGERIAN_STATES, seed_states
from gaiafaac_api.pipeline.extraction.file_import import import_file
from gaiafaac_api.pipeline.extraction.oagf_pdf_adapter import (
    OagfPdfAdapter,
    _resolve_columns,
)
from gaiafaac_api.pipeline.importer import ImportRequest
from gaiafaac_api.pipeline.states import StateNormalizer


def _write_csv(
    path: Path,
    rows: list[dict],
    fields: list[str],
) -> None:
    with path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fields,
        )
        writer.writeheader()
        writer.writerows(rows)


def test_import_file_derives_deductions_and_marks_real(
    session: Session,
    tmp_path: Path,
) -> None:
    seed_states(session)

    path = tmp_path / "real.csv"

    _write_csv(
        path,
        [
            {
                "state": name,
                "gross_total": "1000.00",
                "net_allocation": "900.00",
            }
            for name, *_ in NIGERIAN_STATES
        ],
        [
            "state",
            "gross_total",
            "net_allocation",
        ],
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

    allocations = list(
        session.scalars(
            select(StateAllocation)
        )
    )

    assert len(allocations) == 37

    assert all(
        allocation.is_demo is False
        and allocation.is_published is False
        for allocation in allocations
    )

    # Deductions are derived as gross - net when the source has
    # no explicit deductions column.
    assert all(
        allocation.total_deductions
        == allocation.gross_total - allocation.net_allocation
        for allocation in allocations
    )

    assert all(
        allocation.verification_status
        is VerificationStatus.AUTOMATICALLY_VALIDATED
        for allocation in allocations
    )

    published = session.scalar(
        select(func.count())
        .select_from(StateAllocation)
        .where(
            StateAllocation.is_published.is_(True)
        )
    )

    assert published == 0


def test_import_file_flags_unknown_state(
    session: Session,
    tmp_path: Path,
) -> None:
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
        [
            "state",
            "gross_total",
            "net_allocation",
            "reported_unit",
        ],
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

    codes = set(
        session.scalars(
            select(ValidationResult.rule_code)
        )
    )

    assert "IMPORT_INVALID_STATE_ALIAS" in codes
    assert result.blocking_finding_count >= 1


def test_resolve_columns_finds_named_headers() -> None:
    """Historical OAGF Total ... Amount layout."""

    table = [
        [
            "1",
            "2",
            "3",
            "18",
            "19",
        ],
        [
            "S/n",
            "Beneficiaries",
            "Statutory Allocation",
            "Total Gross Amount",
            "Total Net Amount",
        ],
        [
            "1",
            "Lagos",
            "x",
            "42,028,139,677.58",
            "31,638,718,887.15",
        ],
    ]

    assert _resolve_columns(table) == (
        1,
        3,
        4,
        1,
    )


def test_resolve_columns_accepts_allocation_header_variant() -> None:
    """January 2025-style Total ... Allocation terminology."""

    table = [
        [
            "1",
            "2",
            "3",
            "21",
            "22",
        ],
        [
            "S/n",
            "Beneficiaries",
            "No. of LGCs",
            "Total Gross Allocation",
            "Total Net Allocation",
        ],
        [
            "1",
            "ABIA",
            "17",
            "12,313,768,248.48",
            "11,277,583,006.94",
        ],
    ]

    assert _resolve_columns(table) == (
        1,
        3,
        4,
        1,
    )


def test_resolve_columns_finds_late_multiline_header() -> None:
    """Recent OAGF reports place the named header after title rows."""

    table = [
        [
            "Office of the Accountant General of the Federation",
            "",
            "",
            "",
            "",
        ],
        [
            "Federation Account Department",
            "",
            "",
            "",
            "",
        ],
        [
            "Table III",
            "",
            "",
            "",
            "",
        ],
        [
            "Distribution of Revenue Allocation to State Governments",
            "",
            "",
            "",
            "",
        ],
        [
            "1",
            "2",
            "3",
            "18",
            "19",
        ],
        [
            "S/n",
            "Beneficiaries",
            "No. of LGCs",
            "Total Gross Amount",
            "Total Net Amount",
        ],
        [
            "1",
            "ABIA",
            "17",
            "17,970,769,468.62",
            "17,236,856,587.68",
        ],
    ]

    assert _resolve_columns(table) == (
        1,
        3,
        4,
        5,
    )


def test_locate_scans_beyond_first_eight_pages() -> None:
    """Regression test for reports where Table III appears after page 8."""

    state_table = [
        [
            "1",
            "2",
            "3",
            "18",
            "19",
        ],
        [
            "S/n",
            "Beneficiaries",
            "No. of LGCs",
            "Total Gross Amount",
            "Total Net Amount",
        ],
        [
            "1",
            "ABIA",
            "17",
            "17,417,207,125.64",
            "16,344,866,725.37",
        ],
    ]

    class FakePage:
        def __init__(
            self,
            page_number: int,
            text: str = "",
            tables: list | None = None,
        ) -> None:
            self.page_number = page_number
            self._text = text
            self._tables = tables or []

        def extract_text(self):
            return self._text

        def extract_tables(self):
            return self._tables

    class FakePdf:
        def __init__(self) -> None:
            self.pages = [
                FakePage(page_number)
                for page_number in range(1, 10)
            ]

            self.pages.append(
                FakePage(
                    10,
                    (
                        "Table III Distribution of Revenue Allocation "
                        "to State Governments"
                    ),
                    [state_table],
                )
            )

    located = OagfPdfAdapter._locate(FakePdf())

    assert located is not None

    page_number, table, columns = located

    assert page_number == 10
    assert table == state_table
    assert columns == (
        1,
        3,
        4,
        1,
    )


def test_state_normalizer_accepts_fct_abuja(
    session: Session,
) -> None:
    """OAGF sometimes reports FCT using the literal label 'FCT ABUJA'."""

    seed_states(session)

    normalizer = StateNormalizer.from_session(session)
    match = normalizer.match("FCT ABUJA")

    assert match.state.code == "FC"
    assert match.state.is_fct is True