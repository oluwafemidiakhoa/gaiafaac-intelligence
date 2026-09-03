from decimal import Decimal

import pytest
from sqlalchemy import select

from gaiafaac_api.database.enums import ProcessingStatus, SourceStatus, VerificationStatus
from gaiafaac_api.database.igr_models import IgrPeriodType, StateIgrRecord
from gaiafaac_api.database.models import SourceDocument, State
from gaiafaac_api.database.seeds import NIGERIAN_STATES, seed_states
from gaiafaac_api.pipeline.errors import ImportContractError
from gaiafaac_api.pipeline.nbs_igr.extract import (
    extract_nbs_igr_source,
    extract_pending_igr_sources,
    parse_nbs_igr_text,
)


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


def _appendix_pages_without_serial_column() -> list[tuple[int, str]]:
    """Some report years' appendix table has no serial-number column at all - just
    "State Total Tax MDAs Revenue Total" - and a footnote asterisk can sit directly on
    a state name with no space (observed live: "KADUNA*")."""
    lines = ["APPENDIX", "STATE TOTAL TAX MDAs REVENUE TOTAL"]
    for index, (name, _code, *_rest) in enumerate(NIGERIAN_STATES, start=1):
        tax = f"{index * 800}.00"
        mda = f"{index * 200}.00"
        total = f"{index * 1000}.00"
        display_name = f"{name.upper()}*" if name == "Kaduna" else name.upper()
        lines.append(f"{display_name} {tax} {mda} {total}")
    return [(14, "\n".join(lines))]


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


def test_parse_nbs_igr_text_reads_appendix_table_with_no_serial_column():
    rows = parse_nbs_igr_text(_appendix_pages_without_serial_column(), fiscal_year=2022)

    assert len(rows) == 37
    by_state = {row.state_name: row for row in rows}
    assert "Total" not in by_state
    kaduna = next(name for name in by_state if name.upper() == "KADUNA")
    assert by_state[kaduna].amount is not None


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


def test_extract_pending_igr_sources_isolates_failures(session, tmp_path):
    seed_states(session)

    good_path = tmp_path / "good.pdf"
    good_path.write_bytes(b"%PDF-test")
    good_source = SourceDocument(
        source_organization="National Bureau of Statistics (NBS)",
        source_url="https://www.nigerianstat.gov.ng/elibrary/read/1",
        original_filename="good.pdf",
        storage_path=str(good_path),
        sha256="e" * 64,
        mime_type="application/pdf",
        processing_status=ProcessingStatus.REGISTERED,
        source_status=SourceStatus.REGISTERED,
        document_version="igr-2023-report-1",
        is_demo=False,
    )
    bad_path = tmp_path / "bad.pdf"
    bad_path.write_bytes(b"%PDF-test")
    bad_source = SourceDocument(
        source_organization="National Bureau of Statistics (NBS)",
        source_url="https://www.nigerianstat.gov.ng/elibrary/read/2",
        original_filename="bad.pdf",
        storage_path=str(bad_path),
        sha256="f" * 64,
        mime_type="application/pdf",
        processing_status=ProcessingStatus.REGISTERED,
        source_status=SourceStatus.REGISTERED,
        document_version="igr-2023-report-2",
        is_demo=False,
    )
    session.add_all([good_source, bad_source])
    session.commit()

    good_resolved = str(good_path.resolve())

    def text_reader(path):
        if str(path) == good_resolved:
            return _pages()
        return [(1, "1 Abia not-a-number")]

    outcomes = extract_pending_igr_sources(session, text_reader=text_reader)

    by_id = {outcome.source_document_id: outcome for outcome in outcomes}
    assert len(outcomes) == 2
    assert by_id[str(good_source.id)].status == "extracted"
    assert by_id[str(good_source.id)].records_extracted == 37
    assert by_id[str(bad_source.id)].status == "failed"
    assert by_id[str(bad_source.id)].error is not None

    good_records = list(
        session.scalars(
            select(StateIgrRecord).where(StateIgrRecord.source_document_id == good_source.id)
        )
    )
    assert len(good_records) == 37
    assert (
        session.scalar(
            select(StateIgrRecord.id).where(StateIgrRecord.source_document_id == bad_source.id)
        )
        is None
    )
