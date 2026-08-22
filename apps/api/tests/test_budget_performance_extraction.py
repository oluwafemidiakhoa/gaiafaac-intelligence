from __future__ import annotations

import hashlib
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from gaiafaac_api.database.budget_models import (
    BudgetPerformanceMetric,
    StateBudgetPerformanceRecord,
)
from gaiafaac_api.database.enums import ProcessingStatus, SourceStatus, VerificationStatus
from gaiafaac_api.database.models import SourceDocument, State
from gaiafaac_api.pipeline.errors import ImportContractError
from gaiafaac_api.pipeline.state_budget.performance_extract import (
    extract_budget_performance_source,
)

OYO_2026_Q2_TABLE1 = "\n".join(
    (
        "Oyo State Government 2026 Q2 Budget Performance Report - Summary",
        "Table 1: Budget Implementation Summary",
        "Opening Balance 100.00 0.00 0.00 0.0% 100.00",
        "Recurrent Revenue 1,000.00 150.00 300.00 30.0% 700.00",
        "11 - GOVERNMENT SHARE OF FAAC (STATUTORY REVENUE) "
        "600.00 100.00 200.00 33.3% 400.00",
        "12 - INDEPENDENT REVENUE 400.00 50.00 100.00 25.0% 300.00",
        "Recurrent Expenditure 600.00 100.00 200.00 33.3% 400.00",
        "21 - PERSONNEL COST (INCLUDING 2201 WHERE APPROPRIATE) "
        "300.00 50.00 100.00 33.3% 200.00",
        "22 - OTHER RECURRENT COSTS (EXCLUDING 2201) "
        "300.00 50.00 100.00 33.3% 200.00",
        "2202 - OVERHEAD COST 200.00 40.00 80.00 40.0% 120.00",
        "OTHER RECURRENT (2203-2209) 100.00 10.00 20.00 20.0% 80.00",
        "Transfer to Capital Account 400.00 100.00 200.00 50.0% 200.00",
        "Other Receipts 500.00 50.00 100.00 20.0% 400.00",
        "13 - AID AND GRANTS 200.00 20.00 40.00 20.0% 160.00",
        "14 - CAPITAL DEVELOPMENT FUND (CDF) RECEIPTS "
        "300.00 30.00 60.00 20.0% 240.00",
        "Capital Expenditure 900.00 150.00 300.00 33.3% 600.00",
        "Total Revenue (including OB) 1,600.00 200.00 400.00 25.0% 1,200.00",
        "Total Expenditure 1,500.00 250.00 500.00 33.3% 1,000.00",
    )
)


def _state(session: Session, *, name: str, code: str) -> State:
    state = State(
        name=name,
        code=code,
        slug=name.lower(),
        geopolitical_zone="South West" if code == "OY" else "North West",
        capital="Ibadan" if code == "OY" else "Gusau",
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
    quarter: int = 2,
    body: bytes = b"%PDF-performance-fixture",
) -> SourceDocument:
    path = tmp_path / f"{state_code.lower()}-2026-q{quarter}.pdf"
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
        document_version=f"budget-performance-{state_code.lower()}-2026-q{quarter}",
        is_demo=False,
    )
    session.add(source)
    session.flush()
    return source


def test_extracts_oyo_table1_into_unpublished_review_records(
    session: Session, tmp_path: Path
) -> None:
    _state(session, name="Oyo", code="OY")
    source = _source(session, tmp_path, state_name="Oyo", state_code="OY")

    result = extract_budget_performance_source(
        session,
        source_document_id=source.id,
        text_reader=lambda _path: [(7, OYO_2026_Q2_TABLE1)],
    )

    records = list(
        session.scalars(
            select(StateBudgetPerformanceRecord).where(
                StateBudgetPerformanceRecord.source_document_id == source.id
            )
        )
    )
    assert result.records_extracted == 16
    assert result.total_revenue_ytd == Decimal("400.00")
    assert result.total_expenditure_ytd == Decimal("500.00")
    assert len(records) == 16
    assert {record.metric for record in records} == set(BudgetPerformanceMetric)
    assert all(record.quarter == 2 for record in records)
    assert all(record.currency == "NGN" for record in records)
    assert all(
        record.verification_status is VerificationStatus.REQUIRES_REVIEW for record in records
    )
    assert all(not record.is_published for record in records)
    assert all(record.source_page == 7 for record in records)
    assert source.processing_status is ProcessingStatus.READY_FOR_REVIEW
    assert source.source_status is SourceStatus.READY_FOR_REVIEW


def test_reconciliation_failure_rolls_back_performance_batch(
    session: Session, tmp_path: Path
) -> None:
    _state(session, name="Oyo", code="OY")
    source = _source(session, tmp_path, state_name="Oyo", state_code="OY")
    broken = OYO_2026_Q2_TABLE1.replace(
        "Total Expenditure 1,500.00 250.00 500.00 33.3% 1,000.00",
        "Total Expenditure 1,500.00 250.00 501.00 33.4% 999.00",
    )

    with pytest.raises(ImportContractError, match="reconciliation failed"):
        extract_budget_performance_source(
            session,
            source_document_id=source.id,
            text_reader=lambda _path: [(7, broken)],
        )

    count = session.scalar(select(func.count()).select_from(StateBudgetPerformanceRecord))
    assert count == 0


def test_unsupported_performance_state_fails_closed(session: Session, tmp_path: Path) -> None:
    _state(session, name="Zamfara", code="ZA")
    source = _source(session, tmp_path, state_name="Zamfara", state_code="ZA")

    with pytest.raises(ImportContractError, match="No deterministic budget-performance"):
        extract_budget_performance_source(
            session,
            source_document_id=source.id,
            text_reader=lambda _path: [],
        )


def test_performance_archive_integrity_mismatch_blocks_extraction(
    session: Session, tmp_path: Path
) -> None:
    _state(session, name="Oyo", code="OY")
    source = _source(session, tmp_path, state_name="Oyo", state_code="OY")
    Path(source.storage_path).write_bytes(b"%PDF-tampered")

    with pytest.raises(ImportContractError, match="SHA-256 integrity"):
        extract_budget_performance_source(
            session,
            source_document_id=source.id,
            text_reader=lambda _path: [(7, OYO_2026_Q2_TABLE1)],
        )
