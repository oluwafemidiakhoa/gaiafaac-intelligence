from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.enums import ExtractionStatus, UserRole, ValidationSeverity
from gaiafaac_api.database.models import (
    AuditLog,
    ExtractionRun,
    NationalDistribution,
    ReportingPeriod,
    SourceDocument,
    User,
    ValidationResult,
)
from gaiafaac_api.pipeline.national_distribution import reconciliation_for_distribution

_BLOCKING = {ValidationSeverity.ERROR, ValidationSeverity.CRITICAL}


def _value(value: Decimal | None) -> str | None:
    return str(value) if value is not None else None


def _distribution_for_run(
    session: Session, run: ExtractionRun
) -> NationalDistribution | None:
    configuration = run.configuration or {}
    if configuration.get("scope") != "national_distribution":
        return None
    raw_id = configuration.get("distribution_id")
    if not raw_id:
        return None
    try:
        distribution_id = uuid.UUID(str(raw_id))
    except ValueError:
        return None
    return session.get(NationalDistribution, distribution_id)


def _findings(session: Session, run_id: uuid.UUID) -> list[ValidationResult]:
    return list(
        session.scalars(
            select(ValidationResult)
            .where(ValidationResult.extraction_run_id == run_id)
            .order_by(ValidationResult.created_at, ValidationResult.rule_code)
        )
    )


def _approval(session: Session, distribution_id: uuid.UUID) -> AuditLog | None:
    return session.scalar(
        select(AuditLog)
        .where(
            AuditLog.action == "national_distribution.approved",
            AuditLog.entity_type == "national_distribution",
            AuditLog.entity_id == distribution_id,
        )
        .order_by(AuditLog.created_at.desc())
        .limit(1)
    )


def list_active_national_actors(session: Session) -> list[dict[str, object]]:
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


def list_pending_national_reviews(session: Session) -> list[dict[str, object]]:
    runs = list(
        session.scalars(
            select(ExtractionRun)
            .where(ExtractionRun.status.in_([ExtractionStatus.REQUIRES_REVIEW, ExtractionStatus.COMPLETED]))
            .order_by(ExtractionRun.created_at.desc())
        )
    )
    items: list[dict[str, object]] = []
    for run in runs:
        distribution = _distribution_for_run(session, run)
        if distribution is None or distribution.is_published:
            continue
        period = session.get(ReportingPeriod, distribution.reporting_period_id)
        source = session.get(SourceDocument, distribution.source_document_id)
        if period is None or source is None:
            continue
        findings = _findings(session, run.id)
        approval = _approval(session, distribution.id)
        items.append(
            {
                "run_id": str(run.id),
                "distribution_id": str(distribution.id),
                "reporting_label": period.reporting_label,
                "disbursement_month": (
                    period.disbursement_month or period.revenue_month
                ).isoformat(),
                "allocation_period_month": (
                    period.allocation_period_month.isoformat()
                    if period.allocation_period_month
                    else None
                ),
                "source_organization": source.source_organization,
                "verification_status": distribution.verification_status.value,
                "pipeline_status": run.status.value,
                "finding_count": len(findings),
                "blocking_count": sum(item.severity in _BLOCKING for item in findings),
                "approved": approval is not None,
                "approved_by": str(approval.actor_user_id) if approval and approval.actor_user_id else None,
                "created_at": run.created_at.isoformat() if run.created_at else None,
            }
        )
    return items


def get_national_review_packet(
    session: Session, run_id: uuid.UUID
) -> dict[str, object] | None:
    run = session.get(ExtractionRun, run_id)
    if run is None:
        return None
    distribution = _distribution_for_run(session, run)
    if distribution is None:
        return None
    period = session.get(ReportingPeriod, distribution.reporting_period_id)
    source = session.get(SourceDocument, distribution.source_document_id)
    if period is None or source is None:
        return None
    findings = _findings(session, run.id)
    reconciliation = reconciliation_for_distribution(distribution, run)
    configuration = run.configuration or {}
    approval = _approval(session, distribution.id)
    approver = session.get(User, approval.actor_user_id) if approval and approval.actor_user_id else None
    return {
        "run_id": str(run.id),
        "distribution_id": str(distribution.id),
        "reporting_period_id": str(period.id),
        "reporting_label": period.reporting_label,
        "disbursement_month": (period.disbursement_month or period.revenue_month).isoformat(),
        "allocation_period_month": (
            period.allocation_period_month.isoformat() if period.allocation_period_month else None
        ),
        "verification_status": distribution.verification_status.value,
        "pipeline_status": run.status.value,
        "published": distribution.is_published,
        "source": {
            "source_organization": source.source_organization,
            "source_url": source.source_url,
            "original_filename": source.original_filename,
            "sha256": source.sha256,
            "publication_date": source.publication_date.isoformat() if source.publication_date else None,
            "source_type": configuration.get("source_type"),
            "source_authority": configuration.get("source_authority"),
            "canonical_source_status": configuration.get("canonical_source_status"),
        },
        "amounts": {
            "reported_unit": distribution.reported_unit.value,
            "net_distributable_amount": _value(distribution.net_distributable_amount),
            "federal_amount": _value(distribution.federal_amount),
            "states_amount": _value(distribution.states_amount),
            "local_governments_amount": _value(distribution.local_governments_amount),
            "derivation_amount": _value(distribution.derivation_amount),
            "vat_amount": _value(distribution.vat_amount),
            "statutory_amount": _value(distribution.statutory_amount),
            "gross_amount": _value(distribution.gross_amount),
            "deductions_amount": _value(distribution.deductions_amount),
        },
        "reconciliation": {
            "status": reconciliation.status,
            "component_total": _value(reconciliation.component_total),
            "variance": _value(reconciliation.variance),
            "tolerance": _value(reconciliation.tolerance),
            "derivation_treatment": reconciliation.derivation_treatment,
            "note": reconciliation.note,
        },
        "states_scope": configuration.get("states_scope"),
        "findings": [
            {
                "rule_code": finding.rule_code,
                "severity": finding.severity.value,
                "message": finding.message,
                "details": finding.details,
                "tolerance": _value(finding.tolerance),
            }
            for finding in findings
        ],
        "blocking_count": sum(item.severity in _BLOCKING for item in findings),
        "approval": (
            {
                "actor_user_id": str(approval.actor_user_id) if approval.actor_user_id else None,
                "actor_name": approver.full_name if approver else None,
                "created_at": approval.created_at.isoformat(),
                "note": (approval.payload or {}).get("review_note"),
            }
            if approval is not None
            else None
        ),
    }
