from __future__ import annotations

import re
import tempfile
import uuid
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from gaiafaac_api.database.enums import ExtractionStatus, UserRole, VerificationStatus
from gaiafaac_api.database.lga_models import (
    LocalGovernment,
    LocalGovernmentAllocation,
    LocalGovernmentReview,
)
from gaiafaac_api.database.models import AuditLog, ExtractionRun, SourceDocument, State, User
from gaiafaac_api.database.oagf_revision_models import OagfArchiveObject
from gaiafaac_api.pipeline.extraction.oagf_lga_table_iv import extract_oagf_table_iv

EXPECTED_LGA_JURISDICTIONS = 774

_STATE_ALIASES = {
    "fct abuja": "fct",
    "fct": "fct",
    "nassarawa": "nasarawa",
}


def _key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")


def _active_user(session: Session, user_id: uuid.UUID, *, administrator: bool = False) -> User:
    user = session.get(User, user_id)
    if user is None or not user.is_active:
        raise ValueError("An active database user is required")
    allowed = (
        {UserRole.ADMINISTRATOR}
        if administrator
        else {
            UserRole.REVIEWER,
            UserRole.ADMINISTRATOR,
        }
    )
    if user.role not in allowed:
        raise ValueError("The selected user is not authorized for this action")
    return user


def _state_map(session: Session) -> dict[str, State]:
    states = list(session.scalars(select(State)))
    mapped: dict[str, State] = {}
    for state in states:
        mapped[_key(state.name)] = state
        mapped[_key(state.code)] = state
    for alias, canonical in _STATE_ALIASES.items():
        target = mapped.get(canonical)
        if target is not None:
            mapped[alias] = target
    return mapped


def import_lga_table_iv_from_archive(
    session: Session,
    *,
    source_document_id: uuid.UUID,
) -> LocalGovernmentReview:
    """Import retained OAGF Table IV bytes into a governed, unpublished review batch."""
    source = session.get(SourceDocument, source_document_id)
    if source is None:
        raise ValueError("Source document does not exist")
    if source.reporting_period_id is None:
        raise ValueError("OAGF source document is not attached to a reporting period")

    existing_review = session.scalar(
        select(LocalGovernmentReview).where(LocalGovernmentReview.source_document_id == source.id)
    )
    if existing_review is not None:
        return existing_review

    archive = session.scalar(
        select(OagfArchiveObject).where(OagfArchiveObject.sha256 == source.sha256)
    )
    if archive is None:
        raise ValueError("Exact OAGF source bytes are not retained in the durable archive")

    run = ExtractionRun(
        source_document_id=source.id,
        status=ExtractionStatus.RUNNING,
        extractor_name="oagf_table_iv_lga",
        extractor_version="1",
        started_at=datetime.now(UTC),
        records_extracted=0,
        configuration={"source_table": "Table IV", "expected_jurisdictions": 774},
    )
    session.add(run)
    session.flush()

    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as handle:
            handle.write(archive.content)
            temporary_path = Path(handle.name)
        extracted = extract_oagf_table_iv(temporary_path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)

    states = _state_map(session)
    unmatched_states = sorted(
        {
            row.state_name
            for row in extracted.rows
            if _key(row.state_name) not in states
            and _STATE_ALIASES.get(_key(row.state_name), _key(row.state_name)) not in states
        }
    )

    blocking = len(extracted.warnings) + len(unmatched_states)
    inserted = 0
    seen: set[tuple[uuid.UUID, str]] = set()

    for row in extracted.rows:
        state_key = _STATE_ALIASES.get(_key(row.state_name), _key(row.state_name))
        state = states.get(state_key)
        if state is None:
            continue
        slug = _slug(row.local_government_name)
        key = (state.id, slug)
        if key in seen:
            blocking += 1
            continue
        seen.add(key)

        lga = session.scalar(
            select(LocalGovernment).where(
                LocalGovernment.state_id == state.id,
                LocalGovernment.slug == slug,
            )
        )
        if lga is None:
            lga = LocalGovernment(
                state_id=state.id,
                official_name=row.local_government_name,
                slug=slug,
            )
            session.add(lga)
            session.flush()

        existing = session.scalar(
            select(LocalGovernmentAllocation).where(
                LocalGovernmentAllocation.reporting_period_id == source.reporting_period_id,
                LocalGovernmentAllocation.local_government_id == lga.id,
            )
        )
        if existing is not None:
            blocking += 1
            continue

        originals = row.originals
        session.add(
            LocalGovernmentAllocation(
                reporting_period_id=source.reporting_period_id,
                local_government_id=lga.id,
                source_document_id=source.id,
                extraction_run_id=run.id,
                net_statutory_allocation=row.net_statutory_allocation,
                deduction_amount=row.deduction_amount,
                ecology_share=row.ecology_share,
                ecology_transfer=row.ecology_transfer,
                net_ecology_share=row.net_ecology_share,
                vat_amount=row.vat_amount,
                total_net_allocation=row.total_net_allocation,
                net_statutory_original=originals["net_statutory_allocation"],
                deduction_original=originals["deduction_amount"],
                ecology_share_original=originals["ecology_share"],
                ecology_transfer_original=originals["ecology_transfer"],
                net_ecology_original=originals["net_ecology_share"],
                vat_original=originals["vat_amount"],
                total_net_original=originals["total_net_allocation"] or "",
                source_page=row.page,
                verification_status=VerificationStatus.REQUIRES_REVIEW,
            )
        )
        inserted += 1

    if inserted != EXPECTED_LGA_JURISDICTIONS:
        blocking += 1

    run.records_extracted = inserted
    run.completed_at = datetime.now(UTC)
    run.status = ExtractionStatus.REQUIRES_REVIEW
    run.configuration = {
        **(run.configuration or {}),
        "warnings": extracted.warnings,
        "unmatched_states": unmatched_states,
        "inserted_records": inserted,
        "blocking_count": blocking,
    }

    review = LocalGovernmentReview(
        reporting_period_id=source.reporting_period_id,
        source_document_id=source.id,
        extraction_run_id=run.id,
        record_count=inserted,
        blocking_count=blocking,
        status="requires_review" if blocking == 0 else "investigation_required",
    )
    session.add(review)
    session.commit()
    session.refresh(review)
    return review


def approve_lga_review(
    session: Session,
    *,
    review_id: uuid.UUID,
    reviewer_id: uuid.UUID,
) -> LocalGovernmentReview:
    reviewer = _active_user(session, reviewer_id)
    review = session.get(LocalGovernmentReview, review_id)
    if review is None:
        raise ValueError("LGA review batch does not exist")
    if review.status == "published":
        raise ValueError("Published LGA evidence cannot be re-approved")
    if review.blocking_count != 0 or review.record_count != EXPECTED_LGA_JURISDICTIONS:
        raise ValueError(
            "LGA evidence has blocking findings or incomplete 774-jurisdiction coverage"
        )

    allocations = list(
        session.scalars(
            select(LocalGovernmentAllocation).where(
                LocalGovernmentAllocation.extraction_run_id == review.extraction_run_id
            )
        )
    )
    if len(allocations) != EXPECTED_LGA_JURISDICTIONS:
        raise ValueError("Stored LGA allocation count does not match the governed review batch")

    now = datetime.now(UTC)
    for allocation in allocations:
        allocation.verification_status = VerificationStatus.HUMAN_VERIFIED
        allocation.reviewed_by = reviewer.id
        allocation.reviewed_at = now
    review.status = "approved"
    review.approved_by = reviewer.id
    review.approved_at = now
    session.add(
        AuditLog(
            actor_user_id=reviewer.id,
            action="local_government_allocations.approved",
            entity_type="local_government_review",
            entity_id=review.id,
            payload={"record_count": len(allocations)},
        )
    )
    session.commit()
    session.refresh(review)
    return review


def publish_lga_review(
    session: Session,
    *,
    review_id: uuid.UUID,
    publisher_id: uuid.UUID,
) -> LocalGovernmentReview:
    publisher = _active_user(session, publisher_id, administrator=True)
    review = session.get(LocalGovernmentReview, review_id)
    if review is None:
        raise ValueError("LGA review batch does not exist")
    if review.status != "approved" or review.approved_by is None:
        raise ValueError("LGA evidence must be explicitly approved before publication")
    if review.approved_by == publisher.id:
        raise ValueError("Four-eyes control requires a different publisher from the reviewer")

    allocations = list(
        session.scalars(
            select(LocalGovernmentAllocation).where(
                LocalGovernmentAllocation.extraction_run_id == review.extraction_run_id
            )
        )
    )
    verified_count = sum(
        allocation.verification_status == VerificationStatus.HUMAN_VERIFIED
        for allocation in allocations
    )
    if len(allocations) != EXPECTED_LGA_JURISDICTIONS or verified_count != len(allocations):
        raise ValueError("Only complete human-verified LGA evidence can be published")

    now = datetime.now(UTC)
    for allocation in allocations:
        allocation.is_published = True
        allocation.published_at = now
    review.status = "published"
    review.published_by = publisher.id
    review.published_at = now
    session.add(
        AuditLog(
            actor_user_id=publisher.id,
            action="local_government_allocations.published",
            entity_type="local_government_review",
            entity_id=review.id,
            payload={"record_count": len(allocations), "approved_by": str(review.approved_by)},
        )
    )
    session.commit()
    session.refresh(review)
    return review


def published_lga_count(session: Session, reporting_period_id: uuid.UUID) -> int:
    return int(
        session.scalar(
            select(func.count(LocalGovernmentAllocation.id)).where(
                LocalGovernmentAllocation.reporting_period_id == reporting_period_id,
                LocalGovernmentAllocation.is_published.is_(True),
                LocalGovernmentAllocation.is_demo.is_(False),
            )
        )
        or 0
    )
