from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import select

from gaiafaac_api.database.enums import ReportedUnit, SourceStatus, VerificationStatus
from gaiafaac_api.database.models import ReportingPeriod, SourceDocument, State, StateAllocation
from gaiafaac_api.database.seeds import seed_states
from gaiafaac_api.services.fiscal_domain_claims import publish_domain_claim
from gaiafaac_api.services.fiscal_ledger import publish_current_fiscal_state
from gaiafaac_api.services.gaia_analyst_institutional import gaia_analyst


def _source(session, sha: str, *, organization: str = "Official publisher"):
    source = SourceDocument(
        source_organization=organization,
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


def _published_faac_allocation(session, *, state: State, revenue_month: date, net: str) -> None:
    """Publish a complete 37-jurisdiction month (governed completeness rule) so
    `get_published_overview` resolves, with `state` carrying the given net allocation."""
    published_at = datetime.combine(revenue_month, datetime.min.time(), tzinfo=UTC)
    period = ReportingPeriod(
        revenue_month=revenue_month,
        reporting_label=revenue_month.strftime("%B %Y allocation"),
        is_demo=False,
        is_published=True,
        published_at=published_at,
        verification_status=VerificationStatus.HUMAN_VERIFIED,
        source_status=SourceStatus.APPROVED,
    )
    session.add(period)
    session.flush()
    source = SourceDocument(
        reporting_period_id=period.id,
        source_organization="OAGF",
        original_filename="allocation.pdf",
        storage_path="allocation.pdf",
        sha256="d" * 64,
        mime_type="application/pdf",
        source_status=SourceStatus.APPROVED,
        is_demo=False,
    )
    session.add(source)
    session.flush()
    for other in session.scalars(select(State)).all():
        session.add(
            StateAllocation(
                reporting_period_id=period.id,
                state_id=other.id,
                source_document_id=source.id,
                net_allocation=Decimal(net) if other.id == state.id else Decimal("1000000.00"),
                reported_unit=ReportedUnit.NAIRA,
                verification_status=VerificationStatus.HUMAN_VERIFIED,
                reviewed_at=published_at,
                is_demo=False,
                is_published=True,
                published_at=published_at,
            )
        )
    session.flush()


def _published_igr_record(session, *, state: State, year: int, amount: str) -> None:
    source = _source(
        session,
        "e" * 64,
        organization="National Bureau of Statistics",
    )
    observed = datetime(year, 12, 31, 12, 0, tzinfo=UTC)
    publish_domain_claim(
        session,
        domain="igr",
        state_id=state.id,
        source_document_id=source.id,
        fiscal_period=str(year),
        metric="igr",
        value=Decimal(amount),
        value_text=amount,
        unit="currency",
        currency="NGN",
        effective_at=observed,
        published_at=observed,
        human_reviewed=True,
        reconciled=True,
    )


def test_dependence_falls_back_to_component_evidence_without_a_fiscal_state(session):
    seed_states(session)
    lagos = session.scalar(select(State).where(State.code == "LA"))
    assert lagos is not None
    _published_faac_allocation(
        session, state=lagos, revenue_month=date(2026, 6, 1), net="60348388366.77"
    )
    _published_igr_record(session, state=lagos, year=2024, amount="1261556415048.56")
    session.commit()

    result = gaia_analyst(session, question="How dependent is Lagos on FAAC?", year=2026)

    assert result.intent == "ledger_metric"
    assert result.status == "insufficient_data"
    assert "does not yet calculate a single FAAC dependence ratio" in result.answer
    assert "NGN 60,348,388,366.77" in result.answer
    assert "NGN 1,261,556,415,048.56" in result.answer
    domains = {item.evidence_domain for item in result.evidence}
    assert domains == {"faac", "igr"}


def test_debt_burden_fallback_only_cites_faac_not_igr(session):
    seed_states(session)
    lagos = session.scalar(select(State).where(State.code == "LA"))
    assert lagos is not None
    _published_faac_allocation(
        session, state=lagos, revenue_month=date(2026, 6, 1), net="60348388366.77"
    )
    _published_igr_record(session, state=lagos, year=2024, amount="1261556415048.56")
    session.commit()

    result = gaia_analyst(
        session, question="How much debt does Lagos carry relative to revenue?", year=2026
    )

    assert result.intent == "ledger_metric"
    assert result.status == "insufficient_data"
    assert "the additional evidence domain this ratio needs" in result.answer
    assert "NGN 60,348,388,366.77" in result.answer
    assert "NGN 1,261,556,415,048.56" not in result.answer
    assert {item.evidence_domain for item in result.evidence} == {"faac"}


def test_ledger_metric_stays_a_dead_end_when_no_component_evidence_exists(session):
    seed_states(session)

    result = gaia_analyst(session, question="How dependent is Kano on FAAC?", year=2026)

    assert result.intent == "ledger_metric"
    assert result.status == "insufficient_data"
    assert result.evidence == []
    assert result.answer == "No published Fiscal State is available for Kano."
