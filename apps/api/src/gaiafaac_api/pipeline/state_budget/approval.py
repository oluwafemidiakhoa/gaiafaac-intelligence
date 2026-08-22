from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime, time

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.budget_models import BudgetMetric, StateBudgetRecord
from gaiafaac_api.database.enums import (
    ProcessingStatus,
    SourceStatus,
    UserRole,
    VerificationStatus,
)
from gaiafaac_api.database.models import AuditLog, SourceDocument, State, User
from gaiafaac_api.pipeline.errors import ApprovalError
from gaiafaac_api.services.fiscal_domain_claims import publish_domain_claim

_VERSION_RE = re.compile(r"^approved-budget-(?P<state_code>[a-z]{2})-(?P<year>20\d{2})$")


@dataclass(frozen=True)
class BudgetApprovalResult:
    source_document_id: str
    state_code: str
    fiscal_year: int
    records_affected: int
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
        raise ApprovalError(
            "State-budget approval requires an active reviewer or administrator"
        )
    return reviewer


def _context(
    session: Session,
    *,
    source_document_id: uuid.UUID,
    reviewer_id: uuid.UUID,
) -> tuple[SourceDocument, User, State, list[StateBudgetRecord], int]:
    source = session.get(SourceDocument, source_document_id)
    if source is None:
        raise ApprovalError("State-budget source document does not exist")
    if source.is_demo:
        raise ApprovalError("Demo budget evidence can never be approved or published")

    reviewer = _reviewer(session, reviewer_id)
    records = list(
        session.scalars(
            select(StateBudgetRecord)
            .where(StateBudgetRecord.source_document_id == source.id)
            .order_by(StateBudgetRecord.metric)
        )
    )
    if not records:
        raise ApprovalError("State-budget source has no staged records")

    state_ids = {record.state_id for record in records}
    fiscal_years = {record.fiscal_year for record in records}
    currencies = {record.currency for record in records}
    metrics = {record.metric for record in records}
    extraction_methods = {record.extraction_method for record in records}
    if len(state_ids) != 1:
        raise ApprovalError("State-budget source records must belong to exactly one state")
    if len(fiscal_years) != 1:
        raise ApprovalError("State-budget source records must share one fiscal year")
    if currencies != {"NGN"}:
        raise ApprovalError("State-budget source records must all be reported in NGN")
    if metrics != set(BudgetMetric) or len(records) != len(BudgetMetric):
        raise ApprovalError("State-budget source must contain the complete governed metric set")
    if len(extraction_methods) != 1 or not next(iter(extraction_methods)).strip():
        raise ApprovalError("State-budget source records must share one extraction method")
    if any(record.source_page is None or not record.source_table for record in records):
        raise ApprovalError("Every state-budget record must retain source page and table provenance")
    if any(record.is_demo for record in records):
        raise ApprovalError("Demo budget evidence can never be approved or published")

    fiscal_year = fiscal_years.pop()
    state = session.get(State, state_ids.pop())
    if state is None:
        raise ApprovalError("State-budget source references an unknown state")
    version = _VERSION_RE.fullmatch(source.document_version or "")
    if version is None:
        raise ApprovalError("State-budget source version is invalid")
    if version.group("state_code").upper() != state.code.upper():
        raise ApprovalError("State-budget source version does not match the staged state")
    if int(version.group("year")) != fiscal_year:
        raise ApprovalError("State-budget source version does not match the staged fiscal year")
    if source.source_organization != f"{state.name} State Government":
        raise ApprovalError("State-budget source organization does not match the staged state")

    return source, reviewer, state, records, fiscal_year


def approve_budget_source(
    session: Session,
    *,
    source_document_id: uuid.UUID,
    reviewer_id: uuid.UUID,
) -> BudgetApprovalResult:
    """Human-verify a complete approved state budget without publishing claims."""

    source, reviewer, state, records, fiscal_year = _context(
        session,
        source_document_id=source_document_id,
        reviewer_id=reviewer_id,
    )

    if (
        source.source_status is SourceStatus.APPROVED
        and source.processing_status is ProcessingStatus.COMPLETED
        and all(
            record.verification_status is VerificationStatus.HUMAN_VERIFIED
            for record in records
        )
    ):
        return BudgetApprovalResult(
            source_document_id=str(source.id),
            state_code=state.code,
            fiscal_year=fiscal_year,
            records_affected=len(records),
            published=False,
        )

    if source.source_status is not SourceStatus.READY_FOR_REVIEW:
        raise ApprovalError("State-budget source is not awaiting explicit review")
    if source.processing_status is not ProcessingStatus.READY_FOR_REVIEW:
        raise ApprovalError("State-budget source processing is not ready for review")
    if any(record.is_published for record in records):
        raise ApprovalError("Unapproved state-budget records must not already be published")
    if any(
        record.verification_status is not VerificationStatus.REQUIRES_REVIEW
        for record in records
    ):
        raise ApprovalError(
            "Every state-budget record must be awaiting review before approval"
        )

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
            action="budget.approved",
            entity_type="source_document",
            entity_id=source.id,
            payload={
                "state_code": state.code,
                "fiscal_year": fiscal_year,
                "records_approved": len(records),
                "published": False,
            },
        )
    )
    session.commit()
    return BudgetApprovalResult(
        source_document_id=str(source.id),
        state_code=state.code,
        fiscal_year=fiscal_year,
        records_affected=len(records),
        published=False,
    )


def publish_budget_source(
    session: Session,
    *,
    source_document_id: uuid.UUID,
    reviewer_id: uuid.UUID,
) -> BudgetApprovalResult:
    """Publish an approved state budget into immutable governed budget claims."""

    source, reviewer, state, records, fiscal_year = _context(
        session,
        source_document_id=source_document_id,
        reviewer_id=reviewer_id,
    )

    if source.source_status is not SourceStatus.APPROVED:
        raise ApprovalError("Only approved state-budget sources can be published")
    if source.processing_status is not ProcessingStatus.COMPLETED:
        raise ApprovalError("State-budget source processing must be completed before publication")
    if any(
        record.verification_status is not VerificationStatus.HUMAN_VERIFIED
        for record in records
    ):
        raise ApprovalError(
            "Every state-budget record must be human-verified before publication"
        )

    if all(record.is_published for record in records):
        return BudgetApprovalResult(
            source_document_id=str(source.id),
            state_code=state.code,
            fiscal_year=fiscal_year,
            records_affected=len(records),
            published=True,
        )
    if any(record.is_published for record in records):
        raise ApprovalError(
            "State-budget source is only partially published; manual investigation required"
        )

    published_at = datetime.now(UTC)
    effective_at = datetime.combine(date(fiscal_year, 1, 1), time.min, tzinfo=UTC)
    proof_ids: list[str] = []
    try:
        for record in records:
            proof = publish_domain_claim(
                session,
                domain="budget",
                state_id=record.state_id,
                source_document_id=source.id,
                fiscal_period=str(fiscal_year),
                metric=record.metric.value,
                value=record.amount,
                value_text=record.amount_original,
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
                action="budget.published",
                entity_type="source_document",
                entity_id=source.id,
                payload={
                    "state_code": state.code,
                    "fiscal_year": fiscal_year,
                    "records_published": len(records),
                    "proof_count": len(proof_ids),
                    "published": True,
                },
            )
        )
        session.commit()
    except Exception:
        session.rollback()
        raise

    return BudgetApprovalResult(
        source_document_id=str(source.id),
        state_code=state.code,
        fiscal_year=fiscal_year,
        records_affected=len(records),
        published=True,
        proof_gaia_ids=tuple(proof_ids),
    )
