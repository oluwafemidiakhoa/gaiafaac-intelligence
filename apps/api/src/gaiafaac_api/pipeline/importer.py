from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.enums import (
    ExtractionStatus,
    ProcessingStatus,
    SourceStatus,
    ValidationSeverity,
    VerificationStatus,
)
from gaiafaac_api.database.models import ExtractionRun, ReportingPeriod, StateAllocation
from gaiafaac_api.pipeline.errors import (
    ImportContractError,
    MonetaryParseError,
    StateNormalizationError,
)
from gaiafaac_api.pipeline.monetary import parse_money, parse_reported_unit
from gaiafaac_api.pipeline.states import StateNormalizer
from gaiafaac_api.pipeline.validation import Finding, validate_import
from gaiafaac_api.services.source_documents import register_source_document

MAX_IMPORT_BYTES = 10 * 1024 * 1024
REQUIRED_COLUMNS = {
    "state",
    "gross_total",
    "total_deductions",
    "net_allocation",
    "reported_unit",
}
DEMO_LABEL = "DEMO DATA - NOT REAL FAAC DATA"


@dataclass(frozen=True)
class ImportRequest:
    path: Path
    source_organization: str
    revenue_month: date
    reporting_label: str
    faac_meeting_date: date | None = None
    publication_date: date | None = None
    source_url: str | None = None
    document_version: str = "1"
    is_demo: bool = False
    reported_unit: str | None = None


@dataclass(frozen=True)
class ImportResult:
    run_id: str
    reporting_period_id: str
    source_document_id: str
    records_extracted: int
    finding_count: int
    blocking_finding_count: int


def _validate_path(path: Path) -> Path:
    resolved = path.expanduser().resolve(strict=True)
    if not resolved.is_file():
        raise ImportContractError(f"Import path is not a regular file: {resolved}")
    if resolved.suffix.casefold() != ".csv":
        raise ImportContractError("Milestone 3 controlled imports accept CSV files only")
    size = resolved.stat().st_size
    if size == 0:
        raise ImportContractError("Import file is empty")
    if size > MAX_IMPORT_BYTES:
        raise ImportContractError(
            f"Import exceeds the {MAX_IMPORT_BYTES}-byte controlled file-size limit"
        )
    return resolved


def _confidence(row: dict[str, str], row_number: int, findings: list[Finding]) -> Decimal | None:
    raw = (row.get("extraction_confidence") or "").strip()
    if not raw:
        return None
    try:
        value = Decimal(raw)
    except InvalidOperation:
        value = Decimal("-1")
    if not value.is_finite() or value < 0 or value > 1 or value.as_tuple().exponent < -4:
        findings.append(
            Finding(
                "IMPORT_INVALID_CONFIDENCE",
                ValidationSeverity.ERROR,
                "Extraction confidence must be a decimal from 0 through 1.",
                details={"row": row_number, "original_value": raw},
            )
        )
        return None
    return value


def _import_allocations_csv(session: Session, request: ImportRequest) -> ImportResult:
    """Atomically import reviewed allocation rows and persist validation findings."""
    path = _validate_path(request.path)
    if not request.source_organization.strip():
        raise ImportContractError("Source organization is required")
    if not request.reporting_label.strip():
        raise ImportContractError("Reporting label is required")
    if not request.document_version.strip():
        raise ImportContractError("Document version is required")
    if request.revenue_month.day != 1:
        raise ImportContractError("Revenue month must be the first day of its month")
    if request.is_demo and "DEMO DATA" not in request.reporting_label.upper():
        raise ImportContractError("Demo imports require DEMO DATA in the reporting label")

    source = register_source_document(
        session,
        path=path,
        source_organization=request.source_organization,
        publication_date=request.publication_date,
        mime_type="text/csv",
        source_url=request.source_url,
        document_version=request.document_version,
        source_status=SourceStatus.DEMO if request.is_demo else SourceStatus.PENDING,
        processing_status=ProcessingStatus.PROCESSING,
        is_demo=request.is_demo,
        commit=False,
    )
    if source.reporting_period_id is not None:
        raise ImportContractError(
            "This exact source document has already been attached to a reporting period"
        )
    existing_period = session.scalar(
        select(ReportingPeriod).where(
            ReportingPeriod.revenue_month == request.revenue_month,
            ReportingPeriod.reporting_label == request.reporting_label,
        )
    )
    if existing_period is not None:
        raise ImportContractError("Reporting period and label already exist")

    period = ReportingPeriod(
        revenue_month=request.revenue_month,
        faac_meeting_date=request.faac_meeting_date,
        publication_date=request.publication_date,
        reporting_label=request.reporting_label,
        source_status=SourceStatus.PENDING,
        verification_status=VerificationStatus.PENDING,
        is_demo=request.is_demo,
        is_published=False,
    )
    session.add(period)
    session.flush()
    source.reporting_period_id = period.id
    run = ExtractionRun(
        source_document_id=source.id,
        status=ExtractionStatus.RUNNING,
        extractor_name="controlled_csv_import",
        extractor_version="1",
        started_at=datetime.now(UTC),
        records_extracted=0,
        configuration={
            "required_columns": sorted(REQUIRED_COLUMNS),
            "is_demo": request.is_demo,
        },
    )
    session.add(run)
    session.flush()

    normalizer = StateNormalizer.from_session(session)
    findings: list[Finding] = []
    seen_state_ids = set()
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        header_list = reader.fieldnames or []
        headers = set(header_list)
        if len(header_list) != len(headers):
            raise ImportContractError("CSV contains duplicate column names")
        missing_columns = REQUIRED_COLUMNS - headers
        if missing_columns:
            raise ImportContractError(
                f"CSV is missing required columns: {', '.join(sorted(missing_columns))}"
            )
        if request.is_demo and "data_label" not in headers:
            raise ImportContractError("Demo imports require a data_label column")

        for row_number, row in enumerate(reader, start=2):
            if request.is_demo and row.get("data_label") != DEMO_LABEL:
                findings.append(
                    Finding(
                        "IMPORT_DEMO_LABEL_MISSING",
                        ValidationSeverity.CRITICAL,
                        "Demo row does not carry the required DEMO DATA label.",
                        details={"row": row_number},
                    )
                )
                continue
            submitted_state = row.get("state") or ""
            try:
                match = normalizer.match(submitted_state)
            except StateNormalizationError as error:
                findings.append(
                    Finding(
                        "IMPORT_INVALID_STATE_ALIAS",
                        ValidationSeverity.ERROR,
                        str(error),
                        details={"row": row_number, "submitted_state": submitted_state},
                    )
                )
                continue
            if match.state.id in seen_state_ids:
                findings.append(
                    Finding(
                        "IMPORT_DUPLICATE_STATE",
                        ValidationSeverity.ERROR,
                        "State appears more than once in the import.",
                        details={
                            "row": row_number,
                            "state_code": match.state.code,
                            "submitted_state": submitted_state,
                        },
                    )
                )
                continue
            try:
                unit = parse_reported_unit(row.get("reported_unit") or "")
            except MonetaryParseError as error:
                findings.append(
                    Finding(
                        "IMPORT_INVALID_MONETARY_UNIT",
                        ValidationSeverity.ERROR,
                        str(error),
                        details={"row": row_number, "state_code": match.state.code},
                    )
                )
                continue
            try:
                gross = parse_money(row.get("gross_total"), unit)
                deductions = parse_money(row.get("total_deductions"), unit)
                net = parse_money(row.get("net_allocation"), unit)
            except MonetaryParseError as error:
                findings.append(
                    Finding(
                        "IMPORT_INVALID_MONETARY_VALUE",
                        ValidationSeverity.ERROR,
                        str(error),
                        details={"row": row_number, "state_code": match.state.code},
                    )
                )
                continue
            allocation = StateAllocation(
                reporting_period_id=period.id,
                state_id=match.state.id,
                source_document_id=source.id,
                gross_total=gross.value,
                total_deductions=deductions.value,
                net_allocation=net.value,
                gross_total_original=gross.original_text,
                total_deductions_original=deductions.original_text,
                net_allocation_original=net.original_text,
                reported_unit=unit,
                verification_status=VerificationStatus.PENDING,
                extraction_confidence=_confidence(row, row_number, findings),
                is_demo=request.is_demo,
                is_published=False,
            )
            session.add(allocation)
            seen_state_ids.add(match.state.id)
            run.records_extracted += 1

    run.completed_at = datetime.now(UTC)
    session.flush()
    results = validate_import(session, run, initial_findings=findings)
    session.commit()
    blocking_count = sum(
        result.severity in {ValidationSeverity.ERROR, ValidationSeverity.CRITICAL}
        for result in results
    )
    return ImportResult(
        run_id=str(run.id),
        reporting_period_id=str(period.id),
        source_document_id=str(source.id),
        records_extracted=run.records_extracted,
        finding_count=len(results),
        blocking_finding_count=blocking_count,
    )


def import_allocations_csv(session: Session, request: ImportRequest) -> ImportResult:
    try:
        return _import_allocations_csv(session, request)
    except Exception:
        session.rollback()
        raise
