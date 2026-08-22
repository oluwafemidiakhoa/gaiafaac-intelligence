from __future__ import annotations

import hashlib
import re
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.budget_models import (
    BudgetPerformanceMetric,
    StateBudgetPerformanceRecord,
)
from gaiafaac_api.database.enums import ProcessingStatus, SourceStatus, VerificationStatus
from gaiafaac_api.database.models import SourceDocument, State
from gaiafaac_api.pipeline.errors import ImportContractError

_VERSION_RE = re.compile(
    r"^budget-performance-(?P<state_code>[a-z]{2})-(?P<year>20\d{2})-q(?P<quarter>[1-4])$"
)
_MONEY_TOKEN = r"(?:-|(?:-\s*)?\d{1,3}(?:,\d{3})*\.\d{2})"
_PERCENT_TOKEN = r"(?:-|\d+(?:\.\d+)?%)"
_PERCENT_TENTH = Decimal("0.1")


@dataclass(frozen=True)
class ParsedPerformanceRow:
    metric: BudgetPerformanceMetric
    original_budget: Decimal
    original_budget_text: str
    quarter_actual: Decimal | None
    quarter_actual_text: str
    ytd_actual: Decimal | None
    ytd_actual_text: str
    performance_percent: Decimal | None
    performance_percent_text: str
    balance: Decimal | None
    balance_text: str
    source_page: int
    source_table: str


@dataclass(frozen=True)
class BudgetPerformanceExtractionResult:
    source_document_id: str
    state_code: str
    fiscal_year: int
    quarter: int
    records_extracted: int
    total_revenue_ytd: Decimal
    total_expenditure_ytd: Decimal


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


def _money(
    raw: str,
    *,
    metric: BudgetPerformanceMetric,
    field: str,
    allow_missing: bool,
    allow_negative: bool = False,
) -> Decimal | None:
    normalized = _normalize(raw)
    if normalized == "-":
        if allow_missing:
            return None
        raise ImportContractError(f"Missing {field} for {metric.value}")
    try:
        value = Decimal(normalized.replace(",", "").replace(" ", ""))
    except InvalidOperation as error:
        raise ImportContractError(f"Invalid {field} for {metric.value}: {raw!r}") from error
    if not allow_negative and value < 0:
        raise ImportContractError(f"Negative {field} for {metric.value}: {value}")
    return value


def _percent(raw: str, *, metric: BudgetPerformanceMetric) -> Decimal | None:
    normalized = _normalize(raw)
    if normalized == "-":
        return None
    try:
        value = Decimal(normalized.removesuffix("%"))
    except InvalidOperation as error:
        raise ImportContractError(
            f"Invalid performance percent for {metric.value}: {raw!r}"
        ) from error
    if value < 0:
        raise ImportContractError(f"Negative performance percent for {metric.value}: {value}")
    return value


_OYO_ROWS: tuple[tuple[BudgetPerformanceMetric, str], ...] = (
    (BudgetPerformanceMetric.OPENING_BALANCE, r"Opening Balance"),
    (BudgetPerformanceMetric.RECURRENT_REVENUE, r"Recurrent Revenue"),
    (
        BudgetPerformanceMetric.FAAC_REVENUE,
        r"11\s*-\s*GOVERNMENT SHARE OF FAAC\s*\(STATUTORY REVENUE\)",
    ),
    (BudgetPerformanceMetric.INDEPENDENT_REVENUE, r"12\s*-\s*INDEPENDENT REVENUE"),
    (BudgetPerformanceMetric.RECURRENT_EXPENDITURE, r"Recurrent Expenditure"),
    (
        BudgetPerformanceMetric.PERSONNEL_COST,
        r"21\s*-\s*PERSONNEL COST\s*\(INCLUDING 2201 WHERE APPROPRIATE\)",
    ),
    (
        BudgetPerformanceMetric.OTHER_RECURRENT_COSTS,
        r"22\s*-\s*OTHER RECURRENT COSTS\s*\(EXCLUDING 2201\)",
    ),
    (BudgetPerformanceMetric.OVERHEAD_COST, r"2202\s*-\s*OVERHEAD COST"),
    (BudgetPerformanceMetric.OTHER_RECURRENT, r"OTHER RECURRENT\s*\(2203-2209\)"),
    (
        BudgetPerformanceMetric.TRANSFER_TO_CAPITAL_ACCOUNT,
        r"Transfer to Capital Account",
    ),
    (BudgetPerformanceMetric.OTHER_RECEIPTS, r"Other Receipts"),
    (BudgetPerformanceMetric.AID_AND_GRANTS, r"13\s*-\s*AID AND GRANTS"),
    (
        BudgetPerformanceMetric.CAPITAL_DEVELOPMENT_FUND_RECEIPTS,
        r"14\s*-\s*CAPITAL DEVELOPMENT\s*FUND\s*\(CDF\) RECEIPTS",
    ),
    (BudgetPerformanceMetric.CAPITAL_EXPENDITURE, r"Capital Expenditure"),
    (BudgetPerformanceMetric.TOTAL_REVENUE, r"Total Revenue\s*\(including OB\)"),
    (BudgetPerformanceMetric.TOTAL_EXPENDITURE, r"Total Expenditure"),
)


def _parse_row(
    lines: list[str],
    *,
    metric: BudgetPerformanceMetric,
    label_pattern: str,
    source_page: int,
    source_table: str,
) -> ParsedPerformanceRow:
    pattern = re.compile(
        rf"^{label_pattern}\s+"
        rf"(?P<original>{_MONEY_TOKEN})\s+"
        rf"(?P<quarter>{_MONEY_TOKEN})\s+"
        rf"(?P<ytd>{_MONEY_TOKEN})\s+"
        rf"(?P<percent>{_PERCENT_TOKEN})\s+"
        rf"(?P<balance>{_MONEY_TOKEN})$",
        re.IGNORECASE,
    )
    matches = [match for line in lines if (match := pattern.fullmatch(line)) is not None]
    if len(matches) != 1:
        raise ImportContractError(
            f"Expected exactly one Oyo Table 1 row for {metric.value}; found {len(matches)}"
        )
    match = matches[0]
    original_text = match.group("original")
    quarter_text = match.group("quarter")
    ytd_text = match.group("ytd")
    percent_text = match.group("percent")
    balance_text = match.group("balance")
    original = _money(
        original_text,
        metric=metric,
        field="original budget",
        allow_missing=False,
    )
    assert original is not None
    return ParsedPerformanceRow(
        metric=metric,
        original_budget=original,
        original_budget_text=original_text,
        quarter_actual=_money(
            quarter_text,
            metric=metric,
            field="quarter actual",
            allow_missing=True,
        ),
        quarter_actual_text=quarter_text,
        ytd_actual=_money(
            ytd_text,
            metric=metric,
            field="YTD actual",
            allow_missing=True,
        ),
        ytd_actual_text=ytd_text,
        performance_percent=_percent(percent_text, metric=metric),
        performance_percent_text=percent_text,
        balance=_money(
            balance_text,
            metric=metric,
            field="balance",
            allow_missing=True,
            allow_negative=True,
        ),
        balance_text=balance_text,
        source_page=source_page,
        source_table=source_table,
    )


def _require_equal(actual: Decimal, expected: Decimal, *, label: str) -> None:
    if actual != expected:
        raise ImportContractError(
            f"Oyo budget-performance reconciliation failed for {label}: "
            f"actual={actual}, expected={expected}"
        )


def _value(
    rows: dict[BudgetPerformanceMetric, ParsedPerformanceRow],
    metric: BudgetPerformanceMetric,
    field: str,
) -> Decimal:
    value = getattr(rows[metric], field)
    if value is None:
        raise ImportContractError(f"Missing {field} required to reconcile {metric.value}")
    return value


def _validate_original_budget(rows: dict[BudgetPerformanceMetric, ParsedPerformanceRow]) -> None:
    original = lambda metric: _value(rows, metric, "original_budget")
    _require_equal(
        original(BudgetPerformanceMetric.RECURRENT_REVENUE),
        original(BudgetPerformanceMetric.FAAC_REVENUE)
        + original(BudgetPerformanceMetric.INDEPENDENT_REVENUE),
        label="original recurrent revenue",
    )
    _require_equal(
        original(BudgetPerformanceMetric.OTHER_RECURRENT_COSTS),
        original(BudgetPerformanceMetric.OVERHEAD_COST)
        + original(BudgetPerformanceMetric.OTHER_RECURRENT),
        label="original other recurrent costs",
    )
    _require_equal(
        original(BudgetPerformanceMetric.RECURRENT_EXPENDITURE),
        original(BudgetPerformanceMetric.PERSONNEL_COST)
        + original(BudgetPerformanceMetric.OTHER_RECURRENT_COSTS),
        label="original recurrent expenditure",
    )
    _require_equal(
        original(BudgetPerformanceMetric.OTHER_RECEIPTS),
        original(BudgetPerformanceMetric.AID_AND_GRANTS)
        + original(BudgetPerformanceMetric.CAPITAL_DEVELOPMENT_FUND_RECEIPTS),
        label="original other receipts",
    )
    _require_equal(
        original(BudgetPerformanceMetric.CAPITAL_EXPENDITURE),
        original(BudgetPerformanceMetric.TRANSFER_TO_CAPITAL_ACCOUNT)
        + original(BudgetPerformanceMetric.OTHER_RECEIPTS),
        label="original capital expenditure",
    )
    _require_equal(
        original(BudgetPerformanceMetric.TOTAL_REVENUE),
        original(BudgetPerformanceMetric.OPENING_BALANCE)
        + original(BudgetPerformanceMetric.RECURRENT_REVENUE)
        + original(BudgetPerformanceMetric.OTHER_RECEIPTS),
        label="original total revenue",
    )
    _require_equal(
        original(BudgetPerformanceMetric.TOTAL_EXPENDITURE),
        original(BudgetPerformanceMetric.RECURRENT_EXPENDITURE)
        + original(BudgetPerformanceMetric.CAPITAL_EXPENDITURE),
        label="original total expenditure",
    )


def _validate_actual_column(
    rows: dict[BudgetPerformanceMetric, ParsedPerformanceRow],
    *,
    field: str,
    label_prefix: str,
) -> None:
    actual = lambda metric: _value(rows, metric, field)
    _require_equal(
        actual(BudgetPerformanceMetric.RECURRENT_REVENUE),
        actual(BudgetPerformanceMetric.FAAC_REVENUE)
        + actual(BudgetPerformanceMetric.INDEPENDENT_REVENUE),
        label=f"{label_prefix} recurrent revenue",
    )
    _require_equal(
        actual(BudgetPerformanceMetric.OTHER_RECURRENT_COSTS),
        actual(BudgetPerformanceMetric.OVERHEAD_COST)
        + actual(BudgetPerformanceMetric.OTHER_RECURRENT),
        label=f"{label_prefix} other recurrent costs",
    )
    _require_equal(
        actual(BudgetPerformanceMetric.RECURRENT_EXPENDITURE),
        actual(BudgetPerformanceMetric.PERSONNEL_COST)
        + actual(BudgetPerformanceMetric.OTHER_RECURRENT_COSTS),
        label=f"{label_prefix} recurrent expenditure",
    )
    _require_equal(
        actual(BudgetPerformanceMetric.OTHER_RECEIPTS),
        actual(BudgetPerformanceMetric.AID_AND_GRANTS)
        + actual(BudgetPerformanceMetric.CAPITAL_DEVELOPMENT_FUND_RECEIPTS),
        label=f"{label_prefix} other receipts",
    )
    _require_equal(
        actual(BudgetPerformanceMetric.TOTAL_EXPENDITURE),
        actual(BudgetPerformanceMetric.RECURRENT_EXPENDITURE)
        + actual(BudgetPerformanceMetric.CAPITAL_EXPENDITURE),
        label=f"{label_prefix} total expenditure",
    )

    opening = rows[BudgetPerformanceMetric.OPENING_BALANCE]
    opening_value = getattr(opening, field)
    expected_revenue = actual(BudgetPerformanceMetric.RECURRENT_REVENUE) + actual(
        BudgetPerformanceMetric.OTHER_RECEIPTS
    )
    if opening_value is not None:
        expected_revenue += opening_value
    _require_equal(
        actual(BudgetPerformanceMetric.TOTAL_REVENUE),
        expected_revenue,
        label=f"{label_prefix} total revenue",
    )


def _validate_balances_and_percentages(
    rows: dict[BudgetPerformanceMetric, ParsedPerformanceRow],
) -> None:
    for metric, row in rows.items():
        if row.balance is not None and row.ytd_actual is not None:
            _require_equal(
                row.balance,
                row.original_budget - row.ytd_actual,
                label=f"{metric.value} balance",
            )
        if row.performance_percent is not None and row.original_budget != 0:
            if row.ytd_actual is None:
                raise ImportContractError(
                    f"Missing YTD actual required for {metric.value} performance percent"
                )
            expected = (row.ytd_actual / row.original_budget * Decimal("100")).quantize(
                _PERCENT_TENTH, rounding=ROUND_HALF_UP
            )
            _require_equal(
                row.performance_percent,
                expected,
                label=f"{metric.value} performance percent",
            )


def parse_oyo_budget_performance_table1(
    pages: list[tuple[int, str]],
    fiscal_year: int,
    quarter: int,
) -> list[ParsedPerformanceRow]:
    """Parse Oyo Table 1 without inferring missing values from dashes."""

    title = f"Oyo State Government {fiscal_year} Q{quarter} Budget Performance Report - Summary"
    candidates: list[tuple[int, str]] = []
    for page_number, text in pages:
        normalized = _normalize(text)
        if "Table 1: Budget Implementation Summary" in normalized and title in normalized:
            candidates.append((page_number, text))
    if len(candidates) != 1:
        raise ImportContractError(
            f"Expected one Oyo {fiscal_year} Q{quarter} Table 1 summary page; "
            f"found {len(candidates)}"
        )

    page_number, text = candidates[0]
    lines = [_normalize(line) for line in text.splitlines() if line.strip()]
    rows = [
        _parse_row(
            lines,
            metric=metric,
            label_pattern=label_pattern,
            source_page=page_number,
            source_table="Table 1: Budget Implementation Summary",
        )
        for metric, label_pattern in _OYO_ROWS
    ]
    by_metric = {row.metric: row for row in rows}
    if len(by_metric) != len(_OYO_ROWS):
        raise ImportContractError("Oyo Table 1 did not produce the complete governed metric set")

    _validate_original_budget(by_metric)
    _validate_actual_column(by_metric, field="quarter_actual", label_prefix="quarter")
    _validate_actual_column(by_metric, field="ytd_actual", label_prefix="YTD")
    _validate_balances_and_percentages(by_metric)
    return rows


def _source_contract(source: SourceDocument) -> tuple[str, int, int]:
    if source.is_demo:
        raise ImportContractError(
            "Demo source documents cannot enter the budget-performance pipeline"
        )
    match = _VERSION_RE.fullmatch(source.document_version or "")
    if match is None:
        raise ImportContractError(
            "Budget-performance source version must encode state, fiscal year, and quarter"
        )
    return (
        match.group("state_code").upper(),
        int(match.group("year")),
        int(match.group("quarter")),
    )


def extract_budget_performance_source(
    session: Session,
    *,
    source_document_id: uuid.UUID,
    text_reader: TextReader = _pdf_text,
) -> BudgetPerformanceExtractionResult:
    """Extract one supported quarterly report into unpublished performance records."""

    source = session.get(SourceDocument, source_document_id)
    if source is None:
        raise ImportContractError("Budget-performance source document does not exist")
    state_code, fiscal_year, quarter = _source_contract(source)
    if state_code != "OY":
        raise ImportContractError(
            f"No deterministic budget-performance extraction adapter is registered for {state_code}"
        )
    if source.mime_type != "application/pdf":
        raise ImportContractError(
            "Oyo budget-performance extraction currently requires a PDF source"
        )
    if source.processing_status is not ProcessingStatus.REGISTERED:
        raise ImportContractError("Budget-performance source is not in registered processing state")
    if source.source_status is not SourceStatus.REGISTERED:
        raise ImportContractError("Budget-performance source is not in registered source state")

    state = session.scalar(select(State).where(State.code == state_code))
    if state is None:
        raise ImportContractError(
            f"Budget-performance source references unknown state code {state_code}"
        )
    if source.source_organization != f"{state.name} State Government":
        raise ImportContractError(
            "Budget-performance source organization does not match the staged state"
        )
    if (
        session.scalar(
            select(StateBudgetPerformanceRecord.id).where(
                StateBudgetPerformanceRecord.source_document_id == source.id
            )
        )
        is not None
    ):
        raise ImportContractError("Budget-performance source has already been extracted")
    if (
        session.scalar(
            select(StateBudgetPerformanceRecord.id).where(
                StateBudgetPerformanceRecord.state_id == state.id,
                StateBudgetPerformanceRecord.fiscal_year == fiscal_year,
                StateBudgetPerformanceRecord.quarter == quarter,
            )
        )
        is not None
    ):
        raise ImportContractError(
            "A budget-performance dataset already exists for this state, year, and quarter; "
            "reconciliation is required"
        )

    path = Path(source.storage_path).expanduser().resolve(strict=True)
    if not path.is_file():
        raise ImportContractError(f"Budget-performance archive path is not a regular file: {path}")
    checksum = hashlib.sha256(path.read_bytes()).hexdigest()
    if checksum != source.sha256:
        raise ImportContractError(
            "Budget-performance archive failed SHA-256 integrity verification"
        )

    try:
        rows = parse_oyo_budget_performance_table1(
            text_reader(path),
            fiscal_year,
            quarter,
        )
        records = [
            StateBudgetPerformanceRecord(
                state_id=state.id,
                source_document_id=source.id,
                fiscal_year=fiscal_year,
                quarter=quarter,
                metric=row.metric,
                original_budget=row.original_budget,
                original_budget_text=row.original_budget_text,
                quarter_actual=row.quarter_actual,
                quarter_actual_text=row.quarter_actual_text,
                ytd_actual=row.ytd_actual,
                ytd_actual_text=row.ytd_actual_text,
                performance_percent=row.performance_percent,
                performance_percent_text=row.performance_percent_text,
                balance=row.balance,
                balance_text=row.balance_text,
                currency="NGN",
                source_page=row.source_page,
                source_table=row.source_table,
                extraction_method="oyo_budget_performance_pdf_table1_v1",
                verification_status=VerificationStatus.REQUIRES_REVIEW,
                is_demo=False,
                is_published=False,
            )
            for row in rows
        ]
        if len(records) != len(BudgetPerformanceMetric):
            raise ImportContractError(
                "Budget-performance extraction did not produce the complete metric set"
            )
        session.add_all(records)
        source.processing_status = ProcessingStatus.READY_FOR_REVIEW
        source.source_status = SourceStatus.READY_FOR_REVIEW
        session.commit()
    except Exception:
        session.rollback()
        raise

    total_revenue = next(
        record.ytd_actual
        for record in records
        if record.metric is BudgetPerformanceMetric.TOTAL_REVENUE
    )
    total_expenditure = next(
        record.ytd_actual
        for record in records
        if record.metric is BudgetPerformanceMetric.TOTAL_EXPENDITURE
    )
    if total_revenue is None or total_expenditure is None:
        raise ImportContractError("Oyo Table 1 totals must include YTD actual values")
    return BudgetPerformanceExtractionResult(
        source_document_id=str(source.id),
        state_code=state_code,
        fiscal_year=fiscal_year,
        quarter=quarter,
        records_extracted=len(records),
        total_revenue_ytd=total_revenue,
        total_expenditure_ytd=total_expenditure,
    )
