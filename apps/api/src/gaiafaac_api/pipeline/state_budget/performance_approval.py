from __future__ import annotations

import re
import uuid
from calendar import monthrange
from dataclasses import dataclass
from datetime import UTC, date, datetime, time
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.budget_models import (
    BudgetPerformanceMetric,
    StateBudgetPerformanceRecord,
)
from gaiafaac_api.database.enums import (
    ProcessingStatus,
    SourceStatus,
    UserRole,
    VerificationStatus,
)
from gaiafaac_api.database.ledger_models import FiscalClaim
from gaiafaac_api.database.models import AuditLog, SourceDocument, State, User
from gaiafaac_api.pipeline.errors import ApprovalError
from gaiafaac_api.services.fiscal_domain_claims import publish_domain_claim

_VERSION_RE = re.compile(
    r"^budget-performance-(?P<state_code>[a-z]{2})-(?P<year>20\d{2})-q(?P<quarter>[1-4])$"
)

PUBLISHABLE_EXPENDITURE_METRICS = frozenset(
    {
        BudgetPerformanceMetric.RECURRENT_EXPENDITURE,
        BudgetPerformanceMetric.PERSONNEL_COST,
        BudgetPerformanceMetric.OTHER_RECURRENT_COSTS,
        BudgetPerformanceMetric.OVERHEAD_COST,
        BudgetPerformanceMetric.OTHER_RECURRENT,
        BudgetPerformanceMetric.CAPITAL_EXPENDITURE,
        BudgetPerformanceMetric.TOTAL_EXPENDITURE,
    }
)

_BUDGET_ALIGNMENT_METRICS: dict[BudgetPerformanceMetric, str] = {
    BudgetPerformanceMetric.RECURRENT_EXPENDITURE: "recurrent_expenditure",
    BudgetPerformanceMetric.PERSONNEL_COST: "personnel_cost",
    BudgetPerformanceMetric.CAPITAL_EXPENDITURE: "capital_expenditure",
    BudgetPerformanceMetric.TOTAL_EXPENDITURE: "total_expenditure",
}


@dataclass(frozen=True)
class BudgetPerformanceApprovalResult:
    source_document_id: str
    state_code: str
    fiscal_year: int
    quarter: int
    records_affected: int
    claims_published: int
    cross_source_budget_claims_checked: int
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
            "Budget-performance approval requires an active reviewer or administrator"
        )
    return reviewer


def _context(
    session: Session,
    *,
    source_document_id: uuid.UUID,
    reviewer_id: uuid.UUID,
) -> tuple[
    SourceDocument,
    User,
    State,
    list[StateBudgetPerformanceRecord],
    int,
    int,
]:
    source = session.get(SourceDocument, source_document_id)
    if source is None:
        raise ApprovalError("Budget-performance source document does not exist")
    if source.is_demo:
        raise ApprovalError("Demo performance evidence can never be approved or published")

    reviewer = _reviewer(session, reviewer_id)
    records = list(
        session.scalars(
            select(StateBudgetPerformanceRecord)
            .where(StateBudgetPerformanceRecord.source_document_id == source.id)
            .order_by(StateBudgetPerformanceRecord.metric)
        )
    )
    if not records:
        raise ApprovalError("Budget-performance source has no staged records")

    state_ids = {record.state_id for record in records}
    fiscal_years = {record.fiscal_year for record in records}
    quarters = {record.quarter for record in records}
    currencies = {record.currency for record in records}
    metrics = {record.metric for record in records}
    extraction_methods = {record.extraction_method for record in records}
    if len(state_ids) != 1:
        raise ApprovalError("Budget-performance records must belong to exactly one state")
    if len(fiscal_years) != 1 or len(quarters) != 1:
        raise ApprovalError("Budget-performance records must share one fiscal period")
    if currencies != {"NGN"}:
        raise ApprovalError("Budget-performance records must all be reported in NGN")
    if metrics != set(BudgetPerformanceMetric) or len(records) != len(BudgetPerformanceMetric):
        raise ApprovalError(
            "Budget-performance source must contain the complete governed metric set"
        )
    if len(extraction_methods) != 1 or not next(iter(extraction_methods)).strip():
        raise ApprovalError("Budget-performance records must share one extraction method")
    if any(record.source_page < 1 or not record.source_table for record in records):
        raise ApprovalError(
            "Every budget-performance record must retain source page and table provenance"
        )
    if any(record.is_demo for record in records):
        raise ApprovalError("Demo performance evidence can never be approved or published")

    fiscal_year = fiscal_years.pop()
    quarter = quarters.pop()
    state = session.get(State, state_ids.pop())
    if state is None:
        raise ApprovalError("Budget-performance source references an unknown state")

    version = _VERSION_RE.fullmatch(source.document_version or "")
    if version is None:
        raise ApprovalError("Budget-performance source version is invalid")
    if version.group("state_code").upper() != state.code.upper():
        raise ApprovalError("Budget-performance source version does not match the staged state")
    if int(version.group("year")) != fiscal_year or int(version.group("quarter")) != quarter:
        raise ApprovalError("Budget-performance source version does not match the staged period")
    if source.source_organization != f"{state.name} State Government":
        raise ApprovalError("Budget-performance source organization does not match the staged state")

    publishable = [record for record in records if record.metric in PUBLISHABLE_EXPENDITURE_METRICS]
    if len(publishable) != len(PUBLISHABLE_EXPENDITURE_METRICS):
        raise ApprovalError("Budget-performance source is missing a governed expenditure row")
    if any(
        record.quarter_actual is None
        or record.ytd_actual is None
        or record.performance_percent is None
        or record.balance is None
        for record in publishable
    ):
        raise ApprovalError(
            "Every governed expenditure row must contain quarter actual, YTD actual, "
            "performance percent, and remaining budget"
        )

    return source, reviewer, state, records, fiscal_year, quarter


def _check_governed_budget_alignment(
    session: Session,
    *,
    state: State,
    records: list[StateBudgetPerformanceRecord],
    fiscal_year: int,
) -> int:
    by_metric = {record.metric: record for record in records}
    checked = 0
    for performance_metric, budget_metric in _BUDGET_ALIGNMENT_METRICS.items():
        budget_claim = session.scalar(
            select(FiscalClaim)
            .where(
                FiscalClaim.state_id == state.id,
                FiscalClaim.object_type == "budget",
                FiscalClaim.fiscal_period == str(fiscal_year),
                FiscalClaim.metric == budget_metric,
            )
            .order_by(FiscalClaim.published_at.desc())
            .limit(1)
        )
        if budget_claim is None:
            continue
        if budget_claim.value is None:
            raise ApprovalError(
                f"Governed budget claim for {budget_metric} has no numeric value"
            )
        performance_budget = by_metric[performance_metric].original_budget
        if Decimal(budget_claim.value) != performance_budget:
            raise ApprovalError(
                "Budget-performance original budget conflicts with the governed annual "
                f"budget claim for {budget_metric}"
            )
        checked += 1
    return checked


def approve_budget_performance_source(
    session: Session,
    *,
    source_document_id: uuid.UUID,
    reviewer_id: uuid.UUID,
) -> BudgetPerformanceApprovalResult:
    """Human-verify a complete quarterly performance report without publishing claims."""

    source, reviewer, state, records, fiscal_year, quarter = _context(
        session,
        source_document_id=source_document_id,
        reviewer_id=reviewer_id,
    )
    checked = _check_governed_budget_alignment(
        session,
        state=state,
        records=records,
        fiscal_year=fiscal_year,
    )

    if (
        source.source_status is SourceStatus.APPROVED
        and source.processing_status is ProcessingStatus.COMPLETED
        and all(
            record.verification_status is VerificationStatus.HUMAN_VERIFIED
            for record in records
        )
    ):
        publishable = [
            record for record in records if record.metric in PUBLISHABLE_EXPENDITURE_METRICS
        ]
        return BudgetPerformanceApprovalResult(
            source_document_id=str(source.id),
            state_code=state.code,
            fiscal_year=fiscal_year,
            quarter=quarter,
            records_affected=len(records),
            claims_published=0,
            cross_source_budget_claims_checked=checked,
            published=all(record.is_published for record in publishable),
        )

    if source.source_status is not SourceStatus.READY_FOR_REVIEW:
        raise ApprovalError("Budget-performance source is not awaiting explicit review")
    if source.processing_status is not ProcessingStatus.READY_FOR_REVIEW:
        raise ApprovalError("Budget-performance source processing is not ready for review")
    if any(record.is_published for record in records):
        raise ApprovalError("Unapproved budget-performance records must not already be published")
    if any(
        record.verification_status is not VerificationStatus.REQUIRES_REVIEW
        for record in records
    ):
        raise ApprovalError(
            "Every budget-performance record must be awaiting review before approval"
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
            action="budget_performance.approved",
            entity_type="source_document",
            entity_id=source.id,
            payload={
                "state_code": state.code,
                "fiscal_year": fiscal_year,
                "quarter": quarter,
                "records_approved": len(records),
                "cross_source_budget_claims_checked": checked,
                "published": False,
            },
        )
    )
    session.commit()
    return BudgetPerformanceApprovalResult(
        source_document_id=str(source.id),
        state_code=state.code,
        fiscal_year=fiscal_year,
        quarter=quarter,
        records_affected=len(records),
        claims_published=0,
        cross_source_budget_claims_checked=checked,
        published=False,
    )


def _quarter_end(fiscal_year: int, quarter: int) -> datetime:
    month = quarter * 3
    day = monthrange(fiscal_year, month)[1]
    return datetime.combine(date(fiscal_year, month, day), time.min, tzinfo=UTC)


def _existing_expenditure_proof_ids(
    session: Session,
    *,
    source_document_id: uuid.UUID,
    fiscal_period: str,
) -> tuple[str, ...]:
    return tuple(
        session.scalars(
            select(FiscalClaim.gaia_id)
            .where(
                FiscalClaim.source_document_id == source_document_id,
                FiscalClaim.object_type == "expenditure",
                FiscalClaim.fiscal_period == fiscal_period,
            )
            .order_by(FiscalClaim.metric)
        )
    )


def publish_budget_performance_source(
    session: Session,
    *,
    source_document_id: uuid.UUID,
    reviewer_id: uuid.UUID,
) -> BudgetPerformanceApprovalResult:
    """Publish reviewed spending observations as immutable expenditure claims."""

    source, reviewer, state, records, fiscal_year, quarter = _context(
        session,
        source_document_id=source_document_id,
        reviewer_id=reviewer_id,
    )
    checked = _check_governed_budget_alignment(
        session,
        state=state,
        records=records,
        fiscal_year=fiscal_year,
    )

    if source.source_status is not SourceStatus.APPROVED:
        raise ApprovalError("Only approved budget-performance sources can be published")
    if source.processing_status is not ProcessingStatus.COMPLETED:
        raise ApprovalError(
            "Budget-performance source processing must be completed before publication"
        )
    if any(
        record.verification_status is not VerificationStatus.HUMAN_VERIFIED
        for record in records
    ):
        raise ApprovalError(
            "Every budget-performance record must be human-verified before publication"
        )

    publishable = [
        record for record in records if record.metric in PUBLISHABLE_EXPENDITURE_METRICS
    ]
    fiscal_period = f"{fiscal_year}Q{quarter}"
    if all(record.is_published for record in publishable):
        existing_ids = _existing_expenditure_proof_ids(
            session,
            source_document_id=source.id,
            fiscal_period=fiscal_period,
        )
        return BudgetPerformanceApprovalResult(
            source_document_id=str(source.id),
            state_code=state.code,
            fiscal_year=fiscal_year,
            quarter=quarter,
            records_affected=len(publishable),
            claims_published=len(existing_ids),
            cross_source_budget_claims_checked=checked,
            published=True,
            proof_gaia_ids=existing_ids,
        )
    if any(record.is_published for record in publishable):
        raise ApprovalError(
            "Budget-performance expenditure rows are only partially published; "
            "manual investigation required"
        )

    published_at = datetime.now(UTC)
    effective_at = _quarter_end(fiscal_year, quarter)
    proof_ids: list[str] = []
    try:
        for record in publishable:
            observations = (
                (
                    "quarter_actual",
                    record.quarter_actual,
                    record.quarter_actual_text,
                    "currency",
                    "NGN",
                ),
                (
                    "ytd_actual",
                    record.ytd_actual,
                    record.ytd_actual_text,
                    "currency",
                    "NGN",
                ),
                (
                    "budget_execution_percent",
                    record.performance_percent,
                    record.performance_percent_text,
                    "percent",
                    None,
                ),
                (
                    "remaining_budget",
                    record.balance,
                    record.balance_text,
                    "currency",
                    "NGN",
                ),
            )
            for suffix, value, value_text, unit, currency in observations:
                if value is None:
                    raise ApprovalError(
                        f"Publishable expenditure observation {record.metric.value}_{suffix} "
                        "is missing"
                    )
                proof = publish_domain_claim(
                    session,
                    domain="expenditure",
                    state_id=record.state_id,
                    source_document_id=source.id,
                    fiscal_period=fiscal_period,
                    metric=f"{record.metric.value}_{suffix}",
                    value=value,
                    value_text=value_text,
                    unit=unit,
                    currency=currency,
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
                action="budget_performance.expenditure_published",
                entity_type="source_document",
                entity_id=source.id,
                payload={
                    "state_code": state.code,
                    "fiscal_year": fiscal_year,
                    "quarter": quarter,
                    "supporting_records_reviewed": len(records),
                    "expenditure_records_published": len(publishable),
                    "claims_published": len(proof_ids),
                    "cross_source_budget_claims_checked": checked,
                    "published": True,
                },
            )
        )
        session.commit()
    except Exception:
        session.rollback()
        raise

    return BudgetPerformanceApprovalResult(
        source_document_id=str(source.id),
        state_code=state.code,
        fiscal_year=fiscal_year,
        quarter=quarter,
        records_affected=len(publishable),
        claims_published=len(proof_ids),
        cross_source_budget_claims_checked=checked,
        published=True,
        proof_gaia_ids=tuple(proof_ids),
    )
