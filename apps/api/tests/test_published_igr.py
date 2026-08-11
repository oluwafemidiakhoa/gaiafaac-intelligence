from datetime import date
from decimal import Decimal

from sqlalchemy import select

from gaiafaac_api.database.enums import ReportedUnit, VerificationStatus
from gaiafaac_api.database.igr_models import IgrPeriodType, StateIgrRecord
from gaiafaac_api.database.models import SourceDocument, State
from gaiafaac_api.database.seeds import seed_states
from gaiafaac_api.services.published_igr import published_igr


def test_published_igr_returns_only_human_verified_published_records(session):
    seed_states(session)
    states = list(session.scalars(select(State).order_by(State.name)).all())
    first = states[0]
    second = states[1]

    source = SourceDocument(
        source_organization="National Bureau of Statistics",
        source_url="https://example.test/igr-2024.pdf",
        original_filename="igr-2024.pdf",
        storage_path="igr-2024.pdf",
        sha256="a" * 64,
        mime_type="application/pdf",
        publication_date=date(2025, 1, 15),
        is_demo=False,
    )
    session.add(source)
    session.flush()

    session.add_all(
        [
            StateIgrRecord(
                state_id=first.id,
                source_document_id=source.id,
                fiscal_year=2024,
                period_type=IgrPeriodType.ANNUAL,
                quarter=None,
                period_start=date(2024, 1, 1),
                period_end=date(2024, 12, 31),
                igr_amount=Decimal("123456789.10"),
                igr_amount_original="123,456,789.10",
                reported_unit=ReportedUnit.NAIRA,
                publication_date=date(2025, 1, 15),
                source_page=4,
                source_table="Table 2",
                verification_status=VerificationStatus.HUMAN_VERIFIED,
                is_demo=False,
                is_published=True,
            ),
            StateIgrRecord(
                state_id=second.id,
                source_document_id=source.id,
                fiscal_year=2024,
                period_type=IgrPeriodType.ANNUAL,
                quarter=None,
                period_start=date(2024, 1, 1),
                period_end=date(2024, 12, 31),
                igr_amount=Decimal("999.00"),
                igr_amount_original="999.00",
                reported_unit=ReportedUnit.NAIRA,
                verification_status=VerificationStatus.PENDING,
                is_demo=False,
                is_published=True,
            ),
        ]
    )
    session.flush()

    result = published_igr(session, year=2024)

    assert result.record_count == 1
    assert result.records[0].state_slug == first.slug
    assert result.records[0].igr_amount == "123456789.10"
    assert result.records[0].period_type == "annual"
    assert result.records[0].source.sha256 == "a" * 64


def test_published_igr_can_filter_by_state_slug(session):
    seed_states(session)
    state = session.scalars(select(State).order_by(State.name)).first()
    source = SourceDocument(
        source_organization="NBS",
        original_filename="q1.pdf",
        storage_path="q1.pdf",
        sha256="b" * 64,
        mime_type="application/pdf",
        is_demo=False,
    )
    session.add(source)
    session.flush()
    session.add(
        StateIgrRecord(
            state_id=state.id,
            source_document_id=source.id,
            fiscal_year=2025,
            period_type=IgrPeriodType.QUARTERLY,
            quarter=1,
            period_start=date(2025, 1, 1),
            period_end=date(2025, 3, 31),
            igr_amount=Decimal("1000.00"),
            igr_amount_original="1,000.00",
            reported_unit=ReportedUnit.NAIRA,
            verification_status=VerificationStatus.HUMAN_VERIFIED,
            is_demo=False,
            is_published=True,
        )
    )
    session.flush()

    match = published_igr(session, year=2025, state_slug=state.slug)
    miss = published_igr(session, year=2025, state_slug="not-a-state")

    assert match.record_count == 1
    assert match.records[0].quarter == 1
    assert miss.record_count == 0
    assert miss.records == []
