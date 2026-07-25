import csv
import uuid
from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from gaiafaac_api.database.enums import (
    ComponentType,
    ExtractionStatus,
    ReportedUnit,
    SourceStatus,
    UserRole,
    ValidationSeverity,
    VerificationStatus,
)
from gaiafaac_api.database.models import (
    AuditLog,
    ExtractionRun,
    Organization,
    ReportingPeriod,
    StateAllocation,
    StateAllocationComponent,
    User,
    ValidationResult,
)
from gaiafaac_api.database.seeds import NIGERIAN_STATES, seed_states
from gaiafaac_api.pipeline.approval import approve_import, reject_import
from gaiafaac_api.pipeline.errors import ApprovalError
from gaiafaac_api.pipeline.importer import ImportRequest, import_allocations_csv
from gaiafaac_api.pipeline.validation import validate_import

CSV_COLUMNS = [
    "state",
    "gross_total",
    "total_deductions",
    "net_allocation",
    "reported_unit",
    "extraction_confidence",
]


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def _complete_rows() -> list[dict[str, str]]:
    return [
        {
            "state": name,
            "gross_total": "1,000.00",
            "total_deductions": "100.00",
            "net_allocation": "900.00",
            "reported_unit": "naira",
            "extraction_confidence": "0.95",
        }
        for name, _code, _slug, _zone, _capital, _is_fct in NIGERIAN_STATES
    ]


def _request(path: Path, label: str = "January 2026 allocation") -> ImportRequest:
    return ImportRequest(
        path=path,
        source_organization="Test source organization",
        revenue_month=date(2026, 1, 1),
        faac_meeting_date=date(2026, 2, 1),
        publication_date=date(2026, 2, 2),
        reporting_label=label,
    )


def _reviewer(session: Session, role: UserRole = UserRole.REVIEWER) -> User:
    organization = Organization(name="Test review organization", slug=f"test-{uuid.uuid4()}")
    session.add(organization)
    session.flush()
    reviewer = User(
        organization_id=organization.id,
        email=f"{uuid.uuid4()}@example.test",
        full_name="Test Reviewer",
        role=role,
        is_active=True,
    )
    session.add(reviewer)
    session.commit()
    return reviewer


def test_complete_import_is_automatically_validated_but_not_published(
    session: Session, tmp_path: Path
) -> None:
    seed_states(session)
    path = tmp_path / "allocations.csv"
    _write_csv(path, _complete_rows())

    result = import_allocations_csv(session, _request(path))
    run = session.get(ExtractionRun, uuid.UUID(result.run_id))
    period = session.get(ReportingPeriod, uuid.UUID(result.reporting_period_id))
    allocations = list(session.scalars(select(StateAllocation)))

    assert result.records_extracted == 37
    assert result.finding_count == 0
    assert result.blocking_finding_count == 0
    assert run is not None and run.status is ExtractionStatus.REQUIRES_REVIEW
    assert period is not None
    assert period.verification_status is VerificationStatus.AUTOMATICALLY_VALIDATED
    assert period.is_published is False
    assert len(allocations) == 37
    assert all(
        allocation.verification_status is VerificationStatus.AUTOMATICALLY_VALIDATED
        for allocation in allocations
    )
    assert all(allocation.is_published is False for allocation in allocations)
    assert allocations[0].gross_total_original == "1,000.00"


def test_explicit_reviewer_approval_human_verifies_without_publishing(
    session: Session, tmp_path: Path
) -> None:
    seed_states(session)
    path = tmp_path / "clean.csv"
    _write_csv(path, _complete_rows())
    imported = import_allocations_csv(session, _request(path))
    reviewer = _reviewer(session)

    approved = approve_import(session, run_id=uuid.UUID(imported.run_id), reviewer_id=reviewer.id)
    period = session.get(ReportingPeriod, uuid.UUID(imported.reporting_period_id))
    allocations = list(session.scalars(select(StateAllocation)))

    assert approved.allocations_approved == 37
    assert approved.published is False
    assert period is not None
    assert period.verification_status is VerificationStatus.HUMAN_VERIFIED
    assert period.is_published is False
    assert all(
        allocation.verification_status is VerificationStatus.HUMAN_VERIFIED
        for allocation in allocations
    )
    assert all(allocation.reviewed_by == reviewer.id for allocation in allocations)
    assert session.scalar(select(func.count()).select_from(AuditLog)) == 1


def test_viewer_cannot_approve_import(session: Session, tmp_path: Path) -> None:
    seed_states(session)
    path = tmp_path / "clean.csv"
    _write_csv(path, _complete_rows())
    imported = import_allocations_csv(session, _request(path))
    viewer = _reviewer(session, UserRole.VIEWER)

    with pytest.raises(ApprovalError, match="reviewer or administrator"):
        approve_import(session, run_id=uuid.UUID(imported.run_id), reviewer_id=viewer.id)


def test_reconciliation_and_missing_states_create_blocking_findings(
    session: Session, tmp_path: Path
) -> None:
    seed_states(session)
    path = tmp_path / "invalid.csv"
    rows = _complete_rows()[:1]
    rows[0]["net_allocation"] = "950.00"
    _write_csv(path, rows)

    imported = import_allocations_csv(session, _request(path))
    findings = list(
        session.scalars(
            select(ValidationResult).where(
                ValidationResult.extraction_run_id == uuid.UUID(imported.run_id)
            )
        )
    )
    reviewer = _reviewer(session)

    assert imported.blocking_finding_count == 2
    assert {finding.rule_code for finding in findings} == {
        "GROSS_DEDUCTIONS_NET_MISMATCH",
        "MISSING_STATES",
    }
    assert all(finding.severity is ValidationSeverity.ERROR for finding in findings)
    with pytest.raises(ApprovalError, match="blocking validation findings"):
        approve_import(session, run_id=uuid.UUID(imported.run_id), reviewer_id=reviewer.id)


def test_invalid_alias_duplicate_and_monetary_value_are_durable_findings(
    session: Session, tmp_path: Path
) -> None:
    seed_states(session)
    path = tmp_path / "bad-rows.csv"
    rows = [
        {
            "state": "Lagos",
            "gross_total": "1000",
            "total_deductions": "100",
            "net_allocation": "900",
            "reported_unit": "naira",
            "extraction_confidence": "",
        },
        {
            "state": "LA",
            "gross_total": "1000",
            "total_deductions": "100",
            "net_allocation": "900",
            "reported_unit": "naira",
            "extraction_confidence": "",
        },
        {
            "state": "Laggoz",
            "gross_total": "1000",
            "total_deductions": "100",
            "net_allocation": "900",
            "reported_unit": "naira",
            "extraction_confidence": "",
        },
        {
            "state": "Kano",
            "gross_total": "not money",
            "total_deductions": "100",
            "net_allocation": "900",
            "reported_unit": "naira",
            "extraction_confidence": "",
        },
    ]
    _write_csv(path, rows)

    imported = import_allocations_csv(session, _request(path))
    codes = set(
        session.scalars(
            select(ValidationResult.rule_code).where(
                ValidationResult.extraction_run_id == uuid.UUID(imported.run_id)
            )
        )
    )

    assert imported.records_extracted == 1
    assert {
        "IMPORT_DUPLICATE_STATE",
        "IMPORT_INVALID_STATE_ALIAS",
        "IMPORT_INVALID_MONETARY_VALUE",
        "MISSING_STATES",
    } <= codes


def test_component_reconciliation_finding_is_persisted(session: Session, tmp_path: Path) -> None:
    seed_states(session)
    path = tmp_path / "components.csv"
    _write_csv(path, _complete_rows())
    imported = import_allocations_csv(session, _request(path))
    run = session.get(ExtractionRun, uuid.UUID(imported.run_id))
    allocation = session.scalar(select(StateAllocation).limit(1))
    assert run is not None and allocation is not None
    session.add(
        StateAllocationComponent(
            state_allocation_id=allocation.id,
            component_type=ComponentType.STATUTORY_ALLOCATION,
            component_name="Reported statutory component",
            gross_amount=allocation.gross_total - 1,
            deduction_amount=allocation.total_deductions,
            net_amount=allocation.net_allocation,
            gross_amount_original="999.00",
            deduction_amount_original="100.00",
            net_amount_original="900.00",
            reported_unit=ReportedUnit.NAIRA,
        )
    )
    session.flush()

    findings = validate_import(session, run)
    session.commit()

    assert "COMPONENT_TOTAL_MISMATCH" in {finding.rule_code for finding in findings}


def test_rejection_preserves_records_and_audits_decision(session: Session, tmp_path: Path) -> None:
    seed_states(session)
    path = tmp_path / "reject.csv"
    _write_csv(path, _complete_rows())
    imported = import_allocations_csv(session, _request(path))
    reviewer = _reviewer(session)

    result = reject_import(
        session,
        run_id=uuid.UUID(imported.run_id),
        reviewer_id=reviewer.id,
        reason="Source requires correction.",
    )
    period = session.get(ReportingPeriod, uuid.UUID(imported.reporting_period_id))
    allocations = list(session.scalars(select(StateAllocation)))

    assert result.allocations_approved == 0
    assert period is not None
    assert period.source_status is SourceStatus.REJECTED
    assert period.verification_status is VerificationStatus.REJECTED
    assert period.is_published is False
    assert len(allocations) == 37
    assert all(
        allocation.verification_status is VerificationStatus.REJECTED for allocation in allocations
    )
    audit = session.scalar(select(AuditLog))
    assert audit is not None
    assert audit.action == "import.rejected"
    assert audit.payload["reason"] == "Source requires correction."
