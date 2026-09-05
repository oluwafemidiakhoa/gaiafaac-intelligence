from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import select

from gaiafaac_api.database.enums import (
    ReportedUnit,
    SourceStatus,
    VerificationStatus,
)
from gaiafaac_api.database.igr_models import IgrPeriodType, StateIgrRecord
from gaiafaac_api.database.models import SourceDocument, State
from gaiafaac_api.database.seeds import seed_states
from gaiafaac_api.services.canonical_igr import governed_igr_status
from gaiafaac_api.services.fiscal_domain_claims import publish_domain_claim
from gaiafaac_api.services.gaia_analyst_institutional import gaia_analyst


def _source(session, *, organization: str, sha: str) -> SourceDocument:
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


def _canonical_igr(session, *, state: State, source: SourceDocument, year: int, amount: str) -> None:
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


def test_terminal_nbs_status_and_ask_gaia_ignore_legacy_newer_row(session):
    """Regression: a newer legacy StateIgrRecord must never outrank the canonical ledger.

    This is the production inconsistency that previously allowed Terminal to show one NBS
    period while Ask Gaia silently returned a different period from the legacy table.
    """

    seed_states(session)
    lagos = session.scalar(select(State).where(State.slug == "lagos"))
    assert lagos is not None
    nbs = _source(
        session,
        organization="National Bureau of Statistics (NBS)",
        sha="a" * 64,
    )
    _canonical_igr(session, state=lagos, source=nbs, year=2024, amount="100.00")

    # Deliberately create a newer row in the old publication table. It is not a
    # FiscalClaim and therefore must not change either public surface.
    legacy_source = _source(session, organization="Legacy IGR Import", sha="b" * 64)
    session.add(
        StateIgrRecord(
            state_id=lagos.id,
            source_document_id=legacy_source.id,
            fiscal_year=2025,
            period_type=IgrPeriodType.ANNUAL,
            quarter=None,
            period_start=date(2025, 1, 1),
            period_end=date(2025, 12, 31),
            igr_amount=Decimal("999.00"),
            igr_amount_original="999.00",
            reported_unit=ReportedUnit.NAIRA,
            verification_status=VerificationStatus.HUMAN_VERIFIED,
            is_demo=False,
            is_published=True,
        )
    )
    session.flush()

    terminal_status = governed_igr_status(
        session,
        publisher_fragment="National Bureau of Statistics",
    )
    answer = gaia_analyst(
        session,
        question="What is the latest published IGR for Lagos?",
        year=2026,
    )

    assert terminal_status.is_live is True
    assert terminal_status.latest_period == "2024"
    assert terminal_status.published_record_count == 1
    assert answer.intent == "igr_latest"
    assert answer.status == "answered"
    assert answer.evidence[0].period_label == "2024 annual"
    assert answer.evidence[0].source_organization == "National Bureau of Statistics (NBS)"
    assert "NGN 100.00" in answer.answer
    assert "999.00" not in answer.answer


def test_ask_gaia_explicitly_preserves_newer_non_nbs_source_scope(session):
    seed_states(session)
    lagos = session.scalar(select(State).where(State.slug == "lagos"))
    assert lagos is not None
    nbs = _source(
        session,
        organization="National Bureau of Statistics (NBS)",
        sha="c" * 64,
    )
    state_source = _source(
        session,
        organization="Lagos State Internal Revenue Service",
        sha="d" * 64,
    )
    _canonical_igr(session, state=lagos, source=nbs, year=2024, amount="100.00")
    _canonical_igr(session, state=lagos, source=state_source, year=2025, amount="150.00")
    session.flush()

    nbs_status = governed_igr_status(
        session,
        publisher_fragment="National Bureau of Statistics",
    )
    answer = gaia_analyst(
        session,
        question="What is the latest published IGR for Lagos?",
        year=2026,
    )

    assert nbs_status.latest_period == "2024"
    assert answer.evidence[0].period_label == "2025 annual"
    assert answer.evidence[0].source_organization == "Lagos State Internal Revenue Service"
