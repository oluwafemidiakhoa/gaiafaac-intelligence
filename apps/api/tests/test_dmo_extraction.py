from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import select

from gaiafaac_api.database.debt_models import DebtKind, StateDebtRecord
from gaiafaac_api.database.enums import ProcessingStatus, SourceStatus
from gaiafaac_api.database.models import SourceDocument, State
from gaiafaac_api.database.seeds import seed_states
from gaiafaac_api.pipeline.dmo.archive import DMO_ORGANIZATION
from gaiafaac_api.pipeline.dmo.extract import extract_dmo_debt_source, parse_dmo_debt_text
from gaiafaac_api.pipeline.errors import ImportContractError


def _domestic_text() -> str:
    rows = [f"{index} State {index} {index * 1000:,.2f}" for index in range(1, 38)]
    return "SN STATE DEBT STOCK (N)\n" + "\n".join(rows)


def _external_text() -> str:
    rows = [
        f"{index} State {index} {index * 100:,.2f} - - - - {index * 100:,.2f}"
        for index in range(1, 38)
    ]
    return "S/No States and FGN Multilateral Total\n" + "\n".join(rows)


def test_parse_domestic_debt_rows_requires_all_37_serials():
    rows = parse_dmo_debt_text([(1, _domestic_text())], debt_kind=DebtKind.DOMESTIC)

    assert len(rows) == 37
    assert rows[0].state_name == "State 1"
    assert rows[0].amount == Decimal("1000.00")
    assert rows[-1].serial == 37
    assert rows[-1].source_page == 1


def test_parse_external_debt_uses_last_numeric_column_as_total():
    rows = parse_dmo_debt_text([(1, _external_text())], debt_kind=DebtKind.EXTERNAL)

    assert rows[0].amount == Decimal("100.00")
    assert rows[0].components == {"reported_component_1": "100.00"}


def test_parse_debt_rows_fails_closed_when_coverage_is_incomplete():
    text = "\n".join(_domestic_text().splitlines()[:-1])

    with pytest.raises(ImportContractError, match="coverage failed"):
        parse_dmo_debt_text([(1, text)], debt_kind=DebtKind.DOMESTIC)


def test_parse_debt_rows_rejects_duplicate_serials():
    text = _domestic_text() + "\n1 Abia 1,000.00"

    with pytest.raises(ImportContractError, match="Duplicate DMO serial"):
        parse_dmo_debt_text([(1, text)], debt_kind=DebtKind.DOMESTIC)


def test_real_layout_examples_match_dmo_semantics():
    domestic = parse_dmo_debt_text(
        [
            (
                1,
                "\n".join(
                    [
                        "1 ABIA 48,319,385,321.00",
                        *[
                            f"{index} State {index} {index * 1000:,.2f}"
                            for index in range(2, 37)
                        ],
                        "37 FCT 389,875,138,075.16",
                    ]
                ),
            )
        ],
        debt_kind=DebtKind.DOMESTIC,
    )
    external = parse_dmo_debt_text(
        [
            (
                1,
                "\n".join(
                    [
                        "1 Abia 107,163,236.46 - - - - 107,163,236.46",
                        *[
                            f"{index} State {index} {index * 100:,.2f} - - - - {index * 100:,.2f}"
                            for index in range(2, 37)
                        ],
                        "37 FCT 26,798,042.48 - - - - 26,798,042.48",
                    ]
                ),
            )
        ],
        debt_kind=DebtKind.EXTERNAL,
    )

    assert domestic[0].amount == Decimal("48319385321.00")
    assert domestic[-1].amount == Decimal("389875138075.16")
    assert external[0].amount == Decimal("107163236.46")
    assert external[-1].amount == Decimal("26798042.48")


def test_extract_dmo_source_stages_exact_state_fct_coverage(session, tmp_path):
    seed_states(session)
    states = list(session.scalars(select(State).order_by(State.name)))
    assert len(states) == 37
    archive = tmp_path / "source.pdf"
    archive.write_bytes(b"%PDF-test")
    source = SourceDocument(
        source_organization=DMO_ORGANIZATION,
        source_url="https://www.dmo.gov.ng/files/test.pdf",
        original_filename="test.pdf",
        storage_path=str(archive),
        sha256="d" * 64,
        mime_type="application/pdf",
        downloaded_at=datetime.now(UTC),
        processing_status=ProcessingStatus.REGISTERED,
        source_status=SourceStatus.REGISTERED,
        document_version="domestic-2026-03-31",
        is_demo=False,
    )
    session.add(source)
    session.commit()

    lines = [
        f"{index} {state.name} {index * 1_000_000:,.2f}"
        for index, state in enumerate(states, start=1)
    ]
    result = extract_dmo_debt_source(
        session,
        source_document_id=source.id,
        text_reader=lambda _path: [(1, "\n".join(lines))],
    )

    records = list(
        session.scalars(
            select(StateDebtRecord)
            .where(StateDebtRecord.source_document_id == source.id)
            .order_by(StateDebtRecord.state_id)
        )
    )
    assert result.records_extracted == 37
    assert result.currency == "NGN"
    assert len(records) == 37
    assert all(not record.is_published for record in records)
    assert source.source_status is SourceStatus.READY_FOR_REVIEW
    assert source.processing_status is ProcessingStatus.READY_FOR_REVIEW
