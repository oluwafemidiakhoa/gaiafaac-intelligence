from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select

from gaiafaac_api.database.enums import SourceStatus
from gaiafaac_api.database.models import SourceDocument, State
from gaiafaac_api.database.seeds import seed_states
from gaiafaac_api.services.canonical_igr import governed_igr_observations
from gaiafaac_api.services.fiscal_domain_claims import publish_domain_claim


def _source(session, *, organization: str, sha: str) -> SourceDocument:
    source = SourceDocument(
        source_organization=organization,
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


def _publish(
    session,
    *,
    state: State,
    source: SourceDocument,
    amount: str,
    published_at: datetime,
    human_reviewed: bool,
) -> None:
    publish_domain_claim(
        session,
        domain="igr",
        state_id=state.id,
        source_document_id=source.id,
        fiscal_period="2024",
        metric="igr",
        value=Decimal(amount),
        value_text=amount,
        unit="currency",
        currency="NGN",
        effective_at=published_at,
        published_at=published_at,
        human_reviewed=human_reviewed,
        reconciled=True,
    )


def test_partial_successor_does_not_hide_last_verified_igr(session):
    seed_states(session)
    lagos = session.scalar(select(State).where(State.slug == "lagos"))
    assert lagos is not None

    verified_source = _source(
        session,
        organization="National Bureau of Statistics (NBS)",
        sha="e" * 64,
    )
    partial_source = _source(
        session,
        organization="National Bureau of Statistics (NBS)",
        sha="f" * 64,
    )
    _publish(
        session,
        state=lagos,
        source=verified_source,
        amount="100.00",
        published_at=datetime(2025, 1, 10, 12, 0, tzinfo=UTC),
        human_reviewed=True,
    )
    _publish(
        session,
        state=lagos,
        source=partial_source,
        amount="110.00",
        published_at=datetime(2025, 1, 11, 12, 0, tzinfo=UTC),
        human_reviewed=False,
    )
    session.flush()

    observations = governed_igr_observations(session, state_slug="lagos", year=2024)

    assert len(observations) == 1
    assert observations[0].value == "100.00"
    assert observations[0].source_sha256 == "e" * 64


def test_verified_successor_replaces_prior_verified_igr(session):
    seed_states(session)
    lagos = session.scalar(select(State).where(State.slug == "lagos"))
    assert lagos is not None

    first_source = _source(session, organization="NBS", sha="1" * 64)
    revised_source = _source(session, organization="NBS", sha="2" * 64)
    _publish(
        session,
        state=lagos,
        source=first_source,
        amount="100.00",
        published_at=datetime(2025, 2, 10, 12, 0, tzinfo=UTC),
        human_reviewed=True,
    )
    _publish(
        session,
        state=lagos,
        source=revised_source,
        amount="120.00",
        published_at=datetime(2025, 2, 11, 12, 0, tzinfo=UTC),
        human_reviewed=True,
    )
    session.flush()

    observations = governed_igr_observations(session, state_slug="lagos", year=2024)

    assert len(observations) == 1
    assert observations[0].value == "120.00"
    assert observations[0].source_sha256 == "2" * 64


def test_verified_revision_after_partial_intermediate_becomes_only_current_igr(session):
    seed_states(session)
    lagos = session.scalar(select(State).where(State.slug == "lagos"))
    assert lagos is not None

    first_source = _source(session, organization="NBS", sha="3" * 64)
    partial_source = _source(session, organization="NBS", sha="4" * 64)
    final_source = _source(session, organization="NBS", sha="5" * 64)
    _publish(
        session,
        state=lagos,
        source=first_source,
        amount="100.00",
        published_at=datetime(2025, 3, 10, 12, 0, tzinfo=UTC),
        human_reviewed=True,
    )
    _publish(
        session,
        state=lagos,
        source=partial_source,
        amount="110.00",
        published_at=datetime(2025, 3, 11, 12, 0, tzinfo=UTC),
        human_reviewed=False,
    )
    _publish(
        session,
        state=lagos,
        source=final_source,
        amount="125.00",
        published_at=datetime(2025, 3, 12, 12, 0, tzinfo=UTC),
        human_reviewed=True,
    )
    session.flush()

    observations = governed_igr_observations(session, state_slug="lagos", year=2024)

    assert len(observations) == 1
    assert observations[0].value == "125.00"
    assert observations[0].source_sha256 == "5" * 64
