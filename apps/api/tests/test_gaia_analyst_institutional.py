from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select

from gaiafaac_api.database.enums import SourceStatus
from gaiafaac_api.database.models import SourceDocument, State
from gaiafaac_api.database.seeds import seed_states
from gaiafaac_api.services.fiscal_domain_claims import publish_domain_claim
from gaiafaac_api.services.fiscal_ledger import publish_current_fiscal_state
from gaiafaac_api.services.gaia_analyst_institutional import gaia_analyst


def _source(session, sha: str):
    source = SourceDocument(
        source_organization="Official publisher",
        original_filename=f"{sha[:4]}.pdf",
        storage_path=f"archive/{sha}.pdf",
        sha256=sha,
        mime_type="application/pdf",
        source_status=SourceStatus.APPROVED,
        is_demo=False,
    )
    session.add(source)
    session.flush()
    return source


def _build_lagos_fiscal_state(session):
    seed_states(session)
    state = session.scalar(select(State).where(State.code == "LA"))
    assert state is not None
    source = _source(session, "a" * 64)
    observed = datetime(2026, 12, 31, 12, 0, tzinfo=UTC)
    publish_domain_claim(
        session,
        domain="debt",
        state_id=state.id,
        source_document_id=source.id,
        fiscal_period="2026",
        metric="total_debt_stock",
        value=Decimal("200"),
        value_text="200",
        unit="naira",
        currency="NGN",
        effective_at=observed,
        published_at=observed,
        human_reviewed=True,
        reconciled=True,
    )
    publish_domain_claim(
        session,
        domain="budget",
        state_id=state.id,
        source_document_id=source.id,
        fiscal_period="2026",
        metric="total_revenue",
        value=Decimal("100"),
        value_text="100",
        unit="naira",
        currency="NGN",
        effective_at=observed,
        published_at=observed,
        human_reviewed=True,
        reconciled=True,
    )
    fiscal_state = publish_current_fiscal_state(
        session,
        state_id=state.id,
        effective_at=observed,
        fiscal_period="2026",
    )
    session.commit()
    return state, fiscal_state


def test_analyst_answers_cross_domain_metric_from_fiscal_state(session):
    _state, fiscal_state = _build_lagos_fiscal_state(session)
    response = gaia_analyst(
        session,
        question="What is the debt burden for Lagos?",
        year=2026,
    )
    assert response.intent == "ledger_metric"
    assert response.status == "answered"
    assert "200.00 percent" in response.answer
    assert response.evidence[0].gaia_object_id == fiscal_state.fiscal_state_id
    assert response.evidence[0].metric == "debt_burden"


def test_analyst_answers_bitemporal_question_without_future_revision(session):
    seed_states(session)
    state = session.scalar(select(State).where(State.code == "LA"))
    assert state is not None
    first = _source(session, "b" * 64)
    second = _source(session, "c" * 64)
    second.supersedes_document_id = first.id
    effective = datetime(2026, 6, 30, 12, 0, tzinfo=UTC)
    publish_domain_claim(
        session,
        domain="debt",
        state_id=state.id,
        source_document_id=first.id,
        fiscal_period="2026Q2",
        metric="total_debt_stock",
        value=Decimal("100"),
        value_text="100",
        unit="naira",
        currency="NGN",
        effective_at=effective,
        published_at=datetime(2026, 7, 15, 12, 0, tzinfo=UTC),
        human_reviewed=True,
        reconciled=True,
    )
    publish_domain_claim(
        session,
        domain="debt",
        state_id=state.id,
        source_document_id=second.id,
        fiscal_period="2026Q2",
        metric="total_debt_stock",
        value=Decimal("120"),
        value_text="120",
        unit="naira",
        currency="NGN",
        effective_at=effective,
        published_at=datetime(2026, 8, 15, 12, 0, tzinfo=UTC),
        human_reviewed=True,
        reconciled=True,
    )
    session.commit()

    response = gaia_analyst(
        session,
        question="What did Gaia know about Lagos debt as of 2026-08-01?",
        year=2026,
    )
    assert response.intent == "temporal_metric"
    assert response.status == "answered"
    assert "100 NGN" in response.answer
    assert "120 NGN" not in response.answer
    assert response.evidence[0].source_sha256 == first.sha256


def test_state_code_does_not_match_inside_unrelated_word(session):
    seed_states(session)
    response = gaia_analyst(
        session,
        question="What changed in the latest published FAAC data for 2026?",
        year=2026,
    )
    assert response.intent != "ledger_metric"
    assert response.intent != "temporal_metric"
