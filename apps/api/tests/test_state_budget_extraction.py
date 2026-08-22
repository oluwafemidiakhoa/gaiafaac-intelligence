from __future__ import annotations

import hashlib
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from gaiafaac_api.database.budget_models import BudgetMetric, StateBudgetRecord
from gaiafaac_api.database.enums import ProcessingStatus, SourceStatus, VerificationStatus
from gaiafaac_api.database.models import SourceDocument, State
from gaiafaac_api.pipeline.errors import ImportContractError
from gaiafaac_api.pipeline.state_budget.extract import extract_state_budget_source

ZAMFARA_2026_SUMMARY = "\n".join(
    (
        "Zamfara State Government 2026 Approved Budget Summary",
        "Recurrent Revenue 256,014,575,000.00 240,919,075,000.00 "
        "149,039,920,738.31 364,717,300,000.00 3,132,000,000.00",
        "11 - GOVERNMENT SHARE OF FAAC 223,150,000,000.00 200,500,000,000.00 "
        "123,357,891,547.76 324,652,711,000.00 3,132,000,000.00",
        "12 - INDEPENDENT REVENUE 32,864,575,000.00 40,419,075,000.00 "
        "25,682,029,190.55 40,064,589,000.00 -",
        "Recurrent Expenditure 151,680,000,000.00 154,155,208,328.96 "
        "60,353,332,467.85 149,846,470,000.00 2,202,000,000.00",
        "21 - PERSONNEL COST 58,386,834,000.00 57,743,149,328.96 "
        "31,878,315,286.83 48,008,900,000.00 -",
        "Other Non Debt Recurrent 78,159,166,000.00 79,924,059,000.00 "
        "20,526,207,889.81 88,817,570,000.00 2,202,000,000.00",
        "Debt Service 15,134,000,000.00 16,488,000,000.00 7,948,809,291.21 13,020,000,000.00 -",
        "Transfer to Capital Account 104,334,575,000.00 86,763,866,671.04 "
        "127,455,107,806.68 214,870,830,000.00 930,000,000.00",
        "Other Receipts 290,000,000,000.00 257,764,000,000.00 "
        "28,088,903,036.72 506,619,700,000.00 4,000,000,000.00",
        "13 - AID AND GRANTS 141,272,384,000.00 114,272,384,000.00 - "
        "138,300,000,000.00 4,000,000,000.00",
        "14 - CAPITAL DEVELOPMENTFUND (CDF) RECEIPTS 148,727,616,000.00 "
        "143,491,616,000.00 28,088,903,036.72 368,319,700,000.00 -",
        "23 - CAPITAL EXPENDITURE (Capital Expenditure) 394,334,575,000.00 "
        "344,527,866,671.04 66,829,832,913.16 721,490,530,000.00 4,930,000,000.00",
        "Total Revenue (including OB) 546,014,575,000.00 498,683,075,000.00 "
        "215,897,343,311.25 871,337,000,000.00 7,132,000,000.00",
        "Total Expenditure 546,014,575,000.00 498,683,075,000.00 "
        "127,183,165,381.01 871,337,000,000.00 7,132,000,000.00",
    )
)


def _state(session: Session, *, name: str, code: str) -> State:
    state = State(
        name=name,
        code=code,
        slug=name.lower().replace(" ", "-"),
        geopolitical_zone="North West" if code == "ZA" else "South West",
        capital="Gusau" if code == "ZA" else "Ibadan",
        is_fct=False,
    )
    session.add(state)
    session.flush()
    return state


def _source(
    session: Session,
    tmp_path: Path,
    *,
    state_name: str,
    state_code: str,
    fiscal_year: int = 2026,
    body: bytes = b"%PDF-budget-fixture",
) -> SourceDocument:
    path = tmp_path / f"{state_code.lower()}-{fiscal_year}.pdf"
    path.write_bytes(body)
    source = SourceDocument(
        source_organization=f"{state_name} State Government",
        source_url=f"https://example.invalid/{path.name}",
        original_filename=path.name,
        storage_path=str(path),
        sha256=hashlib.sha256(body).hexdigest(),
        mime_type="application/pdf",
        processing_status=ProcessingStatus.REGISTERED,
        source_status=SourceStatus.REGISTERED,
        document_version=f"approved-budget-{state_code.lower()}-{fiscal_year}",
        is_demo=False,
    )
    session.add(source)
    session.flush()
    return source


def test_extracts_zamfara_summary_into_unpublished_review_records(
    session: Session, tmp_path: Path
) -> None:
    _state(session, name="Zamfara", code="ZA")
    source = _source(session, tmp_path, state_name="Zamfara", state_code="ZA")

    result = extract_state_budget_source(
        session,
        source_document_id=source.id,
        text_reader=lambda _path: [(23, ZAMFARA_2026_SUMMARY)],
    )

    records = list(
        session.scalars(
            select(StateBudgetRecord).where(StateBudgetRecord.source_document_id == source.id)
        )
    )
    assert result.records_extracted == 14
    assert result.total_expenditure == Decimal("871337000000.00")
    assert len(records) == 14
    assert {record.metric for record in records} == set(BudgetMetric)
    assert all(record.currency == "NGN" for record in records)
    assert all(
        record.verification_status is VerificationStatus.REQUIRES_REVIEW for record in records
    )
    assert all(not record.is_published for record in records)
    assert all(record.source_page == 23 for record in records)
    assert source.processing_status is ProcessingStatus.READY_FOR_REVIEW
    assert source.source_status is SourceStatus.READY_FOR_REVIEW

    debt_service = next(
        record for record in records if record.metric is BudgetMetric.BUDGETED_DEBT_SERVICE
    )
    assert debt_service.amount == Decimal("13020000000.00")
    assert debt_service.amount_original == "13,020,000,000.00"


def test_unsupported_state_adapter_fails_closed(session: Session, tmp_path: Path) -> None:
    _state(session, name="Oyo", code="OY")
    source = _source(session, tmp_path, state_name="Oyo", state_code="OY")

    with pytest.raises(
        ImportContractError, match="No deterministic approved-budget extraction adapter"
    ):
        extract_state_budget_source(
            session,
            source_document_id=source.id,
            text_reader=lambda _path: [],
        )

    count = session.scalar(select(func.count()).select_from(StateBudgetRecord))
    assert count == 0
    assert source.processing_status is ProcessingStatus.REGISTERED
    assert source.source_status is SourceStatus.REGISTERED


def test_reconciliation_failure_rolls_back_batch(session: Session, tmp_path: Path) -> None:
    _state(session, name="Zamfara", code="ZA")
    source = _source(session, tmp_path, state_name="Zamfara", state_code="ZA")
    broken = ZAMFARA_2026_SUMMARY.replace(
        "127,183,165,381.01 871,337,000,000.00 7,132,000,000.00",
        "127,183,165,381.01 871,337,000,001.00 7,132,000,000.00",
    )

    with pytest.raises(ImportContractError, match="reconciliation failed"):
        extract_state_budget_source(
            session,
            source_document_id=source.id,
            text_reader=lambda _path: [(23, broken)],
        )

    count = session.scalar(select(func.count()).select_from(StateBudgetRecord))
    assert count == 0


def test_archive_integrity_mismatch_blocks_extraction(session: Session, tmp_path: Path) -> None:
    _state(session, name="Zamfara", code="ZA")
    source = _source(session, tmp_path, state_name="Zamfara", state_code="ZA")
    Path(source.storage_path).write_bytes(b"%PDF-tampered")

    with pytest.raises(ImportContractError, match="SHA-256 integrity"):
        extract_state_budget_source(
            session,
            source_document_id=source.id,
            text_reader=lambda _path: [(23, ZAMFARA_2026_SUMMARY)],
        )
