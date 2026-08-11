import uuid
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import select

from gaiafaac_api.database.enums import (
    ProcessingStatus,
    ReportedUnit,
    SourceStatus,
    UserRole,
    VerificationStatus,
)
from gaiafaac_api.database.igr_models import IgrPeriodType, StateIgrRecord
from gaiafaac_api.database.models import AuditLog, SourceDocument, State, User
from gaiafaac_api.database.seeds import seed_states
from gaiafaac_api.pipeline.errors import ApprovalError
from gaiafaac_api.pipeline.igr.approval import approve_igr_source, publish_igr_source


def _seed_review_source(session):
    seed_states(session)
    reviewer = User(
        email=f"reviewer-{uuid.uuid4()}@example.test",
        full_name="IGR Reviewer",
        role=UserRole.REVIEWER,
        is_active=True,
    )
    source = SourceDocument(
        source_organization="National Bureau of Statistics (NBS)",
        source_url="https://example.test/IGR_2024.zip",
        original_filename="IGR_2024.zip",
        storage_path="/tmp/IGR_2024.zip",
        sha256="b" * 64,
        mime_type="application/zip",
        processing_status=ProcessingStatus.READY_FOR_REVIEW,
        source_status=SourceStatus.READY_FOR_REVIEW,
        is_demo=False,
    )
    session.add_all([reviewer, source])
    session.flush()

    states = list(session.scalars(select(State).order_by(State.code)))
    for index, state in enumerate(states, start=1):
        session.add(
            StateIgrRecord(
                state_id=state.id,
                source_document_id=source.id,
                fiscal_year=2024,
                period_type=IgrPeriodType.ANNUAL,
                quarter=None,
                period_start=date(2024, 1, 1),
                period_end=date(2024, 12, 31),
                igr_amount=Decimal(index * 1000),
                igr_amount_original=str(index * 1000),
                reported_unit=ReportedUnit.NAIRA,
                verification_status=VerificationStatus.REQUIRES_REVIEW,
                is_demo=False,
                is_published=False,
            )
        )
    session.commit()
    return reviewer, source


def test_approve_then_publish_igr_source(session):
    reviewer, source = _seed_review_source(session)

    approved = approve_igr_source(
        session,
        source_document_id=source.id,
        reviewer_id=reviewer.id,
    )
    assert approved.records_approved == 37
    assert approved.fiscal_year == 2024
    assert approved.published is False

    records = list(
        session.scalars(select(StateIgrRecord).where(StateIgrRecord.source_document_id == source.id))
    )
    assert len(records) == 37
    assert all(record.verification_status is VerificationStatus.HUMAN_VERIFIED for record in records)
    assert all(record.reviewed_by == reviewer.id for record in records)
    assert all(record.reviewed_at is not None for record in records)
    assert all(record.is_published is False for record in records)
    assert source.source_status is SourceStatus.APPROVED
    assert source.processing_status is ProcessingStatus.COMPLETED

    published = publish_igr_source(
        session,
        source_document_id=source.id,
        reviewer_id=reviewer.id,
    )
    assert published.records_approved == 37
    assert published.published is True
    assert all(record.is_published is True for record in records)
    assert all(record.published_at is not None for record in records)

    actions = list(
        session.scalars(
            select(AuditLog.action)
            .where(AuditLog.entity_id == source.id)
            .order_by(AuditLog.created_at)
        )
    )
    assert actions == ["igr.approved", "igr.published"]


def test_cannot_publish_before_human_approval(session):
    reviewer, source = _seed_review_source(session)

    with pytest.raises(ApprovalError, match="Only approved IGR sources"):
        publish_igr_source(
            session,
            source_document_id=source.id,
            reviewer_id=reviewer.id,
        )


def test_approval_rejects_incomplete_state_coverage(session):
    reviewer, source = _seed_review_source(session)
    record = session.scalar(
        select(StateIgrRecord).where(StateIgrRecord.source_document_id == source.id).limit(1)
    )
    session.delete(record)
    session.commit()

    with pytest.raises(ApprovalError, match="all 36 states and the FCT"):
        approve_igr_source(
            session,
            source_document_id=source.id,
            reviewer_id=reviewer.id,
        )


def test_approval_requires_active_reviewer_or_admin(session):
    _, source = _seed_review_source(session)
    viewer = User(
        email=f"viewer-{uuid.uuid4()}@example.test",
        full_name="IGR Viewer",
        role=UserRole.VIEWER,
        is_active=True,
    )
    session.add(viewer)
    session.commit()

    with pytest.raises(ApprovalError, match="active reviewer or administrator"):
        approve_igr_source(
            session,
            source_document_id=source.id,
            reviewer_id=viewer.id,
        )
