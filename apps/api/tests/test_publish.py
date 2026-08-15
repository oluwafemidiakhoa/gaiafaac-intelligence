import csv
import uuid
from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.enums import UserRole
from gaiafaac_api.database.ledger_models import EvidenceSource, FiscalProof, FiscalState
from gaiafaac_api.database.models import StateAllocation, User
from gaiafaac_api.database.seeds import NIGERIAN_STATES, seed_states
from gaiafaac_api.pipeline.approval import approve_import, publish_import
from gaiafaac_api.pipeline.errors import ApprovalError
from gaiafaac_api.pipeline.extraction.file_import import import_file
from gaiafaac_api.pipeline.importer import ImportRequest
from gaiafaac_api.services.published_data import get_published_overview, latest_published_period


def _user(session: Session, role: UserRole) -> User:
    user = User(
        email=f"{uuid.uuid4()}@example.test",
        full_name=role.value.title(),
        role=role,
        is_active=True,
    )
    session.add(user)
    session.commit()
    return user


def _import(
    session: Session, tmp_path: Path, *, is_demo: bool = False, label: str = "Real Jan 2026"
):
    seed_states(session)
    path = tmp_path / f"{'demo' if is_demo else 'real'}.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["state", "gross_total", "net_allocation", "data_label"]
        )
        writer.writeheader()
        for name, *_ in NIGERIAN_STATES:
            writer.writerow(
                {
                    "state": name,
                    "gross_total": "1000.00",
                    "net_allocation": "900.00",
                    "data_label": "DEMO DATA - NOT REAL FAAC DATA" if is_demo else "",
                }
            )
    return import_file(
        session,
        ImportRequest(
            path=path,
            source_organization="OAGF",
            revenue_month=date(2026, 1, 1),
            faac_meeting_date=date(2026, 2, 1),
            publication_date=date(2026, 2, 1),
            reporting_label=label,
            reported_unit="naira",
            is_demo=is_demo,
        ),
    )


def test_full_publish_lifecycle_serves_real_data(session: Session, tmp_path: Path) -> None:
    result = _import(session, tmp_path)
    reviewer = _user(session, UserRole.REVIEWER)
    publisher = _user(session, UserRole.ADMINISTRATOR)
    approve_import(session, run_id=uuid.UUID(result.run_id), reviewer_id=reviewer.id)

    published = publish_import(session, run_id=uuid.UUID(result.run_id), reviewer_id=publisher.id)
    assert published.published is True
    assert published.allocations_approved == 37

    allocations = list(session.scalars(select(StateAllocation)))
    assert all(a.is_published is True and a.is_demo is False for a in allocations)
    assert len(list(session.scalars(select(FiscalProof)))) == 37
    assert len(list(session.scalars(select(FiscalState)))) == 37
    assert len(list(session.scalars(select(EvidenceSource)))) == 37

    period = latest_published_period(session)
    assert period is not None
    overview = get_published_overview(session, period)
    assert overview is not None
    assert overview.covered_states == 37
    assert overview.source.source_organization == "OAGF"
    assert overview.total_net == "33300.00"  # 37 states x 900.00
    assert not hasattr(overview, "data_label")


def test_cannot_publish_before_human_verification(session: Session, tmp_path: Path) -> None:
    result = _import(session, tmp_path)
    publisher = _user(session, UserRole.ADMINISTRATOR)
    with pytest.raises(ApprovalError, match="human-verified"):
        publish_import(session, run_id=uuid.UUID(result.run_id), reviewer_id=publisher.id)


def test_reviewer_cannot_publish(session: Session, tmp_path: Path) -> None:
    result = _import(session, tmp_path)
    reviewer = _user(session, UserRole.REVIEWER)
    approve_import(session, run_id=uuid.UUID(result.run_id), reviewer_id=reviewer.id)
    with pytest.raises(ApprovalError, match="administrator"):
        publish_import(session, run_id=uuid.UUID(result.run_id), reviewer_id=reviewer.id)


def test_same_administrator_cannot_review_and_publish(session: Session, tmp_path: Path) -> None:
    result = _import(session, tmp_path)
    administrator = _user(session, UserRole.ADMINISTRATOR)
    approve_import(session, run_id=uuid.UUID(result.run_id), reviewer_id=administrator.id)
    with pytest.raises(ApprovalError, match="reviewer cannot publish"):
        publish_import(session, run_id=uuid.UUID(result.run_id), reviewer_id=administrator.id)


def test_demo_data_can_never_be_published(session: Session, tmp_path: Path) -> None:
    result = _import(session, tmp_path, is_demo=True, label="DEMO Jan 2026")
    reviewer = _user(session, UserRole.REVIEWER)
    publisher = _user(session, UserRole.ADMINISTRATOR)
    approve_import(session, run_id=uuid.UUID(result.run_id), reviewer_id=reviewer.id)
    with pytest.raises(ApprovalError, match="Demo data can never be published"):
        publish_import(session, run_id=uuid.UUID(result.run_id), reviewer_id=publisher.id)
