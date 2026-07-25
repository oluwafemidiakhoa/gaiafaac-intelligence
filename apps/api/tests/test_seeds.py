from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from gaiafaac_api.database.enums import SourceStatus, VerificationStatus
from gaiafaac_api.database.models import (
    ReportingPeriod,
    SourceDocument,
    State,
    StateAllocation,
    StateAllocationComponent,
)
from gaiafaac_api.database.seeds import seed_demo_allocations, seed_states

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEMO_CSV = REPOSITORY_ROOT / "database/seeds/demo_state_allocations.csv"


def test_state_seed_is_complete_deterministic_and_idempotent(session: Session) -> None:
    assert seed_states(session) == 37
    first_ids = {state.code: state.id for state in session.scalars(select(State))}

    assert seed_states(session) == 0
    second_ids = {state.code: state.id for state in session.scalars(select(State))}

    assert first_ids == second_ids
    assert len(first_ids) == 37
    assert session.scalar(select(func.count()).select_from(State).where(State.is_fct)) == 1
    assert "oil_producing" not in State.__table__.c


def test_demo_seed_is_unmistakable_pending_and_unpublished(session: Session) -> None:
    assert seed_demo_allocations(session, DEMO_CSV) == 3
    assert seed_demo_allocations(session, DEMO_CSV) == 0

    period = session.scalar(select(ReportingPeriod).where(ReportingPeriod.is_demo))
    source = session.scalar(select(SourceDocument).where(SourceDocument.is_demo))
    allocations = session.scalars(select(StateAllocation).where(StateAllocation.is_demo)).all()
    components = session.scalars(select(StateAllocationComponent)).all()

    assert period is not None
    assert "DEMO DATA" in period.reporting_label
    assert period.revenue_month.year == 2099
    assert period.verification_status is VerificationStatus.PENDING
    assert period.is_published is False
    assert source is not None
    assert source.source_status is SourceStatus.DEMO
    assert source.is_demo is True
    assert len(allocations) == 3
    assert len(components) == 3
    assert all(item.verification_status is VerificationStatus.PENDING for item in allocations)
    assert all(item.is_published is False for item in allocations)
    assert all("DEMO DATA" in item.component_name for item in components)
