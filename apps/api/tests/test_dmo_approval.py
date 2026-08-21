from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import select

from gaiafaac_api.database.debt_models import DebtKind, StateDebtRecord
from gaiafaac_api.database.enums import (
    ProcessingStatus,
    SourceStatus,
    UserRole,
    VerificationStatus,
)
from gaiafaac_api.database.ledger_models import FiscalClaim
from gaiafaac_api.database.models import SourceDocument, State, User
from gaiafaac_api.database.seeds import seed_states
from gaiafaac_api.pipeline.dmo.approval import approve_debt_source, publish_debt_source
from gaiafaac_api.pipeline.dmo.archive import DMO_ORGANIZATION
from gaiafaac_api.pipeline.errors import ApprovalError


def _reviewer(session) -> User:
    user = User(
        email="reviewer@example.com",
        full_name="DMO Reviewer",
        role=UserRole.REVIEWER,
        is_active=True,
    )
    session.add(user)
    session.flush()
    return user


def _staged_source(session, *, missing_one: bool = False):
    seed_states(session)
    states = list(session.scalars(select(State).order_by(State.code)))
    source = SourceDocument(
        source_organization=DMO_ORGANIZATION,
        source_url="https://www.dmo.gov.ng/files/test.pdf",
        original_filename="test.pdf",
        storage_path="/tmp/test.pdf",
        sha256="a" * 64,
        mime_type="application/pdf",
        processing_status=ProcessingStatus.READY_FOR_REVIEW,
        source_status=SourceStatus.READY_FOR_REVIEW,
        document_version="domestic-2026-03-31",
        is_demo=False,
    )
    session.add(source)
    session.flush()
    selected = states[:-1] if missing_one else states
    for index, state in enumerate(selected, start=1):
        session.add(
            StateDebtRecord(
                state_id=state.id,
                source_document_id=source.id,
                debt_kind=DebtKind.DOMESTIC,
                as_of_date=date(2026, 3, 31),
                debt_amount=Decimal(index * 1_000_000),
                debt_amount_original=f"{index * 1_000_000:.2f}",
                currency="NGN",
                components={},
                source_page=1,
                source_table="DMO domestic state/FCT debt stock",
                verification_status=VerificationStatus.REQUIRES_REVIEW,
                is_demo=False,
                is_published=False,
            )
        )
    session.commit()
    return source


def test_approve_debt_source_requires_complete_state_fct_coverage(session):
    reviewer = _reviewer(session)
    source = _staged_source(session, missing_one=True)

    with pytest.raises(ApprovalError, match="36 states and the FCT"):
        approve_debt_source(
            session,
            source_document_id=source.id,
            reviewer_id=reviewer.id,
        )


def test_approve_debt_source_human_verifies_without_publishing(session):
    reviewer = _reviewer(session)
    source = _staged_source(session)

    result = approve_debt_source(
        session,
        source_document_id=source.id,
        reviewer_id=reviewer.id,
    )
    records = list(
        session.scalars(
            select(StateDebtRecord).where(StateDebtRecord.source_document_id == source.id)
        )
    )

    assert result.records_affected == 37
    assert result.published is False
    assert source.source_status is SourceStatus.APPROVED
    assert source.processing_status is ProcessingStatus.COMPLETED
    assert all(
        record.verification_status is VerificationStatus.HUMAN_VERIFIED
        for record in records
    )
    assert all(not record.is_published for record in records)


def test_publish_debt_source_creates_verified_governed_claims(session):
    reviewer = _reviewer(session)
    source = _staged_source(session)
    approve_debt_source(
        session,
        source_document_id=source.id,
        reviewer_id=reviewer.id,
    )

    result = publish_debt_source(
        session,
        source_document_id=source.id,
        reviewer_id=reviewer.id,
    )
    claims = list(
        session.scalars(
            select(FiscalClaim).where(
                FiscalClaim.source_document_id == source.id,
                FiscalClaim.object_type == "debt",
                FiscalClaim.metric == "domestic_debt_stock",
            )
        )
    )
    records = list(
        session.scalars(
            select(StateDebtRecord).where(StateDebtRecord.source_document_id == source.id)
        )
    )

    assert result.published is True
    assert len(result.proof_gaia_ids) == 37
    assert len(claims) == 37
    assert {claim.currency for claim in claims} == {"NGN"}
    assert all(record.is_published for record in records)
