from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from gaiafaac_api.database.enums import (
    ExtractionStatus,
    ProcessingStatus,
    ReportedUnit,
    SourceStatus,
    UserRole,
    ValidationSeverity,
    VerificationStatus,
)
from gaiafaac_api.database.models import (
    AuditLog,
    ExtractionRun,
    NationalDistribution,
    ReportingPeriod,
    SourceDocument,
    StateAllocation,
    User,
    ValidationResult,
)
from gaiafaac_api.pipeline.errors import ApprovalError, ImportContractError, MonetaryParseError
from gaiafaac_api.pipeline.monetary import ParsedMoney, parse_money, parse_reported_unit
from gaiafaac_api.pipeline.validation import Finding
from gaiafaac_api.services.source_documents import register_source_document

DERIVATION_TREATMENTS = {"separate", "included_in_states", "not_reported"}
STATES_SCOPES = {"states_only_36", "states_plus_fct_37"}
_BLOCKING = {ValidationSeverity.ERROR, ValidationSeverity.CRITICAL}
_UNIT_QUANTA = {
    ReportedUnit.NAIRA: Decimal("1"),
    ReportedUnit.THOUSAND_NAIRA: Decimal("1000"),
    ReportedUnit.MILLION_NAIRA: Decimal("1000000"),
    ReportedUnit.BILLION_NAIRA: Decimal("1000000000"),
}


@dataclass(frozen=True)
class NationalDistributionImportRequest:
    path: Path
    reporting_period_id: uuid.UUID
    source_organization: str
    reported_unit: str
    net_distributable_amount: str
    federal_amount: str
    states_amount: str
    local_governments_amount: str
    derivation_amount: str | None = None
    derivation_treatment: str = "separate"
    gross_amount: str | None = None
    deductions_amount: str | None = None
    vat_amount: str | None = None
    statutory_amount: str | None = None
    publication_date: date | None = None
    source_url: str | None = None
    document_version: str = "1"


@dataclass(frozen=True)
class NationalDistributionResult:
    distribution_id: str
    run_id: str
    reporting_period_id: str
    finding_count: int
    blocking_finding_count: int
    published: bool


@dataclass(frozen=True)
class ComponentReconciliation:
    status: str
    component_total: Decimal | None
    variance: Decimal | None
    tolerance: Decimal | None
    derivation_treatment: str
    note: str


def _required_money(value: str, unit: ReportedUnit, field_name: str) -> ParsedMoney:
    parsed = parse_money(value, unit)
    if parsed.value is None:
        raise ImportContractError(f"{field_name} is required")
    return parsed


def _optional_money(value: str | None, unit: ReportedUnit) -> ParsedMoney:
    return parse_money(value, unit)


def _decimal_places(original: str | None) -> int | None:
    if original is None:
        return None
    text = str(original).strip()
    if not text or text.casefold() in {"-", "–", "—", "n/a", "na", "null"}:
        return None
    if text.startswith("(") and text.endswith(")"):
        text = text[1:-1].strip()
    text = re.sub(r"^(?:₦|ngn)\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*ngn$", "", text, flags=re.IGNORECASE)
    text = text.replace(",", "").replace(" ", "")
    match = re.fullmatch(r"[+-]?(?:\d+(?:\.(\d+))?|\.([0-9]+))", text)
    if match is None:
        return None
    return len(match.group(1) or match.group(2) or "")


def _source_precision_tolerance(originals: list[str | None], unit: ReportedUnit) -> Decimal:
    """Return half the least precise displayed quantum, never below one kobo."""
    base = _UNIT_QUANTA.get(unit)
    if base is None:
        return Decimal("0.01")
    quanta = [
        base / (Decimal(10) ** places)
        for original in originals
        if (places := _decimal_places(original)) is not None
    ]
    if not quanta:
        return Decimal("0.01")
    return max(Decimal("0.01"), max(quanta) / Decimal("2"))


def _configuration(
    run: ExtractionRun,
) -> tuple[str, str, dict[str, str | None]]:
    configuration = run.configuration or {}
    treatment = str(configuration.get("derivation_treatment") or "")
    states_scope = str(configuration.get("states_scope") or "")
    originals = configuration.get("original_values") or {}
    if not isinstance(originals, dict):
        originals = {}
    return (
        treatment,
        states_scope,
        {str(key): None if value is None else str(value) for key, value in originals.items()},
    )


def _component_reconciliation(
    distribution: NationalDistribution,
    *,
    derivation_treatment: str,
    originals: dict[str, str | None],
) -> ComponentReconciliation:
    if derivation_treatment not in DERIVATION_TREATMENTS:
        return ComponentReconciliation(
            "conflicted",
            None,
            None,
            None,
            derivation_treatment,
            "The derivation treatment is invalid, so additive reconciliation is blocked.",
        )
    required = (
        distribution.net_distributable_amount,
        distribution.federal_amount,
        distribution.states_amount,
        distribution.local_governments_amount,
    )
    if any(value is None for value in required):
        return ComponentReconciliation(
            "unavailable",
            None,
            None,
            None,
            derivation_treatment,
            "Required national distribution values are unavailable.",
        )
    if derivation_treatment == "not_reported":
        return ComponentReconciliation(
            "unavailable",
            None,
            None,
            None,
            derivation_treatment,
            "The source does not report derivation semantics that support additive reconciliation.",
        )

    component_total = (
        distribution.federal_amount
        + distribution.states_amount
        + distribution.local_governments_amount
    )
    compared_originals = [
        originals.get("net_distributable_amount"),
        originals.get("federal_amount"),
        originals.get("states_amount"),
        originals.get("local_governments_amount"),
    ]
    if derivation_treatment == "separate":
        if distribution.derivation_amount is None:
            return ComponentReconciliation(
                "unavailable",
                None,
                None,
                None,
                derivation_treatment,
                "Derivation is marked separate but no derivation amount is reported.",
            )
        component_total += distribution.derivation_amount
        compared_originals.append(originals.get("derivation_amount"))

    tolerance = _source_precision_tolerance(compared_originals, distribution.reported_unit)
    variance = component_total - distribution.net_distributable_amount
    reconciled = abs(variance) <= tolerance
    return ComponentReconciliation(
        "reconciled" if reconciled else "conflicted",
        component_total,
        variance,
        tolerance,
        derivation_treatment,
        (
            "The observed national components reconcile within source-derived reporting precision."
            if reconciled
            else "The observed national components do not reconcile within "
            "source-derived reporting precision."
        ),
    )


def validate_national_distribution(session: Session, run: ExtractionRun) -> list[ValidationResult]:
    configuration = run.configuration or {}
    if configuration.get("scope") != "national_distribution":
        raise ValueError("Extraction run is not a national-distribution run")
    raw_distribution_id = configuration.get("distribution_id")
    if not raw_distribution_id:
        raise ValueError("National-distribution run has no distribution id")
    distribution = session.get(NationalDistribution, uuid.UUID(str(raw_distribution_id)))
    if distribution is None:
        raise ValueError("National distribution does not exist")
    source = session.get(SourceDocument, run.source_document_id)
    if source is None or source.id != distribution.source_document_id:
        raise ValueError("National distribution source lineage is invalid")

    session.execute(delete(ValidationResult).where(ValidationResult.extraction_run_id == run.id))
    treatment, states_scope, originals = _configuration(run)
    findings: list[Finding] = []

    if distribution.reported_unit is ReportedUnit.UNSPECIFIED:
        findings.append(
            Finding(
                "NATIONAL_INVALID_MONETARY_UNIT",
                ValidationSeverity.ERROR,
                "National distribution has no explicit reported monetary unit.",
            )
        )
    if treatment not in DERIVATION_TREATMENTS:
        findings.append(
            Finding(
                "NATIONAL_INVALID_DERIVATION_TREATMENT",
                ValidationSeverity.ERROR,
                "Derivation treatment must be separate, included_in_states, or not_reported.",
                details={"derivation_treatment": treatment},
            )
        )
    if states_scope not in STATES_SCOPES:
        findings.append(
            Finding(
                "NATIONAL_STATES_SCOPE_REQUIRED",
                ValidationSeverity.ERROR,
                "Declare whether the official states aggregate covers 36 states or "
                "36 states plus FCT.",
                details={"states_scope": states_scope or None},
            )
        )

    required_values = {
        "net_distributable_amount": distribution.net_distributable_amount,
        "federal_amount": distribution.federal_amount,
        "states_amount": distribution.states_amount,
        "local_governments_amount": distribution.local_governments_amount,
    }
    for field_name, value in required_values.items():
        if value is None:
            findings.append(
                Finding(
                    "NATIONAL_MISSING_REQUIRED_VALUE",
                    ValidationSeverity.ERROR,
                    f"Required national value {field_name} is missing.",
                    details={"field": field_name},
                )
            )

    for field_name, value in {
        **required_values,
        "gross_amount": distribution.gross_amount,
        "deductions_amount": distribution.deductions_amount,
        "vat_amount": distribution.vat_amount,
        "statutory_amount": distribution.statutory_amount,
        "derivation_amount": distribution.derivation_amount,
    }.items():
        if value is not None and value < 0:
            findings.append(
                Finding(
                    "NATIONAL_NEGATIVE_VALUE_REQUIRES_REVIEW",
                    ValidationSeverity.WARNING,
                    f"Negative national value {field_name} requires human review.",
                    details={"field": field_name, "value": str(value)},
                )
            )

    reconciliation = _component_reconciliation(
        distribution,
        derivation_treatment=treatment,
        originals=originals,
    )
    if reconciliation.status == "conflicted":
        findings.append(
            Finding(
                "NATIONAL_COMPONENT_TOTAL_MISMATCH",
                ValidationSeverity.ERROR,
                "National components do not reconcile with the reported distributable total.",
                details={
                    "component_total": str(reconciliation.component_total),
                    "net_distributable_amount": str(distribution.net_distributable_amount),
                    "variance": str(reconciliation.variance),
                    "derivation_treatment": treatment,
                },
                tolerance=reconciliation.tolerance,
            )
        )
    elif reconciliation.status == "unavailable":
        findings.append(
            Finding(
                "NATIONAL_COMPONENT_RECONCILIATION_UNAVAILABLE",
                ValidationSeverity.WARNING,
                reconciliation.note,
                details={"derivation_treatment": treatment},
            )
        )

    if (
        distribution.gross_amount is not None
        and distribution.deductions_amount is not None
        and distribution.net_distributable_amount is not None
    ):
        tolerance = _source_precision_tolerance(
            [
                originals.get("gross_amount"),
                originals.get("deductions_amount"),
                originals.get("net_distributable_amount"),
            ],
            distribution.reported_unit,
        )
        variance = (
            distribution.gross_amount
            - distribution.deductions_amount
            - distribution.net_distributable_amount
        )
        if abs(variance) > tolerance:
            findings.append(
                Finding(
                    "NATIONAL_GROSS_DEDUCTIONS_NET_MISMATCH",
                    ValidationSeverity.ERROR,
                    "National gross amount minus deductions does not reconcile with "
                    "the distributable total.",
                    details={"variance": str(variance)},
                    tolerance=tolerance,
                )
            )

    results = [
        ValidationResult(
            extraction_run_id=run.id,
            reporting_period_id=distribution.reporting_period_id,
            rule_code=finding.rule_code,
            outcome=VerificationStatus.REQUIRES_REVIEW,
            severity=finding.severity,
            message=finding.message,
            details=finding.details,
            tolerance=finding.tolerance,
        )
        for finding in findings
    ]
    session.add_all(results)
    distribution.verification_status = (
        VerificationStatus.REQUIRES_REVIEW
        if any(finding.severity in _BLOCKING for finding in findings)
        else VerificationStatus.AUTOMATICALLY_VALIDATED
    )
    source.source_status = SourceStatus.READY_FOR_REVIEW
    source.processing_status = ProcessingStatus.READY_FOR_REVIEW
    run.status = ExtractionStatus.REQUIRES_REVIEW
    run.completed_at = datetime.now(UTC)
    session.flush()
    return results


def import_national_distribution(
    session: Session, request: NationalDistributionImportRequest
) -> NationalDistributionResult:
    try:
        period = session.get(ReportingPeriod, request.reporting_period_id)
        if period is None:
            raise ImportContractError("Reporting period does not exist")
        if period.is_demo:
            raise ImportContractError(
                "National distribution evidence cannot attach to a demo period"
            )
        if not request.source_organization.strip():
            raise ImportContractError("Source organization is required")
        if not request.document_version.strip():
            raise ImportContractError("Document version is required")
        treatment = request.derivation_treatment.strip().casefold()
        if treatment not in DERIVATION_TREATMENTS:
            raise ImportContractError(
                "Derivation treatment must be separate, included_in_states, or not_reported"
            )
        try:
            unit = parse_reported_unit(request.reported_unit)
        except MonetaryParseError as error:
            raise ImportContractError(str(error)) from error
        if unit is ReportedUnit.UNSPECIFIED:
            raise ImportContractError("An explicit monetary unit is required")

        source = register_source_document(
            session,
            path=request.path,
            source_organization=request.source_organization,
            publication_date=request.publication_date,
            source_url=request.source_url,
            document_version=request.document_version,
            source_status=SourceStatus.PENDING,
            processing_status=ProcessingStatus.PROCESSING,
            is_demo=False,
            commit=False,
        )
        if source.reporting_period_id not in (None, period.id):
            raise ImportContractError(
                "Source document is already attached to another reporting period"
            )
        if session.scalar(
            select(StateAllocation.id)
            .where(StateAllocation.source_document_id == source.id)
            .limit(1)
        ):
            raise ImportContractError(
                "Use a distinct national source document; a jurisdiction-allocation "
                "source cannot be reused."
            )
        source.reporting_period_id = period.id
        if session.scalar(
            select(NationalDistribution.id).where(
                NationalDistribution.reporting_period_id == period.id,
                NationalDistribution.source_document_id == source.id,
            )
        ):
            raise ImportContractError("This national distribution source is already imported")

        net = _required_money(request.net_distributable_amount, unit, "net_distributable_amount")
        federal = _required_money(request.federal_amount, unit, "federal_amount")
        states = _required_money(request.states_amount, unit, "states_amount")
        lgas = _required_money(request.local_governments_amount, unit, "local_governments_amount")
        derivation = _optional_money(request.derivation_amount, unit)
        gross = _optional_money(request.gross_amount, unit)
        deductions = _optional_money(request.deductions_amount, unit)
        vat = _optional_money(request.vat_amount, unit)
        statutory = _optional_money(request.statutory_amount, unit)
        if treatment == "separate" and derivation.value is None:
            raise ImportContractError(
                "derivation_amount is required when derivation_treatment is separate"
            )

        distribution = NationalDistribution(
            reporting_period_id=period.id,
            source_document_id=source.id,
            gross_amount=gross.value,
            deductions_amount=deductions.value,
            net_distributable_amount=net.value,
            federal_amount=federal.value,
            states_amount=states.value,
            local_governments_amount=lgas.value,
            vat_amount=vat.value,
            statutory_amount=statutory.value,
            derivation_amount=derivation.value,
            gross_amount_original=gross.original_text,
            deductions_amount_original=deductions.original_text,
            net_amount_original=net.original_text,
            reported_unit=unit,
            verification_status=VerificationStatus.PENDING,
            is_demo=False,
            is_published=False,
        )
        session.add(distribution)
        session.flush()
        originals = {
            "gross_amount": gross.original_text,
            "deductions_amount": deductions.original_text,
            "net_distributable_amount": net.original_text,
            "federal_amount": federal.original_text,
            "states_amount": states.original_text,
            "local_governments_amount": lgas.original_text,
            "vat_amount": vat.original_text,
            "statutory_amount": statutory.original_text,
            "derivation_amount": derivation.original_text,
        }
        run = ExtractionRun(
            source_document_id=source.id,
            status=ExtractionStatus.RUNNING,
            extractor_name="controlled_national_distribution",
            extractor_version="1",
            started_at=datetime.now(UTC),
            records_extracted=1,
            configuration={
                "scope": "national_distribution",
                "distribution_id": str(distribution.id),
                "derivation_treatment": treatment,
                "original_values": originals,
            },
        )
        session.add(run)
        session.flush()
        results = validate_national_distribution(session, run)
        session.commit()
        blocking = sum(result.severity in _BLOCKING for result in results)
        return NationalDistributionResult(
            str(distribution.id),
            str(run.id),
            str(period.id),
            len(results),
            blocking,
            False,
        )
    except Exception:
        session.rollback()
        raise


def _review_context(
    session: Session, run_id: uuid.UUID, reviewer_id: uuid.UUID
) -> tuple[ExtractionRun, NationalDistribution, SourceDocument, ReportingPeriod, User]:
    run = session.get(ExtractionRun, run_id)
    reviewer = session.get(User, reviewer_id)
    if run is None or reviewer is None:
        raise ApprovalError("Extraction run or reviewer does not exist")
    if not reviewer.is_active or reviewer.role not in {
        UserRole.REVIEWER,
        UserRole.ADMINISTRATOR,
    }:
        raise ApprovalError("National review requires an active reviewer or administrator")
    configuration = run.configuration or {}
    if configuration.get("scope") != "national_distribution":
        raise ApprovalError("Extraction run is not a national-distribution run")
    raw_distribution_id = configuration.get("distribution_id")
    distribution = (
        session.get(NationalDistribution, uuid.UUID(str(raw_distribution_id)))
        if raw_distribution_id
        else None
    )
    if distribution is None:
        raise ApprovalError("National distribution does not exist")
    source = session.get(SourceDocument, distribution.source_document_id)
    period = session.get(ReportingPeriod, distribution.reporting_period_id)
    if source is None or period is None or source.id != run.source_document_id:
        raise ApprovalError("National distribution source lineage is invalid")
    return run, distribution, source, period, reviewer


def approve_national_distribution(
    session: Session,
    *,
    run_id: uuid.UUID,
    reviewer_id: uuid.UUID,
    note: str | None = None,
) -> NationalDistributionResult:
    run, distribution, source, period, reviewer = _review_context(session, run_id, reviewer_id)
    if (
        run.status is ExtractionStatus.COMPLETED
        and distribution.verification_status is VerificationStatus.HUMAN_VERIFIED
    ):
        return NationalDistributionResult(
            str(distribution.id), str(run.id), str(period.id), 0, 0, distribution.is_published
        )
    if run.status is not ExtractionStatus.REQUIRES_REVIEW:
        raise ApprovalError("National distribution is not awaiting explicit review")

    results = validate_national_distribution(session, run)
    blocking = sum(result.severity in _BLOCKING for result in results)
    if blocking:
        session.commit()
        raise ApprovalError(f"National distribution has {blocking} blocking validation findings")

    distribution.verification_status = VerificationStatus.HUMAN_VERIFIED
    source.source_status = SourceStatus.APPROVED
    source.processing_status = ProcessingStatus.COMPLETED
    run.status = ExtractionStatus.COMPLETED
    session.add(
        AuditLog(
            actor_user_id=reviewer.id,
            action="national_distribution.approved",
            entity_type="national_distribution",
            entity_id=distribution.id,
            payload={
                "reporting_period_id": str(period.id),
                "source_document_id": str(source.id),
                "states_scope": (run.configuration or {}).get("states_scope"),
                "review_note": note.strip() if note and note.strip() else None,
                "published": False,
            },
        )
    )
    session.commit()
    return NationalDistributionResult(
        str(distribution.id), str(run.id), str(period.id), len(results), blocking, False
    )


def publish_national_distribution(
    session: Session, *, run_id: uuid.UUID, reviewer_id: uuid.UUID
) -> NationalDistributionResult:
    run, distribution, source, period, publisher = _review_context(session, run_id, reviewer_id)
    if publisher.role is not UserRole.ADMINISTRATOR:
        raise ApprovalError("Publishing national evidence requires an active administrator")
    approval = session.scalar(
        select(AuditLog)
        .where(
            AuditLog.action == "national_distribution.approved",
            AuditLog.entity_type == "national_distribution",
            AuditLog.entity_id == distribution.id,
        )
        .order_by(AuditLog.created_at.desc())
        .limit(1)
    )
    if approval is None:
        raise ApprovalError("National distribution has no attributable human approval")
    if approval.actor_user_id == publisher.id:
        raise ApprovalError("The national-distribution reviewer cannot publish the same evidence")
    if period.is_demo or source.is_demo or distribution.is_demo:
        raise ApprovalError("Demo data can never be published")
    if not period.is_published:
        raise ApprovalError(
            "Publish the governed jurisdiction period before its national distribution"
        )
    if distribution.verification_status is not VerificationStatus.HUMAN_VERIFIED:
        raise ApprovalError("Only human-verified national evidence can be published")
    if distribution.is_published:
        return NationalDistributionResult(
            str(distribution.id), str(run.id), str(period.id), 0, 0, True
        )

    distribution.is_published = True
    distribution.published_at = datetime.now(UTC)
    session.add(
        AuditLog(
            actor_user_id=publisher.id,
            action="national_distribution.published",
            entity_type="national_distribution",
            entity_id=distribution.id,
            payload={
                "reporting_period_id": str(period.id),
                "source_document_id": str(source.id),
                "states_scope": (run.configuration or {}).get("states_scope"),
                "separation_of_duties": True,
                "published": True,
            },
        )
    )
    session.commit()
    return NationalDistributionResult(str(distribution.id), str(run.id), str(period.id), 0, 0, True)


def reconciliation_for_distribution(
    distribution: NationalDistribution, run: ExtractionRun
) -> ComponentReconciliation:
    treatment, _states_scope, originals = _configuration(run)
    return _component_reconciliation(
        distribution,
        derivation_treatment=treatment,
        originals=originals,
    )