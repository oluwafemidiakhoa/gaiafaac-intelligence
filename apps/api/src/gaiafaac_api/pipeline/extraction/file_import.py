from __future__ import annotations

import mimetypes
from datetime import UTC, datetime
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
from gaiafaac_api.pipeline.extraction.base import AllocationAdapter, select_adapter
from gaiafaac_api.pipeline.extraction.csv_adapter import GenericCsvAdapter
from gaiafaac_api.pipeline.extraction.excel_adapter import GenericExcelAdapter
from gaiafaac_api.pipeline.extraction.oagf_pdf_adapter import OagfPdfAdapter
from gaiafaac_api.pipeline.importer import ImportRequest, ImportResult
from gaiafaac_api.pipeline.monetary import ParsedMoney, parse_money, parse_reported_unit
from gaiafaac_api.pipeline.states import StateNormalizer
from gaiafaac_api.pipeline.validation import Finding, validate_import
from gaiafaac_api.services.source_documents import register_source_document

MAX_IMPORT_BYTES = 30 * 1024 * 1024
_ALLOWED_SUFFIXES = {".csv", ".xlsx", ".xlsm", ".pdf"}
_BLOCKING = {ValidationSeverity.ERROR, ValidationSeverity.CRITICAL}


def _default_adapters() -> list[AllocationAdapter]:
    return [GenericCsvAdapter(), GenericExcelAdapter(), OagfPdfAdapter()]


def _validate_path(path: Path) -> Path:
    resolved = path.expanduser().resolve(strict=True)
    if not resolved.is_file():
        raise ImportContractError(f"Import path is not a regular file: {resolved}")
    if resolved.suffix.casefold() not in _ALLOWED_SUFFIXES:
        raise ImportContractError(
            f"Unsupported file type {resolved.suffix!r}; accepted: {sorted(_ALLOWED_SUFFIXES)}"
        )
    size = resolved.stat().st_size
    if size == 0:
        raise ImportContractError("Import file is empty")
    if size > MAX_IMPORT_BYTES:
        raise ImportContractError(f"Import exceeds the {MAX_IMPORT_BYTES}-byte limit")
    return resolved


def import_file(
    session: Session, request: ImportRequest, adapters: list[AllocationAdapter] | None = None
) -> ImportResult:
    """Import any supported source file (CSV/XLSX/OAGF PDF) through the governed pipeline."""
    try:
        return _import_file(session, request, adapters or _default_adapters())
    except Exception:
        session.rollback()
        raise


def _import_file(
    session: Session, request: ImportRequest, adapters: list[AllocationAdapter]
) -> ImportResult:
    path = _validate_path(request.path)
    if not request.source_organization.strip():
        raise ImportContractError("Source organization is required")
    if not request.reporting_label.strip():
        raise ImportContractError("Reporting label is required")
    if request.revenue_month.day != 1:
        raise ImportContractError("Revenue month must be the first day of its month")

    mime = (
        "application/pdf"
        if path.suffix.casefold() == ".pdf"
        else (mimetypes.guess_type(path.name)[0] or "application/octet-stream")
    )
    adapter = select_adapter(path, mime, adapters)
    table = adapter.extract(path)

    source = register_source_document(
        session,
        path=path,
        source_organization=request.source_organization,
        publication_date=request.publication_date,
        mime_type=mime,
        source_url=request.source_url,
        document_version=request.document_version,
        source_status=SourceStatus.DEMO if request.is_demo else SourceStatus.PENDING,
        processing_status=ProcessingStatus.PROCESSING,
        is_demo=request.is_demo,
        commit=False,
    )
    if source.reporting_period_id is not None:
        raise ImportContractError(
            "This exact source document is already attached to a reporting period"
        )
    if session.scalar(
        select(ReportingPeriod).where(
            ReportingPeriod.revenue_month == request.revenue_month,
            ReportingPeriod.reporting_label == request.reporting_label,
        )
    ):
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
        extractor_name=adapter.name,
        extractor_version="1",
        started_at=datetime.now(UTC),
        records_extracted=0,
        configuration={"adapter": adapter.name, "warnings": table.warnings},
    )
    session.add(run)
    session.flush()

    normalizer = StateNormalizer.from_session(session)
    findings: list[Finding] = []
    seen: set = set()
    default_unit = None
    if request.reported_unit:
        try:
            default_unit = parse_reported_unit(request.reported_unit)
        except MonetaryParseError as error:
            raise ImportContractError(str(error)) from error

    for row in table.rows:
        try:
            match = normalizer.match(row.submitted_state)
        except StateNormalizationError as error:
            findings.append(
                Finding(
                    "IMPORT_INVALID_STATE_ALIAS",
                    ValidationSeverity.ERROR,
                    str(error),
                    details={"submitted_state": row.submitted_state, "row": row.source_row},
                )
            )
            continue
        if match.state.id in seen:
            findings.append(
                Finding(
                    "IMPORT_DUPLICATE_STATE",
                    ValidationSeverity.ERROR,
                    "State appears more than once in the import.",
                    details={"state_code": match.state.code, "row": row.source_row},
                )
            )
            continue
        try:
            unit = parse_reported_unit(row.reported_unit) if row.reported_unit else default_unit
        except MonetaryParseError as error:
            findings.append(
                Finding(
                    "IMPORT_INVALID_MONETARY_UNIT",
                    ValidationSeverity.ERROR,
                    str(error),
                    details={"state_code": match.state.code, "row": row.source_row},
                )
            )
            continue
        if unit is None:
            findings.append(
                Finding(
                    "IMPORT_MISSING_UNIT",
                    ValidationSeverity.ERROR,
                    "No reported monetary unit; supply an explicit unit at import time.",
                    details={"state_code": match.state.code, "row": row.source_row},
                )
            )
            continue
        try:
            gross = parse_money(row.original_text("gross_total"), unit)
            net = parse_money(row.original_text("net_allocation"), unit)
            deductions_text = row.original_text("total_deductions")
            if deductions_text is not None:
                deductions = parse_money(deductions_text, unit)
            elif gross.value is not None and net.value is not None:
                derived = gross.value - net.value
                deductions = ParsedMoney(format(derived, "f"), derived, unit)
            else:
                deductions = ParsedMoney("", None, unit)
        except MonetaryParseError as error:
            findings.append(
                Finding(
                    "IMPORT_INVALID_MONETARY_VALUE",
                    ValidationSeverity.ERROR,
                    str(error),
                    details={"state_code": match.state.code, "row": row.source_row},
                )
            )
            continue
        session.add(
            StateAllocation(
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
                is_demo=request.is_demo,
                is_published=False,
            )
        )
        seen.add(match.state.id)
        run.records_extracted += 1

    if table.requires_review:
        findings.append(
            Finding(
                "IMPORT_ADAPTER_REQUIRES_REVIEW",
                ValidationSeverity.WARNING,
                "; ".join(table.warnings) or "Adapter flagged output for human review.",
            )
        )

    run.completed_at = datetime.now(UTC)
    session.flush()
    results = validate_import(session, run, initial_findings=findings)
    session.commit()
    blocking = sum(result.severity in _BLOCKING for result in results)
    return ImportResult(
        run_id=str(run.id),
        reporting_period_id=str(period.id),
        source_document_id=str(source.id),
        records_extracted=run.records_extracted,
        finding_count=len(results),
        blocking_finding_count=blocking,
    )
