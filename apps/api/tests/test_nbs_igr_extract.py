from decimal import Decimal

import pytest
from sqlalchemy import select

from gaiafaac_api.database.enums import ProcessingStatus, SourceStatus, VerificationStatus
from gaiafaac_api.database.igr_models import IgrPeriodType, StateIgrRecord
from gaiafaac_api.database.models import SourceDocument, State
from gaiafaac_api.database.seeds import NIGERIAN_STATES, seed_states
from gaiafaac_api.pipeline.errors import ImportContractError
from gaiafaac_api.pipeline.nbs_igr.extract import extract_nbs_igr_source, parse_nbs_igr_text


def _pages(*, year: int = 2023, missing_code: str | None = None) -> list[tuple[int, str]]:
    pages: list[tuple[int, str]] = []
    page = 1
    for index, (name, code, *_rest) in enumerate(NIGERIAN_STATES, start=1):
        if code == missing_code:
            continue
        amount = f"{index * 1000}.00"
        pages.append((page, f"{name}\n{year} Total IGR N {amount}"))
        page += 1
    return pages


def _appendix_pages(*, missing_code: str | None = None) -> list[tuple[int, str]]:
    """Some report years render each state's own page as an infographic image with no
    extractable text; the same totals are published as a plain appendix table instead."""
    lines = ["APPENDIX", "SN State Total Tax MDAs Revenue Total"]
    serial = 1
    for index, (name, code, *_rest) in enumerate(NIGERIAN_STATES, start=1):
        if code == missing_code:
            continue
        total = f"{index * 1000}.00"
        tax = "-" if index == 1 else f"{index * 900}.00"
        mda = "-" if index != 1 else total
        lines.append(f"{serial} {name} {tax} {mda} {total}")
        serial += 1
    lines.append("Total 9,999.00 9,999.00 9,999.00")
    return [(43, "\n".join(lines))]


def _source(session, tmp_path, *, year: int = 2023) -> SourceDocument:
    path = tmp_path / "nbs-igr.pdf"
    path.write_bytes(b"%PDF-1.7\nfixture")
    source = SourceDocument(
        source_organization="National Bureau of Statistics (NBS)",
        source_url="https://www.nigerianstat.gov.ng/elibrary/read/1241579",
        original_filename="nbs-igr.pdf",
        storage_path=str(path),
        sha256="a" * 64,
        mime_type="application/pdf",
        processing_status=ProcessingStatus.REGISTERED,
        source_status=SourceStatus.REGISTERED,
        document_version=f"igr-{year}-report-1241579",
        is_demo=False,
    )
    session.add(source)
    session.commit()
    return source


def test_parse_nbs_igr_text_reads_annual_state_totals():
    rows = parse_nbs_igr_text(_pages(), fiscal_year=2023)

    assert len(rows) == 37
    assert rows[0].state_name == "Abia"
    assert rows[0].amount == Decimal("1000.00")
    assert rows[-1].state_name == "Zamfara"


def test_parse_nbs_igr_text_falls_back_to_appendix_table():
    rows = parse_nbs_igr_text(_appendix_pages(), fiscal_year=2023)

    assert len(rows) == 37
    by_state = {row.state_name: row for row in rows}
    assert by_state["Abia"].amount == Decimal("1000.00")
    assert by_state["Akwa Ibom"].source_page == 43
    assert by_state["Zamfara"].amount == Decimal(f"{len(NIGERIAN_STATES) * 1000}.00")
    assert "Total" not in by_state


def test_extract_nbs_igr_source_stages_all_states_from_appendix_table(session, tmp_path):
    seed_states(session)
    source = _source(session, tmp_path)

    result = extract_nbs_igr_source(
        session,
        source_document_id=source.id,
        text_reader=lambda _path: _appendix_pages(),
    )

    records = list(
        session.scalars(
            select(StateIgrRecord).where(StateIgrRecord.source_document_id == source.id)
        )
    )
    assert result.records_extracted == 37
    assert len(records) == 37


def test_extract_nbs_igr_source_stages_all_states_for_review(session, tmp_path):
    seed_states(session)
    source = _source(session, tmp_path)

    result = extract_nbs_igr_source(
        session,
        source_document_id=source.id,
        text_reader=lambda _path: _pages(),
    )

    records = list(
        session.scalars(
            select(StateIgrRecord)
            .where(StateIgrRecord.source_document_id == source.id)
            .order_by(StateIgrRecord.state_id)
        )
    )
    refreshed = session.get(SourceDocument, source.id)
    assert result.records_extracted == 37
    assert len(records) == 37
    assert {record.state_id for record in records} == {
        state.id for state in session.scalars(select(State)).all()
    }
    assert all(record.period_type is IgrPeriodType.ANNUAL for record in records)
    assert all(
        record.verification_status is VerificationStatus.REQUIRES_REVIEW for record in records
    )
    assert all(not record.is_published for record in records)
    assert refreshed is not None
    assert refreshed.processing_status is ProcessingStatus.READY_FOR_REVIEW
    assert refreshed.source_status is SourceStatus.READY_FOR_REVIEW


def test_extract_nbs_igr_source_fails_closed_on_missing_jurisdiction(session, tmp_path):
    seed_states(session)
    source = _source(session, tmp_path)

    with pytest.raises(ImportContractError, match="jurisdiction coverage failed"):
        extract_nbs_igr_source(
            session,
            source_document_id=source.id,
            text_reader=lambda _path: _pages(missing_code="ZA"),
        )

    assert (
        session.scalar(
            select(StateIgrRecord.id).where(StateIgrRecord.source_document_id == source.id)
        )
        is None
    )
