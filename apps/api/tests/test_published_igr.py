from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select

from gaiafaac_api.database.enums import SourceStatus
from gaiafaac_api.database.models import SourceDocument, State
from gaiafaac_api.database.seeds import seed_states
from gaiafaac_api.services.fiscal_domain_claims import publish_domain_claim
from gaiafaac_api.services.published_igr import latest_published_igr, published_igr


def _source(session, *, name: str, sha: str) -> SourceDocument:
    source = SourceDocument(
        source_organization=name,
        source_url=f"https://example.test/{sha[:4]}",
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


def _claim(
    session,
    *,
    state: State,
    source: SourceDocument,
    period: str,
    amount: str,
    human_reviewed: bool = True,
) -> None:
    year = int(period[:4])
    quarter = int(period[-1]) if "Q" in period else None
    month = 3 * quarter if quarter is not None else 12
    day = 31 if month in {3, 12} else 30
    observed = datetime(year, month, day, 12, 0, tzinfo=UTC)
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
        source_page=4,
        source_table="IGR",
        human_reviewed=human_reviewed,
        reconciled=True,
    )


def test_published_igr_returns_only_verified_canonical_claims(session):
    seed_states(session)
    states = list(session.scalars(select(State).order_by(State.name)).all())
    source = _source(session, name="National Bureau of Statistics", sha="a" * 64)
    _claim(session, state=states[0], source=source, period="2024", amount="123456789.10")
    _claim(
        session,
        state=states[1],
        source=source,
        period="2024",
        amount="999.00",
        human_reviewed=False,
    )
    session.flush()

    result = published_igr(session, year=2024)

    assert result.record_count == 1
    assert result.records[0].state_slug == states[0].slug
    assert result.records[0].igr_amount == "123456789.10"
    assert result.records[0].period_type == "annual"
    assert result.records[0].source.sha256 == "a" * 64


def test_published_igr_can_filter_by_state_slug(session):
    seed_states(session)
    state = session.scalars(select(State).order_by(State.name)).first()
    assert state is not None
    source = _source(session, name="NBS", sha="b" * 64)
    _claim(session, state=state, source=source, period="2025Q1", amount="1000.00")
    session.flush()

    match = published_igr(session, year=2025, state_slug=state.slug)
    miss = published_igr(session, year=2025, state_slug="not-a-state")

    assert match.record_count == 1
    assert match.records[0].quarter == 1
    assert miss.record_count == 0
    assert miss.records == []


def test_latest_published_igr_uses_latest_canonical_period_without_cross_state_leakage(session):
    seed_states(session)
    states = list(session.scalars(select(State).order_by(State.name)).all())
    first = states[0]
    second = states[1]
    source = _source(session, name="NBS", sha="c" * 64)
    _claim(session, state=first, source=source, period="2024", amount="100.00")
    _claim(session, state=first, source=source, period="2025Q1", amount="30.00")
    _claim(session, state=second, source=source, period="2026", amount="999.00")
    session.flush()

    latest = latest_published_igr(session, state_slug=first.slug)

    assert latest is not None
    assert latest.state_slug == first.slug
    assert latest.fiscal_year == 2025
    assert latest.quarter == 1
    assert latest.igr_amount == "30.00"
    assert latest_published_igr(session, state_slug="not-a-state") is None
