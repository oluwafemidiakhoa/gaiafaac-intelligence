from __future__ import annotations

import hashlib
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from gaiafaac_api.database.enums import ProcessingStatus, SourceStatus, VerificationStatus
from gaiafaac_api.database.liability_models import LiabilityMetric, StateLiabilityRecord
from gaiafaac_api.database.models import SourceDocument, State
from gaiafaac_api.pipeline.errors import ImportContractError
from gaiafaac_api.pipeline.state_financials.extract import extract_state_liability_source

OYO_2021_ARREARS_SUMMARY = "\n".join(
    (
        "TOTAL CONTRACTOR 4,338,068,360.63",
        "TOTAL PENSIONS AND GRATUITY 29,935,642,098.27",
        "SALARY ARREARS -",
        "OTHER JUDGEMENT ARREARS 106,468,643.85",
        "TOTAL DOMESTIC ARREARS 34,380,179,102.75",
    )
)


def _state(session: Session, *, name: str = "Oyo", code: str = "OY") -> State:
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
    state_name: str = "Oyo",
    state_code: str = "OY",
    evidence_kind: str = "contractor-arrears-register",
    fiscal_year: int = 2021,
    body: bytes = b"%PDF-liability-fixture",
) -> SourceDocument:
    path = tmp_path / f"{state_code.lower()}-{fiscal_year}-{evidence_kind}.pdf"
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
        document_version=(
            f"state-financial-{evidence_kind}-{state_code.lower()}-{fiscal_year}"
        ),
        is_demo=False,
    )
    session.add(source)
    session.flush()
    return source


def test_extracts_oyo_arrears_summary_into_unpublished_review_records(
    session: Session,
    tmp_path: Path,
) -> None:
    _state(session)
    source = _source(session, tmp_path)

    result = extract_state_liability_source(
        session,
        source_document_id=source.id,
        text_reader=lambda _path: [(15, OYO_2021_ARREARS_SUMMARY)],
    )

    records = list(
        session.scalars(
            select(StateLiabilityRecord).where(
                StateLiabilityRecord.source_document_id == source.id
            )
        )
    )
    by_metric = {record.metric: record for record in records}

    assert result.records_extracted == 5
    assert result.total_domestic_arrears == Decimal("34380179102.75")
    assert len(records) == 5
    assert set(by_metric) == set(LiabilityMetric)
    assert by_metric[LiabilityMetric.CONTRACTOR_ARREARS].amount == Decimal("4338068360.63")
    assert by_metric[LiabilityMetric.PENSIONS_AND_GRATUITY_ARREARS].amount == Decimal(
        "29935642098.27"
    )
    assert by_metric[LiabilityMetric.SALARY_ARREARS].amount is None
    assert by_metric[LiabilityMetric.SALARY_ARREARS].amount_text == "-"
    assert by_metric[LiabilityMetric.OTHER_JUDGMENT_ARREARS].amount == Decimal("106468643.85")
    assert all(record.currency == "NGN" for record in records)
    assert all(record.source_page == 15 for record in records)
    assert all(
        record.verification_status is VerificationStatus.REQUIRES_REVIEW for record in records
    )
    assert all(not record.is_published for record in records)
    assert source.processing_status is ProcessingStatus.READY_FOR_REVIEW
    assert source.source_status is SourceStatus.READY_FOR_REVIEW


def test_liability_reconciliation_failure_rolls_back_batch(
    session: Session,
    tmp_path: Path,
) -> None:
    _state(session)
    source = _source(session, tmp_path)
    broken = OYO_2021_ARREARS_SUMMARY.replace(
        "TOTAL DOMESTIC ARREARS 34,380,179,102.75",
        "TOTAL DOMESTIC ARREARS 34,380,179,102.76",
    )

    with pytest.raises(ImportContractError, match="reconciliation failed"):
        extract_state_liability_source(
            session,
            source_document_id=source.id,
            text_reader=lambda _path: [(15, broken)],
        )

    count = session.scalar(select(func.count()).select_from(StateLiabilityRecord))
    assert count == 0


def test_audited_statement_fails_closed_until_adapter_is_verified(
    session: Session,
    tmp_path: Path,
) -> None:
    _state(session)
    source = _source(
        session,
        tmp_path,
        evidence_kind="audited-financial-statement",
        fiscal_year=2025,
    )

    with pytest.raises(ImportContractError, match="No deterministic liability extraction adapter"):
        extract_state_liability_source(
            session,
            source_document_id=source.id,
            text_reader=lambda _path: [],
        )


def test_liability_archive_integrity_mismatch_blocks_extraction(
    session: Session,
    tmp_path: Path,
) -> None:
    _state(session)
    source = _source(session, tmp_path)
    Path(source.storage_path).write_bytes(b"%PDF-tampered")

    with pytest.raises(ImportContractError, match="SHA-256 integrity"):
        extract_state_liability_source(
            session,
            source_document_id=source.id,
            text_reader=lambda _path: [(15, OYO_2021_ARREARS_SUMMARY)],
        )
