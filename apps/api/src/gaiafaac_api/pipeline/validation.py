from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from gaiafaac_api.database.enums import (
    ExtractionStatus,
    ProcessingStatus,
    ReportedUnit,
    SourceStatus,
    ValidationSeverity,
    VerificationStatus,
)
from gaiafaac_api.database.models import (
    ExtractionRun,
    NationalDistribution,
    ReportingPeriod,
    SourceDocument,
    State,
    StateAllocation,
    StateAllocationComponent,
    ValidationResult,
)

DEFAULT_TOLERANCE = Decimal("0.01")
DEFAULT_MOVEMENT_THRESHOLD = Decimal("1.00")


@dataclass(frozen=True)
class Finding:
    rule_code: str
    severity: ValidationSeverity
    message: str
    state_allocation_id: uuid.UUID | None = None
    details: dict[str, Any] = field(default_factory=dict)
    tolerance: Decimal | None = None


def _difference_exceeds(left: Decimal, right: Decimal, tolerance: Decimal) -> bool:
    return abs(left - right) > tolerance


def _component_total(components: list[StateAllocationComponent], field_name: str) -> Decimal | None:
    values = [getattr(component, field_name) for component in components]
    if not values or any(value is None for value in values):
        return None
    return sum(values, Decimal("0"))


def _period_findings(period: ReportingPeriod) -> list[Finding]:
    findings: list[Finding] = []
    if period.revenue_month.day != 1:
        findings.append(
            Finding(
                "PERIOD_REVENUE_MONTH_NOT_FIRST_DAY",
                ValidationSeverity.ERROR,
                "Revenue month must be represented by the first day of its month.",
            )
        )
    if period.faac_meeting_date and period.faac_meeting_date < period.revenue_month:
        findings.append(
            Finding(
                "PERIOD_MEETING_BEFORE_REVENUE_MONTH",
                ValidationSeverity.ERROR,
                "FAAC meeting date precedes the revenue month.",
            )
        )
    if period.publication_date and period.publication_date < period.revenue_month:
        findings.append(
            Finding(
                "PERIOD_PUBLICATION_BEFORE_REVENUE_MONTH",
                ValidationSeverity.ERROR,
                "Publication date precedes the revenue month.",
            )
        )
    if (
        period.publication_date
        and period.faac_meeting_date
        and period.publication_date < period.faac_meeting_date
    ):
        findings.append(
            Finding(
                "PERIOD_PUBLICATION_BEFORE_MEETING",
                ValidationSeverity.ERROR,
                "Publication date precedes the FAAC meeting date.",
            )
        )
    return findings


def _allocation_findings(
    allocation: StateAllocation,
    components: list[StateAllocationComponent],
    *,
    tolerance: Decimal,
) -> list[Finding]:
    findings: list[Finding] = []
    allocation_id = allocation.id
    if allocation.reported_unit is ReportedUnit.UNSPECIFIED:
        findings.append(
            Finding(
                "INVALID_MONETARY_UNIT",
                ValidationSeverity.ERROR,
                "Allocation has no explicit reported monetary unit.",
                allocation_id,
            )
        )
    values = {
        "gross_total": allocation.gross_total,
        "total_deductions": allocation.total_deductions,
        "net_allocation": allocation.net_allocation,
    }
    for field_name, value in values.items():
        if value is None:
            findings.append(
                Finding(
                    "MISSING_MONETARY_VALUE",
                    ValidationSeverity.ERROR,
                    f"Required allocation value {field_name} is missing.",
                    allocation_id,
                    {"field": field_name},
                )
            )
        elif value < 0:
            findings.append(
                Finding(
                    "NEGATIVE_VALUE_REQUIRES_REVIEW",
                    ValidationSeverity.WARNING,
                    f"Negative {field_name} requires human review.",
                    allocation_id,
                    {"field": field_name, "value": str(value)},
                )
            )
    if all(value is not None for value in values.values()) and _difference_exceeds(
        allocation.gross_total - allocation.total_deductions,
        allocation.net_allocation,
        tolerance,
    ):
        findings.append(
            Finding(
                "GROSS_DEDUCTIONS_NET_MISMATCH",
                ValidationSeverity.ERROR,
                "Gross total minus deductions does not reconcile with net allocation.",
                allocation_id,
                {
                    "gross_total": str(allocation.gross_total),
                    "total_deductions": str(allocation.total_deductions),
                    "net_allocation": str(allocation.net_allocation),
                },
                tolerance,
            )
        )
    for component_field, allocation_field in (
        ("gross_amount", "gross_total"),
        ("deduction_amount", "total_deductions"),
        ("net_amount", "net_allocation"),
    ):
        if components and any(
            getattr(component, component_field) is None for component in components
        ):
            findings.append(
                Finding(
                    "COMPONENT_VALUE_MISSING",
                    ValidationSeverity.ERROR,
                    f"At least one component {component_field} value is missing.",
                    allocation_id,
                    {"component_field": component_field},
                )
            )
            continue
        component_sum = _component_total(components, component_field)
        allocation_value = getattr(allocation, allocation_field)
        if (
            component_sum is not None
            and allocation_value is not None
            and _difference_exceeds(component_sum, allocation_value, tolerance)
        ):
            findings.append(
                Finding(
                    "COMPONENT_TOTAL_MISMATCH",
                    ValidationSeverity.ERROR,
                    f"Component {component_field} total does not reconcile.",
                    allocation_id,
                    {
                        "component_field": component_field,
                        "component_total": str(component_sum),
                        "allocation_field": allocation_field,
                        "allocation_value": str(allocation_value),
                    },
                    tolerance,
                )
            )
    return findings


def _movement_findings(
    session: Session,
    period: ReportingPeriod,
    allocations: list[StateAllocation],
    *,
    threshold: Decimal,
) -> list[Finding]:
    findings: list[Finding] = []
    for allocation in allocations:
        previous = session.scalar(
            select(StateAllocation)
            .join(ReportingPeriod, StateAllocation.reporting_period_id == ReportingPeriod.id)
            .where(
                StateAllocation.state_id == allocation.state_id,
                ReportingPeriod.revenue_month < period.revenue_month,
                StateAllocation.net_allocation.is_not(None),
            )
            .order_by(ReportingPeriod.revenue_month.desc())
            .limit(1)
        )
        if (
            previous is None
            or previous.net_allocation in (None, Decimal("0"))
            or allocation.net_allocation is None
        ):
            continue
        change = abs(
            (allocation.net_allocation - previous.net_allocation) / previous.net_allocation
        )
        if change > threshold:
            findings.append(
                Finding(
                    "UNEXPECTED_MONTH_OVER_MONTH_MOVEMENT",
                    ValidationSeverity.WARNING,
                    "Month-over-month net allocation movement exceeds the configured threshold.",
                    allocation.id,
                    {
                        "previous_net_allocation": str(previous.net_allocation),
                        "current_net_allocation": str(allocation.net_allocation),
                        "absolute_change_ratio": str(change),
                        "threshold": str(threshold),
                    },
                )
            )
    return findings


def validate_import(
    session: Session,
    run: ExtractionRun,
    *,
    initial_findings: list[Finding] | None = None,
    tolerance: Decimal = DEFAULT_TOLERANCE,
    movement_threshold: Decimal = DEFAULT_MOVEMENT_THRESHOLD,
) -> list[ValidationResult]:
    """Rebuild durable findings and move an import into explicit-review state."""
    if run.status not in {ExtractionStatus.RUNNING, ExtractionStatus.REQUIRES_REVIEW}:
        raise ValueError("Only running or review-pending extraction runs can be validated")
    source = session.get(SourceDocument, run.source_document_id)
    if source is None or source.reporting_period_id is None:
        raise ValueError("Extraction run source is not linked to a reporting period")
    period = session.get(ReportingPeriod, source.reporting_period_id)
    if period is None:
        raise ValueError("Reporting period does not exist")

    preserved_import_findings: list[Finding] = []
    if initial_findings is None:
        for result in session.scalars(
            select(ValidationResult).where(
                ValidationResult.extraction_run_id == run.id,
                ValidationResult.rule_code.like("IMPORT_%"),
            )
        ):
            preserved_import_findings.append(
                Finding(
                    rule_code=result.rule_code,
                    severity=result.severity,
                    message=result.message,
                    state_allocation_id=result.state_allocation_id,
                    details=result.details or {},
                    tolerance=result.tolerance,
                )
            )
    session.execute(delete(ValidationResult).where(ValidationResult.extraction_run_id == run.id))
    allocations = list(
        session.scalars(
            select(StateAllocation).where(StateAllocation.reporting_period_id == period.id)
        )
    )
    components_by_allocation: dict[uuid.UUID, list[StateAllocationComponent]] = {}
    if allocations:
        components = session.scalars(
            select(StateAllocationComponent).where(
                StateAllocationComponent.state_allocation_id.in_(
                    [allocation.id for allocation in allocations]
                )
            )
        )
        for component in components:
            components_by_allocation.setdefault(component.state_allocation_id, []).append(component)

    findings = list(initial_findings if initial_findings is not None else preserved_import_findings)
    findings.extend(_period_findings(period))
    expected_states = session.scalar(select(func.count()).select_from(State)) or 0
    imported_state_ids = {allocation.state_id for allocation in allocations}
    if len(imported_state_ids) != expected_states:
        missing_codes = list(
            session.scalars(
                select(State.code).where(State.id.not_in(imported_state_ids)).order_by(State.code)
            )
        )
        findings.append(
            Finding(
                "MISSING_STATES",
                ValidationSeverity.ERROR,
                "Import does not contain every canonical state and the FCT.",
                details={
                    "expected_count": expected_states,
                    "imported_count": len(imported_state_ids),
                    "missing_state_codes": missing_codes,
                },
            )
        )
    duplicate_state_ids = list(
        session.scalars(
            select(StateAllocation.state_id)
            .where(StateAllocation.reporting_period_id == period.id)
            .group_by(StateAllocation.state_id)
            .having(func.count(StateAllocation.id) > 1)
        )
    )
    if duplicate_state_ids:
        findings.append(
            Finding(
                "DUPLICATE_STATE_PERIOD",
                ValidationSeverity.ERROR,
                "Duplicate state allocations exist for the reporting period.",
                details={"state_ids": [str(value) for value in duplicate_state_ids]},
            )
        )
    for allocation in allocations:
        if allocation.source_document_id != source.id:
            findings.append(
                Finding(
                    "SOURCE_DOCUMENT_MISMATCH",
                    ValidationSeverity.ERROR,
                    "Allocation source does not match the extraction run source.",
                    allocation.id,
                )
            )
        findings.extend(
            _allocation_findings(
                allocation,
                components_by_allocation.get(allocation.id, []),
                tolerance=tolerance,
            )
        )
    findings.extend(_movement_findings(session, period, allocations, threshold=movement_threshold))

    national = session.scalar(
        select(NationalDistribution).where(
            NationalDistribution.reporting_period_id == period.id,
            NationalDistribution.source_document_id == source.id,
        )
    )
    if national and national.states_amount is not None:
        state_total = sum(
            (
                allocation.net_allocation
                for allocation in allocations
                if allocation.net_allocation is not None
            ),
            Decimal("0"),
        )
        if _difference_exceeds(state_total, national.states_amount, tolerance):
            findings.append(
                Finding(
                    "STATE_TOTAL_NATIONAL_MISMATCH",
                    ValidationSeverity.ERROR,
                    "State net allocations do not reconcile with the reported states aggregate.",
                    details={
                        "state_net_total": str(state_total),
                        "reported_states_amount": str(national.states_amount),
                    },
                    tolerance=tolerance,
                )
            )

    results = [
        ValidationResult(
            extraction_run_id=run.id,
            reporting_period_id=period.id,
            state_allocation_id=finding.state_allocation_id,
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
    blocking_ids = {
        finding.state_allocation_id
        for finding in findings
        if finding.severity in {ValidationSeverity.ERROR, ValidationSeverity.CRITICAL}
        and finding.state_allocation_id is not None
    }
    has_global_blocker = any(
        finding.severity in {ValidationSeverity.ERROR, ValidationSeverity.CRITICAL}
        and finding.state_allocation_id is None
        for finding in findings
    )
    for allocation in allocations:
        allocation.verification_status = (
            VerificationStatus.REQUIRES_REVIEW
            if has_global_blocker or allocation.id in blocking_ids
            else VerificationStatus.AUTOMATICALLY_VALIDATED
        )
    period.verification_status = (
        VerificationStatus.REQUIRES_REVIEW
        if any(
            finding.severity in {ValidationSeverity.ERROR, ValidationSeverity.CRITICAL}
            for finding in findings
        )
        else VerificationStatus.AUTOMATICALLY_VALIDATED
    )
    period.source_status = SourceStatus.READY_FOR_REVIEW
    source.source_status = SourceStatus.READY_FOR_REVIEW
    source.processing_status = ProcessingStatus.READY_FOR_REVIEW
    run.status = ExtractionStatus.REQUIRES_REVIEW
    session.flush()
    return results
