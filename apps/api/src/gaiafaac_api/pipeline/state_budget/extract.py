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

from gaiafaac_api.database.budget_models import BudgetMetric, StateBudgetRecord
from gaiafaac_api.database.enums import ProcessingStatus, SourceStatus, VerificationStatus
from gaiafaac_api.database.models import SourceDocument, State
from gaiafaac_api.pipeline.errors import ImportContractError

_VERSION_RE = re.compile(r"^approved-budget-(?P<state_code>[a-z]{2})-(?P<year>20\d{2})$")
_MONEY_TOKEN = r"(?:-|\d{1,3}(?:,\d{3})*\.\d{2})"
_APPROVED_COLUMN = 3


@dataclass(frozen=True)
class ParsedBudgetRow:
    metric: BudgetMetric
    amount: Decimal
    amount_original: str
    source_page: int
    source_table: str


@dataclass(frozen=True)
class BudgetExtractionResult:
    source_document_id: str
    state_code: str
    fiscal_year: int
    records_extracted: int
    total_expenditure: Decimal


BudgetParser = Callable[[list[tuple[int, str]], int], list[ParsedBudgetRow]]
TextReader = Callable[[Path], list[tuple[int, str]]]


@dataclass(frozen=True)
class BudgetExtractionAdapter:
    state_code: str
    mime_types: frozenset[str]
    extraction_method: str
    parser: BudgetParser


def _pdf_text(path: Path) -> list[tuple[int, str]]:
    import pdfplumber

    pages: list[tuple[int, str]] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            pages.append((page.page_number, page.extract_text() or ""))
    return pages


def _decimal(raw: str, *, metric: BudgetMetric) -> Decimal:
    if raw == "-":
        raise ImportContractError(f"Approved budget value is missing for {metric.value}")
    try:
        return Decimal(raw.replace(",", ""))
    except InvalidOperation as error:
        raise ImportContractError(
            f"Invalid approved budget value for {metric.value}: {raw!r}"
        ) from error


def _normalized(text: str) -> str:
    return " ".join(text.split())


_ZAMFARA_ROWS: tuple[tuple[BudgetMetric, str], ...] = (
    (BudgetMetric.RECURRENT_REVENUE, r"Recurrent Revenue"),
    (BudgetMetric.FAAC_REVENUE, r"11\s*-\s*GOVERNMENT SHARE OF FAAC"),
    (BudgetMetric.INDEPENDENT_REVENUE, r"12\s*-\s*INDEPENDENT REVENUE"),
    (BudgetMetric.RECURRENT_EXPENDITURE, r"Recurrent Expenditure"),
    (BudgetMetric.PERSONNEL_COST, r"21\s*-\s*PERSONNEL COST"),
    (BudgetMetric.OTHER_NON_DEBT_RECURRENT, r"Other Non Debt Recurrent"),
    (BudgetMetric.BUDGETED_DEBT_SERVICE, r"Debt Service"),
    (BudgetMetric.TRANSFER_TO_CAPITAL_ACCOUNT, r"Transfer to Capital Account"),
    (BudgetMetric.OTHER_RECEIPTS, r"Other Receipts"),
    (BudgetMetric.AID_AND_GRANTS, r"13\s*-\s*AID AND GRANTS"),
    (
        BudgetMetric.CAPITAL_DEVELOPMENT_FUND_RECEIPTS,
        r"14\s*-\s*CAPITAL DEVELOPMENT\s*FUND\s*\(CDF\) RECEIPTS",
    ),
    (
        BudgetMetric.CAPITAL_EXPENDITURE,
        r"23\s*-\s*CAPITAL EXPENDITURE\s*\(Capital Expenditure\)",
    ),
    (BudgetMetric.TOTAL_REVENUE, r"Total Revenue\s*\(including OB\)"),
    (BudgetMetric.TOTAL_EXPENDITURE, r"Total Expenditure"),
)


def _extract_row(text: str, metric: BudgetMetric, label_pattern: str) -> str:
    columns = r"\s+".join(f"(?P<c{index}>{_MONEY_TOKEN})" for index in range(5))
    pattern = re.compile(rf"{label_pattern}\s+{columns}", re.IGNORECASE)
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        raise ImportContractError(
            f"Expected exactly one Zamfara summary row for {metric.value}; found {len(matches)}"
        )
    return matches[0].group(f"c{_APPROVED_COLUMN}")


def _require_equal(actual: Decimal, expected: Decimal, *, label: str) -> None:
    if actual != expected:
        raise ImportContractError(
            f"Zamfara approved-budget reconciliation failed for {label}: "
            f"actual={actual}, expected={expected}"
        )


def _validate_zamfara_reconciliation(values: dict[BudgetMetric, Decimal]) -> None:
    _require_equal(
        values[BudgetMetric.RECURRENT_REVENUE],
        values[BudgetMetric.FAAC_REVENUE] + values[BudgetMetric.INDEPENDENT_REVENUE],
        label="recurrent revenue",
    )
    _require_equal(
        values[BudgetMetric.OTHER_RECEIPTS],
        values[BudgetMetric.AID_AND_GRANTS]
        + values[BudgetMetric.CAPITAL_DEVELOPMENT_FUND_RECEIPTS],
        label="other receipts",
    )
    _require_equal(
        values[BudgetMetric.TOTAL_REVENUE],
        values[BudgetMetric.RECURRENT_REVENUE] + values[BudgetMetric.OTHER_RECEIPTS],
        label="total revenue",
    )
    _require_equal(
        values[BudgetMetric.RECURRENT_EXPENDITURE],
        values[BudgetMetric.PERSONNEL_COST]
        + values[BudgetMetric.OTHER_NON_DEBT_RECURRENT]
        + values[BudgetMetric.BUDGETED_DEBT_SERVICE],
        label="recurrent expenditure",
    )
    _require_equal(
        values[BudgetMetric.CAPITAL_EXPENDITURE],
        values[BudgetMetric.TRANSFER_TO_CAPITAL_ACCOUNT] + values[BudgetMetric.OTHER_RECEIPTS],
        label="capital expenditure",
    )
    _require_equal(
        values[BudgetMetric.TOTAL_EXPENDITURE],
        values[BudgetMetric.RECURRENT_EXPENDITURE] + values[BudgetMetric.CAPITAL_EXPENDITURE],
        label="total expenditure",
    )
    _require_equal(
        values[BudgetMetric.TOTAL_REVENUE],
        values[BudgetMetric.TOTAL_EXPENDITURE],
        label="balanced approved budget",
    )


def parse_zamfara_budget_summary(
    pages: list[tuple[int, str]],
    fiscal_year: int,
) -> list[ParsedBudgetRow]:
    """Parse the deterministic approved-budget summary used by the Zamfara adapter."""

    title = f"Zamfara State Government {fiscal_year} Approved Budget Summary"
    matches = [(page, _normalized(text)) for page, text in pages if title in _normalized(text)]
    if len(matches) != 1:
        raise ImportContractError(
            f"Expected one Zamfara {fiscal_year} approved-budget summary page; found {len(matches)}"
        )
    page_number, text = matches[0]
    source_table = title
    rows: list[ParsedBudgetRow] = []
    values: dict[BudgetMetric, Decimal] = {}
    for metric, label_pattern in _ZAMFARA_ROWS:
        raw = _extract_row(text, metric, label_pattern)
        amount = _decimal(raw, metric=metric)
        values[metric] = amount
        rows.append(
            ParsedBudgetRow(
                metric=metric,
                amount=amount,
                amount_original=raw,
                source_page=page_number,
                source_table=source_table,
            )
        )
    _validate_zamfara_reconciliation(values)
    return rows


_ADAPTERS: dict[str, BudgetExtractionAdapter] = {
    "ZA": BudgetExtractionAdapter(
        state_code="ZA",
        mime_types=frozenset({"application/pdf"}),
        extraction_method="zamfara_approved_budget_pdf_summary_v1",
        parser=parse_zamfara_budget_summary,
    )
}


def _source_contract(source: SourceDocument) -> tuple[str, int]:
    if source.is_demo:
        raise ImportContractError("Demo source documents cannot enter the state-budget pipeline")
    match = _VERSION_RE.fullmatch(source.document_version or "")
    if match is None:
        raise ImportContractError(
            "State-budget source version must encode state code and fiscal year"
        )
    return match.group("state_code").upper(), int(match.group("year"))


def extract_state_budget_source(
    session: Session,
    *,
    source_document_id: uuid.UUID,
    text_reader: TextReader = _pdf_text,
) -> BudgetExtractionResult:
    """Extract a supported approved state budget into unpublished review records."""

    source = session.get(SourceDocument, source_document_id)
    if source is None:
        raise ImportContractError("State-budget source document does not exist")
    state_code, fiscal_year = _source_contract(source)
    adapter = _ADAPTERS.get(state_code)
    if adapter is None:
        raise ImportContractError(
            f"No deterministic approved-budget extraction adapter is registered for {state_code}"
        )
    if source.mime_type not in adapter.mime_types:
        raise ImportContractError(
            f"{state_code} approved-budget adapter does not support {source.mime_type!r}"
        )
    if source.processing_status is not ProcessingStatus.REGISTERED:
        raise ImportContractError("State-budget source is not in registered processing state")
    if source.source_status is not SourceStatus.REGISTERED:
        raise ImportContractError("State-budget source is not in registered source state")

    state = session.scalar(select(State).where(State.code == state_code))
    if state is None:
        raise ImportContractError(f"State-budget source references unknown state code {state_code}")
    if source.source_organization != f"{state.name} State Government":
        raise ImportContractError("State-budget source organization does not match the state")
    if (
        session.scalar(
            select(StateBudgetRecord.id).where(StateBudgetRecord.source_document_id == source.id)
        )
        is not None
    ):
        raise ImportContractError("State-budget source has already been extracted")
    if (
        session.scalar(
            select(StateBudgetRecord.id).where(
                StateBudgetRecord.state_id == state.id,
                StateBudgetRecord.fiscal_year == fiscal_year,
            )
        )
        is not None
    ):
        raise ImportContractError(
            "An approved budget dataset already exists for this state and fiscal year; "
            "reconciliation is required"
        )

    path = Path(source.storage_path).expanduser().resolve(strict=True)
    if not path.is_file():
        raise ImportContractError(f"State-budget archive path is not a regular file: {path}")
    checksum = hashlib.sha256(path.read_bytes()).hexdigest()
    if checksum != source.sha256:
        raise ImportContractError("State-budget archive failed SHA-256 integrity verification")

    try:
        rows = adapter.parser(text_reader(path), fiscal_year)
        records = [
            StateBudgetRecord(
                state_id=state.id,
                source_document_id=source.id,
                fiscal_year=fiscal_year,
                metric=row.metric,
                amount=row.amount,
                amount_original=row.amount_original,
                currency="NGN",
                source_page=row.source_page,
                source_table=row.source_table,
                extraction_method=adapter.extraction_method,
                verification_status=VerificationStatus.REQUIRES_REVIEW,
                is_demo=False,
                is_published=False,
            )
            for row in rows
        ]
        if len(records) != len(_ZAMFARA_ROWS):
            raise ImportContractError(
                "State-budget extraction did not produce the complete metric set"
            )
        session.add_all(records)
        source.processing_status = ProcessingStatus.READY_FOR_REVIEW
        source.source_status = SourceStatus.READY_FOR_REVIEW
        session.commit()
    except Exception:
        session.rollback()
        raise

    total_expenditure = next(
        record.amount for record in records if record.metric is BudgetMetric.TOTAL_EXPENDITURE
    )
    return BudgetExtractionResult(
        source_document_id=str(source.id),
        state_code=state_code,
        fiscal_year=fiscal_year,
        records_extracted=len(records),
        total_expenditure=total_expenditure,
    )
