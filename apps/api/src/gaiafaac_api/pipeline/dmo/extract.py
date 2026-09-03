from __future__ import annotations

import re
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.debt_models import DebtKind, StateDebtRecord
from gaiafaac_api.database.enums import ProcessingStatus, SourceStatus, VerificationStatus
from gaiafaac_api.database.models import SourceDocument, State
from gaiafaac_api.pipeline.dmo.archive import DMO_ORGANIZATION
from gaiafaac_api.pipeline.errors import ImportContractError, StateNormalizationError
from gaiafaac_api.pipeline.states import StateNormalizer
from gaiafaac_api.services.object_storage import source_local_copy

_ROW_RE = re.compile(r"^\s*(?P<serial>\d{1,2})\s*(?P<body>.+?)\s*$")
# pdfplumber sometimes splits a right-aligned money column's leading digit(s) away
# from the rest of the number in dense multi-column reports (observed live, all in
# amount columns since no Nigerian state/FCT name contains a digit): "1 05,824,..."
# instead of "105,824,...", or "1 ,600,000..." instead of "1,600,000...". Removing
# whitespace strictly between a digit and a following digit-or-comma is safe because
# state names never contain a digit.
_STRAY_DIGIT_SPLIT_RE = re.compile(r"(?<=\d)\s+(?=[\d,])")
_MONEY_RE = re.compile(r"(?:\d{1,3}(?:,\d{3})+|\d+)\.\d{2}")
_VERSION_RE = re.compile(r"^(domestic|external)-(\d{4}-\d{2}-\d{2})$")
_TOTAL_RE = re.compile(r"^\s*total\b", re.IGNORECASE)
_CENT = Decimal("0.01")


@dataclass(frozen=True)
class ParsedDebtRow:
    serial: int
    state_name: str
    amount: Decimal
    amount_original: str
    components: dict[str, str]
    source_page: int


@dataclass(frozen=True)
class DebtExtractionResult:
    source_document_id: str
    debt_kind: str
    as_of_date: str
    currency: str
    records_extracted: int
    total_amount: Decimal


@dataclass(frozen=True)
class PendingExtractionOutcome:
    source_document_id: str
    status: str
    records_extracted: int | None = None
    total_amount: str | None = None
    error: str | None = None


TextReader = Callable[[Path], list[tuple[int, str]]]


def _pdf_text(path: Path) -> list[tuple[int, str]]:
    import pdfplumber

    pages: list[tuple[int, str]] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            pages.append((page.page_number, page.extract_text() or ""))
    return pages


def _money(value: str, *, serial: int) -> Decimal:
    try:
        amount = Decimal(value.replace(",", "")).quantize(_CENT, rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError) as error:
        raise ImportContractError(f"Invalid DMO debt value for row {serial}: {value!r}") from error
    if amount < 0:
        raise ImportContractError(f"Negative DMO debt value for row {serial}: {amount}")
    return amount


def parse_dmo_debt_text(
    pages: list[tuple[int, str]],
    *,
    debt_kind: DebtKind,
) -> list[ParsedDebtRow]:
    """Parse only numbered state/FCT rows from verified DMO debt layouts."""

    parsed: list[ParsedDebtRow] = []
    seen_serials: set[int] = set()
    for page_number, text in pages:
        for source_line in text.splitlines():
            raw_line = _STRAY_DIGIT_SPLIT_RE.sub("", source_line)
            if _TOTAL_RE.match(raw_line):
                # The "Total" row marks the end of the numbered state table. Footnotes
                # below it (e.g. "2 The Domestic Debt Stock...") can themselves start
                # with a small leading digit and must never be mistaken for table rows.
                return _finalize_dmo_rows(parsed, seen_serials)
            match = _ROW_RE.match(raw_line)
            if match is None:
                continue
            serial = int(match.group("serial"))
            if not 1 <= serial <= 37:
                continue
            if serial in seen_serials:
                raise ImportContractError(f"Duplicate DMO serial number: {serial}")
            body = match.group("body")
            money_matches = list(_MONEY_RE.finditer(body))
            if not money_matches:
                raise ImportContractError(f"DMO row {serial} has no monetary value")
            first_money = money_matches[0]
            state_name = body[: first_money.start()].strip()
            if not state_name:
                raise ImportContractError(f"DMO row {serial} has no jurisdiction name")
            total_match = money_matches[-1]
            total_text = total_match.group(0)
            components: dict[str, str] = {}
            if debt_kind is DebtKind.EXTERNAL:
                component_values = [item.group(0) for item in money_matches[:-1]]
                components = {
                    f"reported_component_{index + 1}": value
                    for index, value in enumerate(component_values)
                }
            parsed.append(
                ParsedDebtRow(
                    serial=serial,
                    state_name=state_name,
                    amount=_money(total_text, serial=serial),
                    amount_original=total_text,
                    components=components,
                    source_page=page_number,
                )
            )
            seen_serials.add(serial)
    return _finalize_dmo_rows(parsed, seen_serials)


def _finalize_dmo_rows(parsed: list[ParsedDebtRow], seen_serials: set[int]) -> list[ParsedDebtRow]:
    if len(parsed) != 37 or seen_serials != set(range(1, 38)):
        missing = sorted(set(range(1, 38)) - seen_serials)
        raise ImportContractError(
            f"DMO jurisdiction coverage failed: rows={len(parsed)}, missing_serials={missing}"
        )
    return sorted(parsed, key=lambda item: item.serial)


def _source_contract(source: SourceDocument) -> tuple[DebtKind, date, str]:
    if source.is_demo:
        raise ImportContractError("Demo source documents cannot enter the DMO debt pipeline")
    if "Debt Management Office" not in source.source_organization:
        raise ImportContractError("Source document is not registered as DMO evidence")
    match = _VERSION_RE.match(source.document_version)
    if match is None:
        raise ImportContractError(
            "DMO source document version must encode debt kind and as-of date"
        )
    kind = DebtKind(match.group(1))
    as_of_date = date.fromisoformat(match.group(2))
    currency = "NGN" if kind is DebtKind.DOMESTIC else "USD"
    return kind, as_of_date, currency


def extract_dmo_debt_source(
    session: Session,
    *,
    source_document_id: uuid.UUID,
    text_reader: TextReader = _pdf_text,
) -> DebtExtractionResult:
    """Extract an archived DMO source into unpublished review records."""

    source = session.get(SourceDocument, source_document_id)
    if source is None:
        raise ImportContractError("DMO source document does not exist")
    kind, as_of_date, currency = _source_contract(source)
    if (
        session.scalar(
            select(StateDebtRecord.id).where(StateDebtRecord.source_document_id == source.id)
        )
        is not None
    ):
        raise ImportContractError("DMO source has already been extracted")

    with source_local_copy(source.storage_path) as path:
        if not path.is_file():
            raise ImportContractError(f"DMO archive path is not a regular file: {path}")
        text_rows = text_reader(path)

    try:
        rows = parse_dmo_debt_text(text_rows, debt_kind=kind)
        normalizer = StateNormalizer.from_session(session)
        expected_states = list(session.scalars(select(State).order_by(State.code)))
        expected_ids = {state.id for state in expected_states}
        seen_ids: set[uuid.UUID] = set()
        records: list[StateDebtRecord] = []
        total_amount = Decimal("0.00")
        for row in rows:
            try:
                match = normalizer.match(row.state_name)
            except StateNormalizationError as error:
                raise ImportContractError(
                    f"Unknown DMO jurisdiction at serial {row.serial}: {row.state_name!r}"
                ) from error
            if match.state.id in seen_ids:
                raise ImportContractError(
                    f"Duplicate DMO jurisdiction at serial {row.serial}: {row.state_name!r}"
                )
            records.append(
                StateDebtRecord(
                    state_id=match.state.id,
                    source_document_id=source.id,
                    debt_kind=kind,
                    as_of_date=as_of_date,
                    debt_amount=row.amount,
                    debt_amount_original=row.amount_original,
                    currency=currency,
                    components=row.components,
                    source_page=row.source_page,
                    source_table=f"DMO {kind.value} state/FCT debt stock",
                    verification_status=VerificationStatus.REQUIRES_REVIEW,
                    is_demo=False,
                    is_published=False,
                )
            )
            seen_ids.add(match.state.id)
            total_amount += row.amount

        missing = expected_ids - seen_ids
        if len(records) != 37 or missing or seen_ids != expected_ids:
            missing_codes = sorted(state.code for state in expected_states if state.id in missing)
            raise ImportContractError(
                "DMO jurisdiction coverage failed after normalization: "
                f"records={len(records)}, missing={missing_codes}"
            )

        session.add_all(records)
        source.processing_status = ProcessingStatus.READY_FOR_REVIEW
        source.source_status = SourceStatus.READY_FOR_REVIEW
        session.commit()
    except Exception:
        session.rollback()
        raise

    return DebtExtractionResult(
        source_document_id=str(source.id),
        debt_kind=kind.value,
        as_of_date=as_of_date.isoformat(),
        currency=currency,
        records_extracted=len(records),
        total_amount=total_amount.quantize(_CENT),
    )


def extract_pending_debt_sources(
    session: Session, *, text_reader: TextReader = _pdf_text
) -> list[PendingExtractionOutcome]:
    """Extract every archived-but-unextracted DMO source. Never publishes; a failure on
    one source is recorded and does not block the others."""
    source_ids = list(
        session.scalars(
            select(SourceDocument.id).where(
                SourceDocument.source_organization == DMO_ORGANIZATION,
                SourceDocument.processing_status == ProcessingStatus.REGISTERED,
                SourceDocument.is_demo.is_(False),
            )
        )
    )
    outcomes: list[PendingExtractionOutcome] = []
    for source_id in source_ids:
        try:
            result = extract_dmo_debt_source(
                session, source_document_id=source_id, text_reader=text_reader
            )
            outcomes.append(
                PendingExtractionOutcome(
                    source_document_id=result.source_document_id,
                    status="extracted",
                    records_extracted=result.records_extracted,
                    total_amount=format(result.total_amount, "f"),
                )
            )
        except ImportContractError as error:
            session.rollback()
            outcomes.append(
                PendingExtractionOutcome(
                    source_document_id=str(source_id),
                    status="failed",
                    error=str(error),
                )
            )
    return outcomes
