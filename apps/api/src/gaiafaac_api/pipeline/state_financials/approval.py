from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime, time
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.enums import (
    ProcessingStatus,
    SourceStatus,
    UserRole,
    VerificationStatus,
)
from gaiafaac_api.database.liability_models import LiabilityMetric, StateLiabilityRecord
from gaiafaac_api.database.models import AuditLog, SourceDocument, State, User
from gaiafaac_api.pipeline.errors import ApprovalError
from gaiafaac_api.services.fiscal_domain_claims import publish_domain_claim

_VERSION_RE = re.compile(
    r"^state-financial-(?P<kind>contractor-arrears-register)-"
    r"(?P<state_code>[a-z]{2})-(?P<year>20\d{2})$"
)
_SUPPORTED_CONTRACT = ("contractor-arrears-register", "OY", 2021)


@dataclass(frozen=True)
class StateLiabilityApprovalResult:
    source_document_id: str
    state_code: str
    fiscal_year: int
    records_approved: int
    numeric_metrics: int
    unreported_metrics: int
    reconciliation_checked: bool
    published: bool
    proof_gaia_ids: tuple[str, ...] = ()


def _reviewer(session: Session, reviewer_id: uuid.UUID) -> User:
    reviewer = session.get(User, reviewer_id)
    if reviewer is None:
        raise ApprovalError("Reviewer does not exist")
    if not reviewer.is_active or reviewer.role not in {
        UserRole.REVIEWER,
        UserRole.ADMINISTRATOR,
    }:
        raise ApprovalError("State-liability approval requires an active reviewer or administrator")
    return reviewer


def _context(
    session: Session,
    *,
    source_document_id: uuid.UUID,
    reviewer_id: uuid.UUID,
) -> tuple[SourceDocument, User, State, list[StateLiabilityRecord], int]:
    source = session.get(SourceDocument, source_document_id)
    if source is None:
        raise ApprovalError("State-liability source document does not exist")
    if source.is_demo:
        raise ApprovalError("Demo liability evidence can never be approved or published")

    reviewer = _reviewer(session, reviewer_id)
    records = list(
        session.scalars(
            select(StateLiabilityRecord)
            .where(StateLiabilityRecord.source_document_id == source.id)
            .order_by(StateLiabilityRecord.metric)
        )
    )
    if not records:
        raise ApprovalError("State-liability source has no staged records")

    state_ids = {record.state_id for record in records}
    fiscal_years = {record.fiscal_year for record in records}
    currencies = {record.currency for record in records}
    metrics = {record.metric for record in records}
    extraction_methods = {record.extraction_method for record in records}
    source_pages = {record.source_page for record in records}
    source_tables = {record.source_table for record in records}

    if len(state_ids) != 1:
        raise ApprovalError("State-liability records must belong to exactly one state")
    if len(fiscal_years) != 1:
        raise ApprovalError("State-liability records must share one fiscal year")
    if currencies != {"NGN"}:
        raise ApprovalError("State-liability records must all be reported in NGN")
    if metrics != set(LiabilityMetric) or len(records) != len(LiabilityMetric):
        raise ApprovalError("State-liability source must contain the complete governed metric set")
    if len(extraction_methods) != 1 or not next(iter(extraction_methods)).strip():
        raise ApprovalError("State-liability records must share one extraction method")
    if len(source_pages) != 1 or next(iter(source_pages)) < 1:
        raise ApprovalError("State-liability records must retain one valid summary source page")
    if len(source_tables) != 1 or not next(iter(source_tables)).strip():
        raise ApprovalError("State-liability records must retain one summary source table")
    if any(record.is_demo for record in records):
        raise ApprovalError("Demo liability evidence can never be approved or published")

    fiscal_year = fiscal_years.pop()
    state = session.get(State, state_ids.pop())
    if state is None:
        raise ApprovalError("State-liability source references an unknown state")

    version = _VERSION_RE.fullmatch(source.document_version or "")
    if version is None:
        raise ApprovalError("State-liability source version is invalid")
    contract = (
        version.group("kind"),
        version.group("state_code").upper(),
        int(version.group("year")),
    )
    if contract != _SUPPORTED_CONTRACT:
        raise ApprovalError(
            "No governed state-liability approval contract is registered for this source"
        )
    if contract[1] != state.code.upper() or contract[2] != fiscal_year:
        raise ApprovalError("State-liability source version does not match the staged records")
    if source.source_organization != f"{state.name} State Government":
        raise ApprovalError("State-liability source organization does not match the staged state")

    return source, reviewer, state, records, fiscal_year


def _validate_reconciliation(records: list[StateLiabilityRecord]) -> None:
    by_metric = {record.metric: record for record in records}

    salary = by_metric[LiabilityMetric.SALARY_ARREARS]
    if salary.amount is not None or " ".join(salary.amount_text.split()) != "-":
        raise ApprovalError(
            "Salary arrears must remain unreported when the official source uses a dash"
        )

    numeric_metrics = (
        LiabilityMetric.CONTRACTOR_ARREARS,
        LiabilityMetric.PENSIONS_AND_GRATUITY_ARREARS,
        LiabilityMetric.OTHER_JUDGMENT_ARREARS,
        LiabilityMetric.TOTAL_DOMESTIC_ARREARS,
    )
    if any(by_metric[metric].amount is None for metric in numeric_metrics):
        raise ApprovalError("All explicitly reported liability totals must remain numeric")

    contractor = Decimal(by_metric[LiabilityMetric.CONTRACTOR_ARREARS].amount)
    pensions = Decimal(by_metric[LiabilityMetric.PENSIONS_AND_GRATUITY_ARREARS].amount)
    judgment = Decimal(by_metric[LiabilityMetric.OTHER_JUDGMENT_ARREARS].amount)
    total = Decimal(by_metric[LiabilityMetric.TOTAL_DOMESTIC_ARREARS].amount)
    expected_total = contractor + pensions + judgment
    if total != expected_total:
        raise ApprovalError(
            "State-liability reconciliation failed for total domestic arrears: "
            f"actual={total}, expected={expected_total}"
        )


def approve_state_liability_source(
    session: Session,
    *,
    source_document_id: uuid.UUID,
    reviewer_id: uuid.UUID,
) -> StateLiabilityApprovalResult:
    """Human-verify one complete liability evidence package without publishing claims."""

    source, reviewer, state, records, fiscal_year = _context(
        session,
        source_document_id=source_document_id,
        reviewer_id=reviewer_id,
    )
    _validate_reconciliation(records)

    if (
        source.source_status is SourceStatus.APPROVED
        and source.processing_status is ProcessingStatus.COMPLETED
        and all(
            record.verification_status is VerificationStatus.HUMAN_VERIFIED for record in records
        )
    ):
        return StateLiabilityApprovalResult(
            source_document_id=str(source.id),
            state_code=state.code,
            fiscal_year=fiscal_year,
            records_approved=len(records),
            numeric_metrics=sum(record.amount is not None for record in records),
            unreported_metrics=sum(record.amount is None for record in records),
            reconciliation_checked=True,
            published=all(record.is_published for record in records),
        )

    if source.source_status is not SourceStatus.READY_FOR_REVIEW:
        raise ApprovalError("State-liability source is not awaiting explicit review")
    if source.processing_status is not ProcessingStatus.READY_FOR_REVIEW:
        raise ApprovalError("State-liability source processing is not ready for review")
    if any(record.is_published for record in records):
        raise ApprovalError("Unapproved state-liability records must not already be published")
    if any(
        record.verification_status is not VerificationStatus.REQUIRES_REVIEW for record in records
    ):
        raise ApprovalError("Every state-liability record must be awaiting review before approval")

    reviewed_at = datetime.now(UTC)
    for record in records:
        record.verification_status = VerificationStatus.HUMAN_VERIFIED
        record.reviewed_by = reviewer.id
        record.reviewed_at = reviewed_at

    source.source_status = SourceStatus.APPROVED
    source.processing_status = ProcessingStatus.COMPLETED
    session.add(
        AuditLog(
            actor_user_id=reviewer.id,
            action="state_liability.approved",
            entity_type="source_document",
            entity_id=source.id,
            payload={
                "state_code": state.code,
                "fiscal_year": fiscal_year,
                "records_approved": len(records),
                "numeric_metrics": sum(record.amount is not None for record in records),
                "unreported_metrics": sum(record.amount is None for record in records),
                "reconciliation_checked": True,
                "published": False,
            },
        )
    )
    session.commit()

    return StateLiabilityApprovalResult(
        source_document_id=str(source.id),
        state_code=state.code,
        fiscal_year=fiscal_year,
        records_approved=len(records),
        numeric_metrics=sum(record.amount is not None for record in records),
        unreported_metrics=sum(record.amount is None for record in records),
        reconciliation_checked=True,
        published=False,
    )


def publish_state_liability_source(
    session: Session,
    *,
    source_document_id: uuid.UUID,
    reviewer_id: uuid.UUID,
) -> StateLiabilityApprovalResult:
    """Publish a human-approved liability package into immutable governed claims."""

    source, reviewer, state, records, fiscal_year = _context(
        session,
        source_document_id=source_document_id,
        reviewer_id=reviewer_id,
    )
    _validate_reconciliation(records)

    if source.source_status is not SourceStatus.APPROVED:
        raise ApprovalError("Only approved state-liability sources can be published")
    if source.processing_status is not ProcessingStatus.COMPLETED:
        raise ApprovalError("State-liability source processing must be completed before publication")
    if any(
        record.verification_status is not VerificationStatus.HUMAN_VERIFIED for record in records
    ):
        raise ApprovalError("Every state-liability record must be human-verified before publication")

    if all(record.is_published for record in records):
        return StateLiabilityApprovalResult(
            source_document_id=str(source.id),
            state_code=state.code,
            fiscal_year=fiscal_year,
            records_approved=len(records),
            numeric_metrics=sum(record.amount is not None for record in records),
            unreported_metrics=sum(record.amount is None for record in records),
            reconciliation_checked=True,
            published=True,
        )
    if any(record.is_published for record in records):
        raise ApprovalError(
            "State-liability source is only partially published; manual investigation required"
        )

    published_at = datetime.now(UTC)
    effective_at = datetime.combine(date(fiscal_year, 12, 31), time.max, tzinfo=UTC)
    proof_ids: list[str] = []
    try:
        for record in records:
            proof = publish_domain_claim(
                session,
                domain="liabilities",
                state_id=record.state_id,
                source_document_id=source.id,
                fiscal_period=str(fiscal_year),
                metric=record.metric.value,
                value=record.amount,
                value_text=record.amount_text,
                unit="currency",
                currency="NGN",
                effective_at=effective_at,
                published_at=published_at,
                source_page=record.source_page,
                source_table=record.source_table,
                extraction_method=record.extraction_method,
                human_reviewed=True,
                reconciled=True,
            )
            proof_ids.append(proof.gaia_id)
            record.is_published = True
            record.published_at = published_at

        session.add(
            AuditLog(
                actor_user_id=reviewer.id,
                action="state_liability.published",
                entity_type="source_document",
                entity_id=source.id,
                payload={
                    "state_code": state.code,
                    "fiscal_year": fiscal_year,
                    "records_published": len(records),
                    "numeric_metrics": sum(record.amount is not None for record in records),
                    "unreported_metrics": sum(record.amount is None for record in records),
                    "proof_count": len(proof_ids),
                    "published": True,
                },
            )
        )
        session.commit()
    except Exception:
        session.rollback()
        raise

    return StateLiabilityApprovalResult(
        source_document_id=str(source.id),
        state_code=state.code,
        fiscal_year=fiscal_year,
        records_approved=len(records),
        numeric_metrics=sum(record.amount is not None for record in records),
        unreported_metrics=sum(record.amount is None for record in records),
        reconciliation_checked=True,
        published=True,
        proof_gaia_ids=tuple(proof_ids),
    )
