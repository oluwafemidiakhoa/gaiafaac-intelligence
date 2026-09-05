from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import select

from gaiafaac_api.database.enums import ReportedUnit, SourceStatus, VerificationStatus
from gaiafaac_api.database.models import ReportingPeriod, SourceDocument, State, StateAllocation
from gaiafaac_api.database.seeds import seed_states
from gaiafaac_api.services.fiscal_domain_claims import publish_domain_claim
from gaiafaac_api.services.gaia_analyst_igr import gaia_analyst


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
        sha256="b" * 64,
        mime_type="application/pdf",
        source_status=SourceStatus.APPROVED,
        is_demo=False,
    )
    session.add(source)
    session.flush()
    all_states = session.scalars(select(State)).all()
    for other in all_states:
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


def _source(session, *, name: str = "National Bureau of Statistics", sha: str = "a" * 64):
    source = SourceDocument(
        source_organization=name,
        original_filename="igr.xlsx",
        storage_path="igr.xlsx",
        sha256=sha,
        mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        source_status=SourceStatus.APPROVED,
        is_demo=False,
    )
    session.add(source)
    session.flush()
    return source


def _record(
    session,
    *,
    state: State,
    source: SourceDocument,
    period: str,
    amount: str,
) -> None:
    year = int(period[:4])
    quarter = int(period[-1]) if "Q" in period else None
    if quarter is None:
        observed = datetime(year, 12, 31, 12, 0, tzinfo=UTC)
    else:
        ends = {1: (3, 31), 2: (6, 30), 3: (9, 30), 4: (12, 31)}
        observed = datetime(year, *ends[quarter], 12, 0, tzinfo=UTC)
    publish_domain_claim(
        session,
        domain="igr",
        state_id=state.id,
        source_document_id=source.id,
        fiscal_period=period,
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


def test_gaia_analyst_answers_exact_year_state_igr_without_faac(session):
    seed_states(session)
    lagos = session.scalars(select(State).where(State.slug == "lagos")).one()
    source = _source(session)
    _record(session, state=lagos, source=source, period="2024", amount="1000000.00")
    session.flush()

    result = gaia_analyst(session, question="What is Lagos IGR in 2024?", year=2024)

    assert result.intent == "igr_state"
    assert result.status == "answered"
    assert result.evidence[0].evidence_domain == "igr"
    assert result.evidence[0].source_sha256 == "a" * 64
    assert result.evidence[0].source_organization == "National Bureau of Statistics"
    assert "NGN 1,000,000.00" in result.answer


def test_gaia_analyst_latest_igr_uses_latest_governed_period_not_year_control(session):
    seed_states(session)
    lagos = session.scalars(select(State).where(State.slug == "lagos")).one()
    source = _source(session)
    _record(session, state=lagos, source=source, period="2024", amount="100.00")
    _record(session, state=lagos, source=source, period="2025Q1", amount="30.00")
    session.flush()

    result = gaia_analyst(
        session,
        question="What is the latest published IGR for Lagos?",
        year=2026,
    )

    assert result.intent == "igr_latest"
    assert result.status == "answered"
    assert result.evidence[0].period_label == "2025 Q1"
    assert "NGN 30.00" in result.answer


def test_gaia_analyst_latest_igr_preserves_non_nbs_source_scope(session):
    seed_states(session)
    lagos = session.scalars(select(State).where(State.slug == "lagos")).one()
    nbs = _source(session, name="National Bureau of Statistics", sha="a" * 64)
    other = _source(session, name="Lagos State Internal Revenue Service", sha="c" * 64)
    _record(session, state=lagos, source=nbs, period="2024", amount="100.00")
    _record(session, state=lagos, source=other, period="2025", amount="150.00")
    session.flush()

    result = gaia_analyst(
        session,
        question="What is the latest published IGR for Lagos?",
        year=2026,
    )

    assert result.status == "answered"
    assert result.evidence[0].period_label == "2025 annual"
    assert result.evidence[0].source_organization == "Lagos State Internal Revenue Service"
    assert result.evidence[0].source_sha256 == "c" * 64


def test_gaia_analyst_ranks_only_a_common_igr_period(session):
    seed_states(session)
    states = list(session.scalars(select(State).order_by(State.name)).all())[:3]
    source = _source(session)
    _record(session, state=states[0], source=source, period="2024", amount="300.00")
    _record(session, state=states[1], source=source, period="2024", amount="200.00")
    _record(session, state=states[2], source=source, period="2024", amount="100.00")
    _record(session, state=states[0], source=source, period="2024Q1", amount="999.00")
    session.flush()

    result = gaia_analyst(session, question="Which states had the highest IGR in 2024?", year=2024)

    assert result.intent == "igr_top"
    assert result.status == "answered"
    assert len(result.evidence) == 3
    assert all(item.period_label == "2024 annual" for item in result.evidence)
    assert result.evidence[0].value == "NGN 300.00"


def test_gaia_analyst_does_not_compare_mismatched_igr_periods(session):
    seed_states(session)
    rivers = session.scalars(select(State).where(State.slug == "rivers")).one()
    lagos = session.scalars(select(State).where(State.slug == "lagos")).one()
    source = _source(session)
    _record(session, state=rivers, source=source, period="2024", amount="300.00")
    _record(session, state=lagos, source=source, period="2024Q1", amount="100.00")
    session.flush()

    result = gaia_analyst(session, question="Compare Rivers and Lagos IGR in 2024", year=2024)

    assert result.intent == "igr_compare"
    assert result.status == "insufficient_data"
    assert result.evidence == []
    assert "No common published IGR period" in result.answer


def test_dependence_falls_back_to_canonical_igr_component_evidence(session):
    seed_states(session)
    lagos = session.scalars(select(State).where(State.slug == "lagos")).one()
    _published_faac_allocation(
        session, state=lagos, revenue_month=date(2026, 6, 1), net="60348388366.77"
    )
    igr_source = _source(session)
    _record(
        session,
        state=lagos,
        source=igr_source,
        period="2024",
        amount="1261556415048.56",
    )
    session.flush()

    result = gaia_analyst(session, question="What is the FAAC dependence for Lagos?", year=2026)

    assert result.intent == "ledger_metric"
    assert result.status == "insufficient_data"
    assert "does not yet calculate a single FAAC dependence ratio" in result.answer
    assert "NGN 60,348,388,366.77" in result.answer
    assert "NGN 1,261,556,415,048.56" in result.answer
    domains = {item.evidence_domain for item in result.evidence}
    assert domains == {"faac", "igr"}


def test_debt_pressure_fallback_only_cites_faac_not_igr(session):
    seed_states(session)
    lagos = session.scalars(select(State).where(State.slug == "lagos")).one()
    _published_faac_allocation(
        session, state=lagos, revenue_month=date(2026, 6, 1), net="60348388366.77"
    )
    igr_source = _source(session)
    _record(
        session,
        state=lagos,
        source=igr_source,
        period="2024",
        amount="1261556415048.56",
    )
    session.flush()

    result = gaia_analyst(
        session, question="What is the debt-service pressure for Lagos?", year=2026
    )

    assert result.intent == "ledger_metric"
    assert result.status == "insufficient_data"
    assert "no verified DMO debt evidence has been published yet" in result.answer
    assert "NGN 60,348,388,366.77" in result.answer
    assert "NGN 1,261,556,415,048.56" not in result.answer
    assert {item.evidence_domain for item in result.evidence} == {"faac"}


def test_ledger_metric_stays_a_dead_end_when_no_component_evidence_exists(session):
    seed_states(session)

    result = gaia_analyst(session, question="What is the FAAC dependence for Kano?", year=2026)

    assert result.intent == "ledger_metric"
    assert result.status == "insufficient_data"
    assert result.evidence == []
    assert result.answer == "No published Fiscal State is available for Kano."
