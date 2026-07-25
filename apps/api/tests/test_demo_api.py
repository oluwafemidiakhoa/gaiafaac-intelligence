from pathlib import Path

import pytest
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.api.v1.routes.demo_data import compare, sources, state_detail
from gaiafaac_api.database.models import StateAllocation
from gaiafaac_api.database.seeds import seed_demo_allocations
from gaiafaac_api.services.demo_data import (
    get_demo_overview,
    get_demo_states,
    latest_demo_period,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEMO_CSV = REPOSITORY_ROOT / "database/seeds/demo_state_allocations.csv"


def _period(session: Session):
    seed_demo_allocations(session, DEMO_CSV)
    period = latest_demo_period(session)
    assert period is not None
    return period


def test_demo_overview_is_partial_labelled_and_unpublished(session: Session) -> None:
    payload = get_demo_overview(session, _period(session))

    assert payload.data_label == "DEMO DATA - NOT REAL FAAC DATA"
    assert payload.covered_states == 3
    assert payload.expected_states == 37
    assert payload.sample_gross_total == "6000.00"
    assert payload.sample_deductions_total == "600.00"
    assert payload.sample_net_total == "5400.00"
    assert "not national FAAC totals" in payload.scope_note
    assert payload.period.is_published is False
    assert all(item.is_published is False for item in payload.allocations)


def test_state_directory_marks_unavailable_demo_values(session: Session) -> None:
    payload = get_demo_states(session, _period(session))

    assert len(payload.states) == 37
    assert sum(state.has_demo_allocation for state in payload.states) == 3
    abia = next(state for state in payload.states if state.slug == "abia")
    assert abia.has_demo_allocation is False
    assert abia.demo_net_allocation is None


def test_overview_does_not_treat_missing_amounts_as_zero(session: Session) -> None:
    period = _period(session)
    allocation = session.scalar(select(StateAllocation).limit(1))
    assert allocation is not None
    allocation.net_allocation = None
    session.flush()

    payload = get_demo_overview(session, period)

    assert payload.sample_net_total is None


def test_state_detail_and_comparison_never_fill_missing_values(session: Session) -> None:
    _period(session)

    lagos = state_detail("lagos", session)
    missing = state_detail("abia", session)
    compared = compare(session, ["lagos", "abia"])

    assert lagos.allocation is not None
    assert lagos.allocation.net_allocation == "900.00"
    assert lagos.components[0].component_name.startswith("DEMO DATA")
    assert missing.allocation is None
    assert missing.unavailable_note is not None
    assert "No labelled demo allocation" in missing.unavailable_note
    assert len(compared.states) == 2
    assert next(item for item in compared.states if item.state.slug == "abia").allocation is None


def test_demo_sources_do_not_expose_internal_storage_paths(session: Session) -> None:
    _period(session)
    payload = sources(session)

    assert payload.data_label == "DEMO DATA - NOT REAL FAAC DATA"
    assert len(payload.sources) == 1
    assert payload.sources[0].is_demo is True
    assert "storage_path" not in payload.sources[0].model_dump()


def test_compare_rejects_duplicate_states(session: Session) -> None:
    _period(session)

    with pytest.raises(HTTPException) as error:
        compare(session, ["lagos", "lagos"])

    assert error.value.status_code == 422
