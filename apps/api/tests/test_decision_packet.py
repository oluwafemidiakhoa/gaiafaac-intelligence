from datetime import date
from decimal import Decimal

from sqlalchemy import select

from gaiafaac_api.database.enums import ReportedUnit, VerificationStatus
from gaiafaac_api.database.igr_models import IgrPeriodType, StateIgrRecord
from gaiafaac_api.database.models import ReportingPeriod, SourceDocument, State, StateAllocation
from gaiafaac_api.database.seeds import seed_states
from gaiafaac_api.services.decision_packet import decision_packet


def test_decision_packet_collects_pulse_watch_monthly_proofs_and_exact_year_igr(session):
    seed_states(session)
    state = session.scalars(select(State).where(State.is_fct.is_(False))).first()
    source = SourceDocument(
        source_organization="OAGF",
        original_filename="packet.pdf",
        storage_path="packet.pdf",
        sha256="d" * 64,
        mime_type="application/pdf",
        is_demo=False,
    )
    igr_source = SourceDocument(
        source_organization="NBS",
        original_filename="igr.zip",
        storage_path="igr.zip",
        sha256="e" * 64,
        mime_type="application/zip",
        is_demo=False,
    )
    session.add_all([source, igr_source])
    session.flush()

    for month, net in ((1, Decimal("80")), (2, Decimal("120"))):
        period = ReportingPeriod(
            revenue_month=date(2026, month, 1),
            reporting_label=f"2026-{month:02d}",
            is_demo=False,
            is_published=True,
        )
        session.add(period)
        session.flush()
        session.add(
            StateAllocation(
                reporting_period_id=period.id,
                state_id=state.id,
                source_document_id=source.id,
                gross_total=Decimal("150"),
                total_deductions=Decimal("30"),
                net_allocation=net,
                reported_unit=ReportedUnit.NAIRA,
                is_demo=False,
                is_published=True,
            )
        )

    session.add_all(
        [
            StateIgrRecord(
                state_id=state.id,
                source_document_id=igr_source.id,
                fiscal_year=2025,
                period_type=IgrPeriodType.ANNUAL,
                quarter=None,
                period_start=date(2025, 1, 1),
                period_end=date(2025, 12, 31),
                igr_amount=Decimal("500.00"),
                igr_amount_original="500.00",
                reported_unit=ReportedUnit.NAIRA,
                verification_status=VerificationStatus.HUMAN_VERIFIED,
                is_demo=False,
                is_published=True,
            ),
            StateIgrRecord(
                state_id=state.id,
                source_document_id=igr_source.id,
                fiscal_year=2026,
                period_type=IgrPeriodType.ANNUAL,
                quarter=None,
                period_start=date(2026, 1, 1),
                period_end=date(2026, 12, 31),
                igr_amount=Decimal("700.00"),
                igr_amount_original="700.00",
                reported_unit=ReportedUnit.NAIRA,
                verification_status=VerificationStatus.HUMAN_VERIFIED,
                is_demo=False,
                is_published=True,
            ),
        ]
    )

    session.flush()
    packet = decision_packet(session, state_slug=state.slug, year=2026)

    assert packet is not None
    assert packet.packet_version == "2"
    assert packet.state_slug == state.slug
    assert packet.months_published == 2
    assert packet.annual_net == "200.00"
    assert len(packet.months) == 2
    assert packet.months[0].proof_id.startswith(f"GF1-NG-{state.code}-202601-")
    assert packet.months[1].proof_path == f"/fiscal-proof/{state.slug}/2026-02-01"
    assert packet.months[0].source_sha256 == "d" * 64
    assert len(packet.watch_events) == 1
    assert packet.watch_events[0].kind == "large_monthly_move"
    assert len(packet.igr_records) == 1
    assert packet.igr_records[0].fiscal_year == 2026
    assert packet.igr_records[0].igr_amount == "700.00"
    assert packet.igr_records[0].source_sha256 == "e" * 64


def test_decision_packet_does_not_borrow_igr_from_another_year(session):
    seed_states(session)
    state = session.scalars(select(State).where(State.is_fct.is_(False))).first()
    faac_source = SourceDocument(
        source_organization="OAGF",
        original_filename="packet.pdf",
        storage_path="packet.pdf",
        sha256="f" * 64,
        mime_type="application/pdf",
        is_demo=False,
    )
    igr_source = SourceDocument(
        source_organization="NBS",
        original_filename="igr.zip",
        storage_path="igr.zip",
        sha256="1" * 64,
        mime_type="application/zip",
        is_demo=False,
    )
    session.add_all([faac_source, igr_source])
    session.flush()

    period = ReportingPeriod(
        revenue_month=date(2026, 1, 1),
        reporting_label="2026-01",
        is_demo=False,
        is_published=True,
    )
    session.add(period)
    session.flush()
    session.add(
        StateAllocation(
            reporting_period_id=period.id,
            state_id=state.id,
            source_document_id=faac_source.id,
            net_allocation=Decimal("100.00"),
            reported_unit=ReportedUnit.NAIRA,
            is_demo=False,
            is_published=True,
        )
    )
    session.add(
        StateIgrRecord(
            state_id=state.id,
            source_document_id=igr_source.id,
            fiscal_year=2024,
            period_type=IgrPeriodType.ANNUAL,
            quarter=None,
            period_start=date(2024, 1, 1),
            period_end=date(2024, 12, 31),
            igr_amount=Decimal("500.00"),
            igr_amount_original="500.00",
            reported_unit=ReportedUnit.NAIRA,
            verification_status=VerificationStatus.HUMAN_VERIFIED,
            is_demo=False,
            is_published=True,
        )
    )
    session.flush()

    packet = decision_packet(session, state_slug=state.slug, year=2026)

    assert packet is not None
    assert packet.igr_records == []
    assert "No published, human-verified IGR evidence" in packet.igr_note


def test_decision_packet_returns_none_for_unknown_state(session):
    assert decision_packet(session, state_slug="not-a-state", year=2026) is None
