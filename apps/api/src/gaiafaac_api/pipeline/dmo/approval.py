from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime, time

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from gaiafaac_api.database.debt_models import DebtKind, StateDebtRecord
from gaiafaac_api.database.enums import (
    ProcessingStatus,
    SourceStatus,
    UserRole,
    VerificationStatus,
)
from gaiafaac_api.database.models import AuditLog, SourceDocument, State, User
from gaiafaac_api.pipeline.errors import ApprovalError
from gaiafaac_api.services.fiscal_domain_claims import publish_domain_claim


@dataclass(frozen=True)
class DebtApprovalResult:
    source_document_id: str
    debt_kind: str
    as_of_date: str
    records_affected: int
    published: bool
    proof_gaia_ids: tuple[str, ...] = ()


def _fiscal_period(as_of_date: date) -> str:
    quarter = ((as_of_date.month - 1) // 3) + 1
    return f"{as_of_date.year}Q{quarter}"


def _reviewer(session: Session, reviewer_id: uuid.UUID) -> User:
    reviewer = session.get(User, reviewer_id)
    if reviewer is None:
        raise ApprovalError("Reviewer does not exist")
    if not reviewer.is_active or reviewer.role not in {
        UserRole.REVIEWER,
        UserRole.ADMINISTRATOR,
    }:
        raise ApprovalError("DMO debt approval requires an active reviewer or administrator")
    return reviewer


def _context(
    session: Session,
    *,
    source_document_id: uuid.UUID,
    reviewer_id: uuid.UUID,
) -> tuple[SourceDocument, User, list[StateDebtRecord], DebtKind]:
    source = session.get(SourceDocument, source_document_id)
    if source is None:
        raise ApprovalError("DMO source document does not exist")
    if source.is_demo:
        raise ApprovalError("Demo debt evidence can never be approved or published")
    if "Debt Management Office" not in source.source_organization:
        raise ApprovalError("Source document is not registered as DMO evidence")

    reviewer = _reviewer(session, reviewer_id)
    records = list(
        session.scalars(
            select(StateDebtRecord)
            .where(StateDebtRecord.source_document_id == source.id)
            .order_by(StateDebtRecord.state_id)
        )
    )
    if not records:
        raise ApprovalError("DMO source has no staged debt records")

    expected_count = session.scalar(select(func.count()).select_from(State)) or 0
    state_ids = {record.state_id for record in records}
    if expected_count != 37 or len(records) != 37 or len(state_ids) != expected_count:
        raise ApprovalError("DMO source must contain all 36 states and the FCT exactly once")

    debt_kinds = {record.debt_kind for record in records}
    as_of_dates = {record.as_of_date for record in records}
    currencies = {record.currency for record in records}
    if len(debt_kinds) != 1 or len(as_of_dates) != 1 or len(currencies) != 1:
        raise ApprovalError("DMO source records must share one debt kind, as-of date, and currency")

    debt_kind = debt_kinds.pop()
    as_of_date = as_of_dates.pop()
    currency = currencies.pop()
    expected_currency = "NGN" if debt_kind is DebtKind.DOMESTIC else "USD"
    if currency != expected_currency:
        raise ApprovalError(
            f"DMO {debt_kind.value} debt records must use {expected_currency}, found {currency}"
        )
    expected_version = f"{debt_kind.value}-{as_of_date.isoformat()}"
    if source.document_version != expected_version:
        raise ApprovalError("DMO source version does not match staged debt kind and as-of date")
    if any(record.is_demo for record in records):
        raise ApprovalError("Demo debt evidence can never be approved or published")

    return source, reviewer, records, debt_kind


def approve_debt_source(
    session: Session,
    *,
    source_document_id: uuid.UUID,
    reviewer_id: uuid.UUID,
) -> DebtApprovalResult:
    """Human-verify complete DMO debt evidence without publishing ledger claims."""

    source, reviewer, records, debt_kind = _context(
        session,
        source_document_id=source_document_id,
        reviewer_id=reviewer_id,
    )
    as_of_date = records[0].as_of_date

    if (
        source.source_status is SourceStatus.APPROVED
        and source.processing_status is ProcessingStatus.COMPLETED
        and all(
            record.verification_status is VerificationStatus.HUMAN_VERIFIED for record in records
        )
    ):
        return DebtApprovalResult(
            source_document_id=str(source.id),
            debt_kind=debt_kind.value,
            as_of_date=as_of_date.isoformat(),
            records_affected=len(records),
            published=False,
        )

    if source.source_status is not SourceStatus.READY_FOR_REVIEW:
        raise ApprovalError("DMO source is not awaiting explicit review")
    if source.processing_status is not ProcessingStatus.READY_FOR_REVIEW:
        raise ApprovalError("DMO source processing is not ready for review")
    if any(record.is_published for record in records):
        raise ApprovalError("Unapproved DMO debt records must not already be published")
    if any(
        record.verification_status is not VerificationStatus.REQUIRES_REVIEW for record in records
    ):
        raise ApprovalError("Every DMO debt record must be awaiting review before approval")

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
            action="debt.approved",
            entity_type="source_document",
            entity_id=source.id,
            payload={
                "debt_kind": debt_kind.value,
                "as_of_date": as_of_date.isoformat(),
                "records_approved": len(records),
                "published": False,
            },
        )
    )
    session.commit()
    return DebtApprovalResult(
        source_document_id=str(source.id),
        debt_kind=debt_kind.value,
        as_of_date=as_of_date.isoformat(),
        records_affected=len(records),
        published=False,
    )


def publish_debt_source(
    session: Session,
    *,
    source_document_id: uuid.UUID,
    reviewer_id: uuid.UUID,
) -> DebtApprovalResult:
    """Publish approved DMO observations into immutable governed debt claims."""

    source, reviewer, records, debt_kind = _context(
        session,
        source_document_id=source_document_id,
        reviewer_id=reviewer_id,
    )
    as_of_date = records[0].as_of_date

    if source.source_status is not SourceStatus.APPROVED:
        raise ApprovalError("Only approved DMO debt sources can be published")
    if source.processing_status is not ProcessingStatus.COMPLETED:
        raise ApprovalError("DMO source processing must be completed before publication")
    if any(
        record.verification_status is not VerificationStatus.HUMAN_VERIFIED for record in records
    ):
        raise ApprovalError("Every DMO debt record must be human-verified before publication")

    if all(record.is_published for record in records):
        return DebtApprovalResult(
            source_document_id=str(source.id),
            debt_kind=debt_kind.value,
            as_of_date=as_of_date.isoformat(),
            records_affected=len(records),
            published=True,
        )
    if any(record.is_published for record in records):
        raise ApprovalError("DMO source is only partially published; manual investigation required")

    published_at = datetime.now(UTC)
    effective_at = datetime.combine(as_of_date, time.min, tzinfo=UTC)
    fiscal_period = _fiscal_period(as_of_date)
    metric = "domestic_debt_stock" if debt_kind is DebtKind.DOMESTIC else "external_debt_stock"
    proof_ids: list[str] = []
    try:
        for record in records:
            proof = publish_domain_claim(
                session,
                domain="debt",
                state_id=record.state_id,
                source_document_id=source.id,
                fiscal_period=fiscal_period,
                metric=metric,
                value=record.debt_amount,
                value_text=record.debt_amount_original,
                unit="currency",
                currency=record.currency,
                effective_at=effective_at,
                published_at=published_at,
                source_page=record.source_page,
                source_table=record.source_table,
                extraction_method="dmo_pdf_deterministic_v1",
                human_reviewed=True,
                reconciled=None,
            )
            proof_ids.append(proof.gaia_id)
            record.is_published = True
            record.published_at = published_at

        session.add(
            AuditLog(
                actor_user_id=reviewer.id,
                action="debt.published",
                entity_type="source_document",
                entity_id=source.id,
                payload={
                    "debt_kind": debt_kind.value,
                    "as_of_date": as_of_date.isoformat(),
                    "fiscal_period": fiscal_period,
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

    return DebtApprovalResult(
        source_document_id=str(source.id),
        debt_kind=debt_kind.value,
        as_of_date=as_of_date.isoformat(),
        records_affected=len(records),
        published=True,
        proof_gaia_ids=tuple(proof_ids),
    )
