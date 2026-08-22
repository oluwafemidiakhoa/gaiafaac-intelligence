from __future__ import annotations

import hashlib
import re
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.enums import ProcessingStatus, SourceStatus, VerificationStatus
from gaiafaac_api.database.liability_models import LiabilityMetric, StateLiabilityRecord
from gaiafaac_api.database.models import SourceDocument, State
from gaiafaac_api.pipeline.errors import ImportContractError

_VERSION_RE = re.compile(
    r"^state-financial-(?P<kind>audited-financial-statement|contractor-arrears-register)-"
    r"(?P<state_code>[a-z]{2})-(?P<year>20\d{2})$"
)
_MONEY_TOKEN = r"(?:-|\d{1,3}(?:,\d{3})*\.\d{2})"
_SOURCE_TABLE = "Oyo State 2021 Contractor and Domestic Arrears Summary"
_EXTRACTION_METHOD = "oyo_contractor_arrears_pdf_summary_v1"


@dataclass(frozen=True)
class ParsedLiabilityRow:
    metric: LiabilityMetric
    amount: Decimal | None
    amount_text: str
    source_page: int
    source_table: str


@dataclass(frozen=True)
class StateLiabilityExtractionResult:
    source_document_id: str
    state_code: str
    fiscal_year: int
    records_extracted: int
    total_domestic_arrears: Decimal


TextReader = Callable[[Path], list[tuple[int, str]]]


def _pdf_text(path: Path) -> list[tuple[int, str]]:
    import pdfplumber

    pages: list[tuple[int, str]] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            pages.append((page.page_number, page.extract_text() or ""))
    return pages


def _normalize(value: str) -> str:
    return " ".join(value.split())


def _money(raw: str, *, metric: LiabilityMetric) -> Decimal | None:
    normalized = _normalize(raw)
    if normalized == "-":
        return None
    try:
        value = Decimal(normalized.replace(",", ""))
    except InvalidOperation as error:
        raise ImportContractError(
            f"Invalid liability amount for {metric.value}: {raw!r}"
        ) from error
    if value < 0:
        raise ImportContractError(f"Negative liability amount for {metric.value}: {value}")
    return value


_OYO_2021_ROWS: tuple[tuple[LiabilityMetric, str], ...] = (
    (LiabilityMetric.CONTRACTOR_ARREARS, r"TOTAL CONTRACTOR"),
    (LiabilityMetric.PENSIONS_AND_GRATUITY_ARREARS, r"TOTAL PENSIONS AND GRATUITY"),
    (LiabilityMetric.SALARY_ARREARS, r"SALARY ARREARS"),
    (LiabilityMetric.OTHER_JUDGMENT_ARREARS, r"OTHER JUDGE?MENT ARREARS"),
    (LiabilityMetric.TOTAL_DOMESTIC_ARREARS, r"TOTAL DOMESTIC ARREARS"),
)


def _parse_summary_row(
    lines: list[str],
    *,
    metric: LiabilityMetric,
    label_pattern: str,
    source_page: int,
) -> ParsedLiabilityRow:
    pattern = re.compile(
        rf"^{label_pattern}\s+(?P<amount>{_MONEY_TOKEN})$",
        re.IGNORECASE,
    )
    matches = [match for line in lines if (match := pattern.fullmatch(line)) is not None]
    if len(matches) != 1:
        raise ImportContractError(
            f"Expected exactly one Oyo liability summary row for {metric.value}; "
            f"found {len(matches)}"
        )
    amount_text = matches[0].group("amount")
    return ParsedLiabilityRow(
        metric=metric,
        amount=_money(amount_text, metric=metric),
        amount_text=amount_text,
        source_page=source_page,
        source_table=_SOURCE_TABLE,
    )


def parse_oyo_2021_contractor_arrears_summary(
    pages: list[tuple[int, str]],
) -> list[ParsedLiabilityRow]:
    """Parse the five explicit summary rows without interpreting a source dash as zero."""

    labels = tuple(label for _, label in _OYO_2021_ROWS)
    candidates: list[tuple[int, str]] = []
    for page_number, text in pages:
        normalized = _normalize(text)
        if all(re.search(label, normalized, re.IGNORECASE) for label in labels):
            candidates.append((page_number, text))
    if len(candidates) != 1:
        raise ImportContractError(
            "Expected exactly one Oyo 2021 contractor-arrears summary page; "
            f"found {len(candidates)}"
        )

    page_number, text = candidates[0]
    lines = [_normalize(line) for line in text.splitlines() if line.strip()]
    rows = [
        _parse_summary_row(
            lines,
            metric=metric,
            label_pattern=label_pattern,
            source_page=page_number,
        )
        for metric, label_pattern in _OYO_2021_ROWS
    ]
    by_metric = {row.metric: row for row in rows}
    if len(by_metric) != len(LiabilityMetric):
        raise ImportContractError("Oyo liability summary did not produce the complete metric set")

    salary = by_metric[LiabilityMetric.SALARY_ARREARS]
    if salary.amount is not None or _normalize(salary.amount_text) != "-":
        raise ImportContractError(
            "Oyo 2021 salary arrears must remain unreported when the official source uses a dash"
        )

    contractor = by_metric[LiabilityMetric.CONTRACTOR_ARREARS].amount
    pensions = by_metric[LiabilityMetric.PENSIONS_AND_GRATUITY_ARREARS].amount
    judgment = by_metric[LiabilityMetric.OTHER_JUDGMENT_ARREARS].amount
    total = by_metric[LiabilityMetric.TOTAL_DOMESTIC_ARREARS].amount
    if contractor is None or pensions is None or judgment is None or total is None:
        raise ImportContractError("Oyo 2021 liability reconciliation requires all reported totals")
    expected_total = contractor + pensions + judgment
    if total != expected_total:
        raise ImportContractError(
            "Oyo liability reconciliation failed for total domestic arrears: "
            f"actual={total}, expected={expected_total}"
        )
    return rows


def _source_contract(source: SourceDocument) -> tuple[str, str, int]:
    if source.is_demo:
        raise ImportContractError("Demo source documents cannot enter the liability pipeline")
    match = _VERSION_RE.fullmatch(source.document_version or "")
    if match is None:
        raise ImportContractError(
            "State-financial source version must encode evidence kind, state, and fiscal year"
        )
    return (
        match.group("kind"),
        match.group("state_code").upper(),
        int(match.group("year")),
    )


def extract_state_liability_source(
    session: Session,
    *,
    source_document_id: uuid.UUID,
    text_reader: TextReader = _pdf_text,
) -> StateLiabilityExtractionResult:
    """Extract the supported official Oyo arrears register into unpublished review records."""

    source = session.get(SourceDocument, source_document_id)
    if source is None:
        raise ImportContractError("State-financial source document does not exist")
    evidence_kind, state_code, fiscal_year = _source_contract(source)
    if (evidence_kind, state_code, fiscal_year) != (
        "contractor-arrears-register",
        "OY",
        2021,
    ):
        raise ImportContractError(
            "No deterministic liability extraction adapter is registered for "
            f"{evidence_kind}/{state_code}/{fiscal_year}"
        )
    if source.mime_type != "application/pdf":
        raise ImportContractError("Oyo 2021 contractor-arrears extraction requires a PDF source")
    if source.processing_status is not ProcessingStatus.REGISTERED:
        raise ImportContractError("State-financial source is not in registered processing state")
    if source.source_status is not SourceStatus.REGISTERED:
        raise ImportContractError("State-financial source is not in registered source state")

    state = session.scalar(select(State).where(State.code == state_code))
    if state is None:
        raise ImportContractError(
            f"State-financial source references unknown state code {state_code}"
        )
    if source.source_organization != f"{state.name} State Government":
        raise ImportContractError(
            "State-financial source organization does not match the staged state"
        )
    if (
        session.scalar(
            select(StateLiabilityRecord.id).where(
                StateLiabilityRecord.source_document_id == source.id
            )
        )
        is not None
    ):
        raise ImportContractError("State-financial liability source has already been extracted")

    path = Path(source.storage_path).expanduser().resolve(strict=True)
    if not path.is_file():
        raise ImportContractError(f"State-financial archive path is not a regular file: {path}")
    checksum = hashlib.sha256(path.read_bytes()).hexdigest()
    if checksum != source.sha256:
        raise ImportContractError("State-financial archive failed SHA-256 integrity verification")

    try:
        rows = parse_oyo_2021_contractor_arrears_summary(text_reader(path))
        records = [
            StateLiabilityRecord(
                state_id=state.id,
                source_document_id=source.id,
                fiscal_year=fiscal_year,
                metric=row.metric,
                amount=row.amount,
                amount_text=row.amount_text,
                currency="NGN",
                source_page=row.source_page,
                source_table=row.source_table,
                extraction_method=_EXTRACTION_METHOD,
                verification_status=VerificationStatus.REQUIRES_REVIEW,
                is_demo=False,
                is_published=False,
            )
            for row in rows
        ]
        if len(records) != len(LiabilityMetric):
            raise ImportContractError(
                "Liability extraction did not produce the complete metric set"
            )
        session.add_all(records)
        source.processing_status = ProcessingStatus.READY_FOR_REVIEW
        source.source_status = SourceStatus.READY_FOR_REVIEW
        session.commit()
    except Exception:
        session.rollback()
        raise

    total = next(
        record.amount
        for record in records
        if record.metric is LiabilityMetric.TOTAL_DOMESTIC_ARREARS
    )
    if total is None:
        raise ImportContractError("Oyo total domestic arrears must be numerically reported")
    return StateLiabilityExtractionResult(
        source_document_id=str(source.id),
        state_code=state_code,
        fiscal_year=fiscal_year,
        records_extracted=len(records),
        total_domestic_arrears=total,
    )
