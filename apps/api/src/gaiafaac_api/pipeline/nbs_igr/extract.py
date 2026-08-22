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

from gaiafaac_api.database.enums import (
    ProcessingStatus,
    ReportedUnit,
    SourceStatus,
    VerificationStatus,
)
from gaiafaac_api.database.igr_models import IgrPeriodType, StateIgrRecord
from gaiafaac_api.database.models import SourceDocument, State
from gaiafaac_api.pipeline.errors import ImportContractError, StateNormalizationError
from gaiafaac_api.pipeline.states import StateNormalizer

_VERSION_RE = re.compile(r"^igr-(?P<year>20\d{2})-report-(?P<report_id>\d+)$")
_AMOUNT_RE = re.compile(r"[N₦]\s*(?P<amount>\d[\d,]*\.\d{2})", re.IGNORECASE)
_HEADER_RE = re.compile(r"INTERNALLY\s+GENERATED\s+REVENUE", re.IGNORECASE)
_CENT = Decimal("0.01")


@dataclass(frozen=True)
class ParsedIgrRow:
    state_name: str
    amount: Decimal
    amount_original: str
    source_page: int


@dataclass(frozen=True)
class IgrExtractionResult:
    source_document_id: str
    fiscal_year: int
    records_extracted: int
    total_amount: Decimal


TextReader = Callable[[Path], list[tuple[int, str]]]


def _pdf_text(path: Path) -> list[tuple[int, str]]:
    import pdfplumber

    pages: list[tuple[int, str]] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            pages.append((page.page_number, page.extract_text() or ""))
    return pages


def _money(value: str, *, state_name: str) -> Decimal:
    try:
        amount = Decimal(value.replace(",", "")).quantize(_CENT, rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError) as error:
        raise ImportContractError(
            f"Invalid NBS IGR value for {state_name!r}: {value!r}"
        ) from error
    if amount < 0:
        raise ImportContractError(f"Negative NBS IGR value for {state_name!r}: {amount}")
    return amount


def _state_candidate(prefix: str) -> str | None:
    lines = [" ".join(line.split()) for line in prefix.splitlines() if line.strip()]
    for line in reversed(lines):
        upper = line.upper()
        if upper in {"TOTAL", "STATE", "NBS", "NATIONAL BUREAU OF STATISTICS"}:
            continue
        if _HEADER_RE.search(line):
            continue
        if line.isdigit():
            continue
        return line
    return None


def parse_nbs_igr_text(
    pages: list[tuple[int, str]],
    *,
    fiscal_year: int,
) -> list[ParsedIgrRow]:
    """Parse annual state/FCT total IGR observations from the archived NBS report.

    The parser intentionally targets only the report's per-jurisdiction infographic pattern
    for the requested fiscal year. It does not infer missing jurisdictions or reuse prior years.
    """

    target = re.compile(
        rf"(?<!\d){fiscal_year}(?!\d)\s+Total\s+IGR\s+"
        rf"(?P<value>[N₦]\s*\d[\d,]*\.\d{{2}})",
        re.IGNORECASE,
    )
    parsed: list[ParsedIgrRow] = []
    seen_pages: set[int] = set()
    for page_number, text in pages:
        matches = list(target.finditer(text))
        if not matches:
            continue
        if len(matches) > 1:
            raise ImportContractError(
                f"NBS IGR page {page_number} contains multiple {fiscal_year} total-IGR blocks"
            )
        match = matches[0]
        state_name = _state_candidate(text[: match.start()])
        if state_name is None:
            continue
        if state_name.strip().casefold() == "total":
            continue
        if page_number in seen_pages:
            raise ImportContractError(f"Duplicate NBS IGR page number: {page_number}")
        original = match.group("value")
        amount_match = _AMOUNT_RE.fullmatch(original)
        if amount_match is None:
            raise ImportContractError(
                f"NBS IGR page {page_number} has an invalid total-IGR value: {original!r}"
            )
        parsed.append(
            ParsedIgrRow(
                state_name=state_name,
                amount=_money(amount_match.group("amount"), state_name=state_name),
                amount_original=original,
                source_page=page_number,
            )
        )
        seen_pages.add(page_number)
    return parsed


def _source_contract(source: SourceDocument) -> tuple[int, str]:
    if source.is_demo:
        raise ImportContractError("Demo source documents cannot enter the NBS IGR pipeline")
    if "National Bureau of Statistics" not in source.source_organization:
        raise ImportContractError("Source document is not registered as NBS evidence")
    if source.mime_type != "application/pdf":
        raise ImportContractError("NBS IGR source document must be the archived report PDF")
    match = _VERSION_RE.fullmatch(source.document_version)
    if match is None:
        raise ImportContractError("NBS IGR source version must encode fiscal year and report ID")
    return int(match.group("year")), match.group("report_id")


def extract_nbs_igr_source(
    session: Session,
    *,
    source_document_id: uuid.UUID,
    text_reader: TextReader = _pdf_text,
) -> IgrExtractionResult:
    """Extract one archived NBS IGR report into unpublished annual review records."""

    source = session.get(SourceDocument, source_document_id)
    if source is None:
        raise ImportContractError("NBS IGR source document does not exist")
    fiscal_year, _report_id = _source_contract(source)
    if source.processing_status is not ProcessingStatus.REGISTERED:
        raise ImportContractError("NBS IGR source is not in registered processing state")
    if source.source_status is not SourceStatus.REGISTERED:
        raise ImportContractError("NBS IGR source is not in registered source state")
    if (
        session.scalar(
            select(StateIgrRecord.id).where(StateIgrRecord.source_document_id == source.id)
        )
        is not None
    ):
        raise ImportContractError("NBS IGR source has already been extracted")
    if (
        session.scalar(
            select(StateIgrRecord.id).where(
                StateIgrRecord.fiscal_year == fiscal_year,
                StateIgrRecord.period_type == IgrPeriodType.ANNUAL,
            )
        )
        is not None
    ):
        raise ImportContractError(
            "An annual IGR dataset already exists for this fiscal year; reconciliation is required"
        )

    path = Path(source.storage_path).expanduser().resolve(strict=True)
    if not path.is_file():
        raise ImportContractError(f"NBS IGR archive path is not a regular file: {path}")

    try:
        rows = parse_nbs_igr_text(text_reader(path), fiscal_year=fiscal_year)
        normalizer = StateNormalizer.from_session(session)
        expected_states = list(session.scalars(select(State).order_by(State.code)))
        expected_ids = {state.id for state in expected_states}
        seen_ids: set[uuid.UUID] = set()
        records: list[StateIgrRecord] = []
        total_amount = Decimal("0.00")
        for row in rows:
            try:
                match = normalizer.match(row.state_name)
            except StateNormalizationError as error:
                raise ImportContractError(
                    f"Unknown NBS IGR jurisdiction on page {row.source_page}: {row.state_name!r}"
                ) from error
            if match.state.id in seen_ids:
                raise ImportContractError(
                    f"Duplicate NBS IGR jurisdiction on page {row.source_page}: {row.state_name!r}"
                )
            records.append(
                StateIgrRecord(
                    state_id=match.state.id,
                    source_document_id=source.id,
                    fiscal_year=fiscal_year,
                    period_type=IgrPeriodType.ANNUAL,
                    quarter=None,
                    period_start=date(fiscal_year, 1, 1),
                    period_end=date(fiscal_year, 12, 31),
                    igr_amount=row.amount,
                    igr_amount_original=row.amount_original,
                    reported_unit=ReportedUnit.NAIRA,
                    publication_date=source.publication_date,
                    source_page=row.source_page,
                    source_table=(
                        f"NBS Internally Generated Revenue At State Level ({fiscal_year})"
                    ),
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
                "NBS IGR jurisdiction coverage failed after normalization: "
                f"records={len(records)}, missing={missing_codes}"
            )

        session.add_all(records)
        source.processing_status = ProcessingStatus.READY_FOR_REVIEW
        source.source_status = SourceStatus.READY_FOR_REVIEW
        session.commit()
    except Exception:
        session.rollback()
        raise

    return IgrExtractionResult(
        source_document_id=str(source.id),
        fiscal_year=fiscal_year,
        records_extracted=len(records),
        total_amount=total_amount.quantize(_CENT),
    )
