from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from gaiafaac_api.database.enums import UserRole, ValidationSeverity
from gaiafaac_api.database.models import (
    AuditLog,
    ExtractionRun,
    ReportingPeriod,
    SourceDocument,
    State,
    StateAllocation,
    User,
    ValidationResult,
)
from gaiafaac_api.review_schemas import (
    PendingReviewItem,
    ReviewAllocationItem,
    ReviewApproval,
    ReviewFindingItem,
    ReviewPacket,
    ReviewSource,
)

EXPECTED_STATE_COUNT = 37
_BLOCKING = {ValidationSeverity.ERROR, ValidationSeverity.CRITICAL}


def list_active_review_actors(session: Session) -> list[dict[str, object]]:
    users = list(
        session.scalars(
            select(User)
            .where(
                User.is_active.is_(True),
                User.role.in_([UserRole.REVIEWER, UserRole.ADMINISTRATOR]),
            )
            .order_by(User.full_name, User.email)
        )
    )
    return [
        {
            "id": str(user.id),
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role.value,
        }
        for user in users
    ]


def _approval(session: Session, run_id: uuid.UUID) -> AuditLog | None:
    return session.scalar(
        select(AuditLog)
        .where(
            AuditLog.action == "import.approved",
            AuditLog.entity_type == "extraction_run",
            AuditLog.entity_id == run_id,
        )
        .order_by(AuditLog.created_at.desc())
        .limit(1)
    )


def list_pending_reviews(session: Session) -> list[PendingReviewItem]:
    """Real (non-demo), unpublished periods awaiting human action. Metadata only."""
    periods = session.scalars(
        select(ReportingPeriod)
        .where(
            ReportingPeriod.is_demo.is_(False),
            ReportingPeriod.is_published.is_(False),
        )
        .order_by(ReportingPeriod.revenue_month.desc())
    )
    items: list[PendingReviewItem] = []
    for period in periods:
        source = session.scalar(
            select(SourceDocument).where(SourceDocument.reporting_period_id == period.id)
        )
        if source is None:
            continue
        run = session.scalar(
            select(ExtractionRun)
            .where(ExtractionRun.source_document_id == source.id)
            .order_by(ExtractionRun.started_at.desc())
        )
        if run is None:
            continue
        covered = (
            session.scalar(
                select(func.count())
                .select_from(StateAllocation)
                .where(
                    StateAllocation.reporting_period_id == period.id,
                    StateAllocation.is_demo.is_(False),
                )
            )
            or 0
        )
        findings = list(
            session.scalars(
                select(ValidationResult).where(ValidationResult.extraction_run_id == run.id)
            )
        )
        blocking = sum(finding.severity in _BLOCKING for finding in findings)
        approval = _approval(session, run.id)
        items.append(
            PendingReviewItem(
                run_id=str(run.id),
                reporting_label=period.reporting_label,
                revenue_month=period.revenue_month,
                source_organization=source.source_organization,
                status=run.status.value,
                covered_states=covered,
                expected_states=EXPECTED_STATE_COUNT,
                finding_count=len(findings),
                blocking_count=blocking,
                approved=approval is not None,
                approved_by=str(approval.actor_user_id)
                if approval and approval.actor_user_id
                else None,
                created_at=run.started_at,
            )
        )
    return items


def get_review_packet(session: Session, run_id: uuid.UUID) -> ReviewPacket | None:
    """Return the evidence packet an authorized accountant needs to review one import."""
    run = session.get(ExtractionRun, run_id)
    if run is None:
        return None
    source = session.get(SourceDocument, run.source_document_id)
    if source is None or source.reporting_period_id is None or source.is_demo:
        return None
    period = session.get(ReportingPeriod, source.reporting_period_id)
    if period is None or period.is_demo or period.is_published:
        return None

    allocations = list(
        session.execute(
            select(StateAllocation, State)
            .join(State, State.id == StateAllocation.state_id)
            .where(
                StateAllocation.reporting_period_id == period.id,
                StateAllocation.is_demo.is_(False),
            )
            .order_by(State.name)
        )
    )
    findings = list(
        session.scalars(
            select(ValidationResult)
            .where(ValidationResult.extraction_run_id == run.id)
            .order_by(ValidationResult.severity.desc(), ValidationResult.rule_code)
        )
    )
    blocking = sum(finding.severity in _BLOCKING for finding in findings)
    approval = _approval(session, run.id)
    approver = (
        session.get(User, approval.actor_user_id) if approval and approval.actor_user_id else None
    )

    return ReviewPacket(
        run_id=str(run.id),
        reporting_label=period.reporting_label,
        revenue_month=period.revenue_month,
        status=run.status.value,
        source=ReviewSource(
            source_organization=source.source_organization,
            source_url=source.source_url,
            original_filename=source.original_filename,
            sha256=source.sha256,
            publication_date=source.publication_date,
            document_version=source.document_version,
        ),
        covered_states=len({allocation.state_id for allocation, _state in allocations}),
        expected_states=EXPECTED_STATE_COUNT,
        finding_count=len(findings),
        blocking_count=blocking,
        allocations=[
            ReviewAllocationItem(
                state_name=state.name,
                state_code=state.code,
                gross_total=str(allocation.gross_total)
                if allocation.gross_total is not None
                else None,
                total_deductions=(
                    str(allocation.total_deductions)
                    if allocation.total_deductions is not None
                    else None
                ),
                net_allocation=(
                    str(allocation.net_allocation)
                    if allocation.net_allocation is not None
                    else None
                ),
                reported_unit=allocation.reported_unit.value,
                verification_status=allocation.verification_status.value,
                extraction_confidence=(
                    str(allocation.extraction_confidence)
                    if allocation.extraction_confidence is not None
                    else None
                ),
            )
            for allocation, state in allocations
        ],
        findings=[
            ReviewFindingItem(
                rule_code=finding.rule_code,
                severity=finding.severity.value,
                message=finding.message,
                details=finding.details,
                outcome=finding.outcome.value,
            )
            for finding in findings
        ],
        approval=(
            ReviewApproval(
                actor_user_id=str(approval.actor_user_id) if approval.actor_user_id else None,
                actor_name=approver.full_name if approver else None,
                created_at=approval.created_at,
                note=(approval.payload or {}).get("review_note"),
            )
            if approval is not None
            else None
        ),
    )
