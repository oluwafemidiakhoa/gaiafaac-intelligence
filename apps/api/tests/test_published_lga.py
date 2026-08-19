from datetime import date
from decimal import Decimal

from sqlalchemy import select

from gaiafaac_api.database.enums import ExtractionStatus, VerificationStatus
from gaiafaac_api.database.lga_models import LocalGovernment, LocalGovernmentAllocation
from gaiafaac_api.database.models import ExtractionRun, ReportingPeriod, SourceDocument, State
from gaiafaac_api.database.seeds import seed_states
from gaiafaac_api.services.published_lga import published_lga_history, published_lgas_for_state


def _period(session, *, month: int, label: str) -> ReportingPeriod:
    period = ReportingPeriod(
        revenue_month=date(2026, month, 1),
        disbursement_month=date(2026, month, 1),
        reporting_label=label,
        is_demo=False,
        is_published=True,
    )
    session.add(period)
    session.flush()
    return period


def _source(session, period: ReportingPeriod) -> SourceDocument:
    source = SourceDocument(
        reporting_period_id=period.id,
        source_organization="Office of the Accountant-General of the Federation",
        source_url="https://example.test/oagf.pdf",
        original_filename="Disbursement.pdf",
        storage_path="archive/disbursement.pdf",
        sha256=(f"{period.revenue_month.month:x}" * 64)[:64],
        mime_type="application/pdf",
        is_demo=False,
    )
    session.add(source)
    session.flush()
    return source


def _run(session, source: SourceDocument) -> ExtractionRun:
    run = ExtractionRun(
        source_document_id=source.id,
        status=ExtractionStatus.COMPLETED,
        extractor_name="oagf_table_iv_lga",
        extractor_version="1",
        records_extracted=774,
    )
    session.add(run)
    session.flush()
    return run


def test_published_lga_state_returns_only_governed_records(session):
    seed_states(session)
    states = list(session.scalars(select(State).order_by(State.name)).all())
    first = states[0]
    second = states[1]
    period = _period(session, month=6, label="OAGF FAAC Disbursement - June 2026")
    source = _source(session, period)
    run = _run(session, source)

    first_lga = LocalGovernment(state_id=first.id, official_name="Alpha Council", slug="alpha-council")
    second_lga = LocalGovernment(state_id=second.id, official_name="Beta Council", slug="beta-council")
    session.add_all([first_lga, second_lga])
    session.flush()

    session.add_all(
        [
            LocalGovernmentAllocation(
                reporting_period_id=period.id,
                local_government_id=first_lga.id,
                source_document_id=source.id,
                extraction_run_id=run.id,
                total_net_allocation=Decimal("123456.78"),
                total_net_original="123,456.78",
                verification_status=VerificationStatus.HUMAN_VERIFIED,
                is_demo=False,
                is_published=True,
            ),
            LocalGovernmentAllocation(
                reporting_period_id=period.id,
                local_government_id=second_lga.id,
                source_document_id=source.id,
                extraction_run_id=run.id,
                total_net_allocation=Decimal("999.00"),
                total_net_original="999.00",
                verification_status=VerificationStatus.REQUIRES_REVIEW,
                is_demo=False,
                is_published=True,
            ),
        ]
    )
    session.flush()

    result = published_lgas_for_state(session, state_code=first.code.lower())

    assert result is not None
    assert result.state_code == first.code
    assert result.local_government_count == 1
    assert result.local_governments[0].local_government_slug == "alpha-council"
    assert result.local_governments[0].total_net_allocation == "123456.78"
    assert published_lgas_for_state(session, state_code=second.code) is None


def test_published_lga_history_is_state_scoped_and_latest_first(session):
    seed_states(session)
    state = session.scalars(select(State).order_by(State.name)).first()
    assert state is not None
    lga = LocalGovernment(state_id=state.id, official_name="Alpha Council", slug="alpha-council")
    session.add(lga)
    session.flush()

    for month, amount in ((5, "100.00"), (6, "120.00")):
        period = _period(session, month=month, label=f"OAGF FAAC Disbursement - {month}/2026")
        source = _source(session, period)
        run = _run(session, source)
        session.add(
            LocalGovernmentAllocation(
                reporting_period_id=period.id,
                local_government_id=lga.id,
                source_document_id=source.id,
                extraction_run_id=run.id,
                total_net_allocation=Decimal(amount),
                total_net_original=amount,
                verification_status=VerificationStatus.HUMAN_VERIFIED,
                is_demo=False,
                is_published=True,
            )
        )
    session.flush()

    history = published_lga_history(
        session,
        state_code=state.code,
        local_government_slug=lga.slug,
    )

    assert history is not None
    assert history.record_count == 2
    assert [record.total_net_allocation for record in history.allocations] == ["120.00", "100.00"]
    assert (
        published_lga_history(
            session,
            state_code="ZZ",
            local_government_slug=lga.slug,
        )
        is None
    )
