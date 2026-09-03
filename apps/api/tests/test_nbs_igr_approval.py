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
from gaiafaac_api.database.ledger_models import FiscalClaim
from gaiafaac_api.database.models import SourceDocument, State, User
from gaiafaac_api.database.seeds import seed_states
from gaiafaac_api.pipeline.errors import ApprovalError
from gaiafaac_api.pipeline.nbs_igr.approval import approve_igr_source, publish_igr_source


def _reviewer(session, *, email: str = "igr-reviewer@example.com") -> User:
    user = User(
        email=email,
        full_name="NBS IGR Reviewer",
        role=UserRole.REVIEWER,
        is_active=True,
    )
    session.add(user)
    session.flush()
    return user


def _administrator(session, *, email: str = "igr-publisher@example.com") -> User:
    user = User(
        email=email,
        full_name="NBS IGR Administrator",
        role=UserRole.ADMINISTRATOR,
        is_active=True,
    )
    session.add(user)
    session.flush()
    return user


def _staged_source(session, *, missing_one: bool = False, year: int = 2023):
    seed_states(session)
    states = list(session.scalars(select(State).order_by(State.code)))
    source = SourceDocument(
        source_organization="National Bureau of Statistics (NBS)",
        source_url="https://www.nigerianstat.gov.ng/elibrary/read/1241579",
        original_filename="nbs-igr.pdf",
        storage_path="/tmp/nbs-igr.pdf",
        sha256="b" * 64,
        mime_type="application/pdf",
        processing_status=ProcessingStatus.READY_FOR_REVIEW,
        source_status=SourceStatus.READY_FOR_REVIEW,
        document_version=f"igr-{year}-report-1241579",
        is_demo=False,
    )
    session.add(source)
    session.flush()
    selected = states[:-1] if missing_one else states
    for index, state in enumerate(selected, start=1):
        session.add(
            StateIgrRecord(
                state_id=state.id,
                source_document_id=source.id,
                fiscal_year=year,
                period_type=IgrPeriodType.ANNUAL,
                quarter=None,
                period_start=date(year, 1, 1),
                period_end=date(year, 12, 31),
                igr_amount=Decimal(index * 1_000_000),
                igr_amount_original=f"N {index * 1_000_000:.2f}",
                reported_unit=ReportedUnit.NAIRA,
                source_page=index,
                source_table=f"NBS Internally Generated Revenue At State Level ({year})",
                verification_status=VerificationStatus.REQUIRES_REVIEW,
                is_demo=False,
                is_published=False,
            )
        )
    session.commit()
    return source


def test_approve_igr_source_requires_complete_state_fct_coverage(session):
    reviewer = _reviewer(session)
    source = _staged_source(session, missing_one=True)

    with pytest.raises(ApprovalError, match="36 states and the FCT"):
        approve_igr_source(
            session,
            source_document_id=source.id,
            reviewer_id=reviewer.id,
        )


def test_approve_igr_source_human_verifies_without_publishing(session):
    reviewer = _reviewer(session)
    source = _staged_source(session)

    result = approve_igr_source(
        session,
        source_document_id=source.id,
        reviewer_id=reviewer.id,
    )
    records = list(
        session.scalars(
            select(StateIgrRecord).where(StateIgrRecord.source_document_id == source.id)
        )
    )

    assert result.records_affected == 37
    assert result.published is False
    assert source.source_status is SourceStatus.APPROVED
    assert source.processing_status is ProcessingStatus.COMPLETED
    assert all(
        record.verification_status is VerificationStatus.HUMAN_VERIFIED for record in records
    )
    assert all(not record.is_published for record in records)
    assert (
        session.scalar(
            select(FiscalClaim.gaia_id).where(FiscalClaim.source_document_id == source.id)
        )
        is None
    )


def test_publish_igr_source_requires_prior_approval(session):
    administrator = _administrator(session)
    source = _staged_source(session)

    with pytest.raises(ApprovalError, match="Only approved NBS IGR sources"):
        publish_igr_source(
            session,
            source_document_id=source.id,
            reviewer_id=administrator.id,
        )


def test_publish_igr_source_creates_verified_governed_claims(session):
    reviewer = _reviewer(session)
    administrator = _administrator(session)
    source = _staged_source(session)
    approve_igr_source(
        session,
        source_document_id=source.id,
        reviewer_id=reviewer.id,
    )

    result = publish_igr_source(
        session,
        source_document_id=source.id,
        reviewer_id=administrator.id,
    )
    claims = list(
        session.scalars(
            select(FiscalClaim).where(
                FiscalClaim.source_document_id == source.id,
                FiscalClaim.object_type == "igr",
                FiscalClaim.metric == "igr",
            )
        )
    )
    records = list(
        session.scalars(
            select(StateIgrRecord).where(StateIgrRecord.source_document_id == source.id)
        )
    )

    assert result.published is True
    assert len(result.proof_gaia_ids) == 37
    assert len(claims) == 37
    assert {claim.fiscal_period for claim in claims} == {"2023"}
    assert {claim.currency for claim in claims} == {"NGN"}
    assert all(record.is_published for record in records)


def test_publish_igr_source_requires_an_administrator(session):
    reviewer = _reviewer(session)
    other_reviewer = _reviewer(session, email="second-igr-reviewer@example.com")
    source = _staged_source(session)
    approve_igr_source(session, source_document_id=source.id, reviewer_id=reviewer.id)

    with pytest.raises(ApprovalError, match="requires an active administrator"):
        publish_igr_source(
            session,
            source_document_id=source.id,
            reviewer_id=other_reviewer.id,
        )


def test_publish_igr_source_rejects_the_same_actor_as_reviewer(session):
    reviewer = _reviewer(session)
    reviewer.role = UserRole.ADMINISTRATOR
    session.flush()
    source = _staged_source(session)
    approve_igr_source(session, source_document_id=source.id, reviewer_id=reviewer.id)

    with pytest.raises(ApprovalError, match="cannot publish the same source"):
        publish_igr_source(
            session,
            source_document_id=source.id,
            reviewer_id=reviewer.id,
        )
