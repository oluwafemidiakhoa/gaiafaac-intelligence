from __future__ import annotations

import zipfile
from decimal import Decimal
from pathlib import Path

import pytest
from openpyxl import Workbook
from sqlalchemy import func, select

from gaiafaac_api.database.enums import VerificationStatus
from gaiafaac_api.database.igr_models import StateIgrRecord
from gaiafaac_api.database.models import SourceDocument, State
from gaiafaac_api.database.seeds import seed_states
from gaiafaac_api.pipeline.errors import ImportContractError
from gaiafaac_api.pipeline.igr.nbs_import import import_nbs_igr_zip


def _make_nbs_zip(session, tmp_path: Path, *, corrupt_state_code: str | None = None) -> Path:
    seed_states(session)
    states = list(session.scalars(select(State).order_by(State.name)))

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "2024"
    sheet.append(["FULL YEAR 2024 SUB-NATIONAL INTERNALLY GENERATED REVENUE"])
    sheet.append([])
    sheet.append([])
    sheet.append([])
    sheet.append(
        [
            "SN",
            "State",
            "PAYE",
            "Direct Assessment",
            "Road Tax",
            "Stamp Duties",
            "Capital Gains Tax",
            "Withholding Tax",
            "Other Tax",
            "LGA Revenue",
            "Total Tax",
            "MDAs Revenue",
            "Total",
        ]
    )

    for index, state in enumerate(states, start=1):
        total_tax = Decimal("100.00") + Decimal(index)
        mdas = Decimal("50.00")
        total = total_tax + mdas
        if state.code == corrupt_state_code:
            total += Decimal("1.00")
        submitted = "FCT" if state.is_fct else state.name
        sheet.append(
            [
                index,
                submitted,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                float(total_tax),
                float(mdas),
                float(total),
            ]
        )

    xlsx_path = tmp_path / "IGR_DATA_2019_2024.xlsx"
    workbook.save(xlsx_path)
    workbook.close()

    zip_path = tmp_path / "IGR_2024.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(xlsx_path, arcname="IGR_DATA_2019_2024.xlsx")
    return zip_path


def test_imports_37_annual_records_for_review_and_never_publishes(session, tmp_path):
    zip_path = _make_nbs_zip(session, tmp_path)

    result = import_nbs_igr_zip(session, path=zip_path, fiscal_year=2024)

    records = list(session.scalars(select(StateIgrRecord).order_by(StateIgrRecord.igr_amount)))
    assert result.records_imported == 37
    assert len(records) == 37
    assert result.total_igr == sum((record.igr_amount for record in records), Decimal("0.00"))
    assert {record.fiscal_year for record in records} == {2024}
    assert {record.verification_status for record in records} == {
        VerificationStatus.REQUIRES_REVIEW
    }
    assert all(record.is_published is False for record in records)
    assert all(record.is_demo is False for record in records)
    assert all(record.period_start.isoformat() == "2024-01-01" for record in records)
    assert all(record.period_end.isoformat() == "2024-12-31" for record in records)

    source = session.get(SourceDocument, result.source_document_id)
    assert source is not None
    assert source.mime_type == "application/zip"
    assert source.original_filename == "IGR_2024.zip"
    assert source.sha256


def test_reconciliation_failure_rolls_back_everything(session, tmp_path):
    zip_path = _make_nbs_zip(session, tmp_path, corrupt_state_code="LA")

    with pytest.raises(ImportContractError, match="does not reconcile"):
        import_nbs_igr_zip(session, path=zip_path, fiscal_year=2024)

    assert session.scalar(select(func.count()).select_from(StateIgrRecord)) == 0
    assert session.scalar(select(func.count()).select_from(SourceDocument)) == 0
