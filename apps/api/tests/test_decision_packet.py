from datetime import date
from decimal import Decimal

from sqlalchemy import select

from gaiafaac_api.database.enums import ReportedUnit
from gaiafaac_api.database.models import ReportingPeriod, SourceDocument, State, StateAllocation
from gaiafaac_api.database.seeds import seed_states
from gaiafaac_api.services.decision_packet import decision_packet


def test_decision_packet_collects_pulse_watch_and_monthly_proofs(session):
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
    session.add(source)
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

    session.flush()
    packet = decision_packet(session, state_slug=state.slug, year=2026)

    assert packet is not None
    assert packet.state_slug == state.slug
    assert packet.months_published == 2
    assert packet.annual_net == "200.00"
    assert len(packet.months) == 2
    assert packet.months[0].proof_id.startswith(f"GF1-NG-{state.code}-202601-")
    assert packet.months[1].proof_path == f"/fiscal-proof/{state.slug}/2026-02-01"
    assert packet.months[0].source_sha256 == "d" * 64
    assert len(packet.watch_events) == 1
    assert packet.watch_events[0].kind == "large_monthly_move"


def test_decision_packet_returns_none_for_unknown_state(session):
    assert decision_packet(session, state_slug="not-a-state", year=2026) is None
