from datetime import UTC, date, datetime
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import select

from gaiafaac_api.database.enums import (
    EvidenceStatus,
    FiscalEventSeverity,
    ReportedUnit,
)
from gaiafaac_api.database.models import (
    Organization,
    ReportingPeriod,
    SourceDocument,
    State,
    StateAllocation,
)
from gaiafaac_api.database.seeds import seed_states
from gaiafaac_api.database.session import get_session
from gaiafaac_api.main import app
from gaiafaac_api.services.api_keys import generate_api_key
from gaiafaac_api.services.fiscal_institutional import publish_fiscal_event


def _publish_one_month(session):
    seed_states(session)
    source = SourceDocument(
        source_organization="OAGF",
        original_filename="x.pdf",
        storage_path="x",
        sha256="a" * 64,
        mime_type="application/pdf",
    )
    session.add(source)
    session.flush()
    states = session.scalars(select(State)).all()
    period = ReportingPeriod(
        revenue_month=date(2024, 1, 1),
        reporting_label="OAGF Jan 2024",
        is_demo=False,
        is_published=True,
    )
    session.add(period)
    session.flush()
    source.reporting_period_id = period.id
    for index, state in enumerate(states, start=1):
        session.add(
            StateAllocation(
                reporting_period_id=period.id,
                state_id=state.id,
                source_document_id=source.id,
                net_allocation=Decimal(900 + index),
                reported_unit=ReportedUnit.NAIRA,
                is_demo=False,
                is_published=True,
            )
        )
    session.flush()


def _key(session, plan):
    org = Organization(name="Acme", slug=f"acme-{plan}")
    session.add(org)
    session.flush()
    _key_row, raw = generate_api_key(session, organization_id=org.id, name="k", plan_code=plan)
    session.commit()
    return raw


def _client(session):
    app.dependency_overrides[get_session] = lambda: session
    return TestClient(app)


def test_requires_api_key(session):
    _publish_one_month(session)
    try:
        client = _client(session)
        assert client.get("/api/v1/data/months").status_code == 401
        assert (
            client.get("/api/v1/data/months", headers={"X-API-Key": "gfk_wrong"}).status_code == 401
        )
    finally:
        app.dependency_overrides.clear()


def test_non_api_plan_is_forbidden(session):
    _publish_one_month(session)
    raw = _key(session, "analyst")
    try:
        client = _client(session)
        assert client.get("/api/v1/data/months", headers={"X-API-Key": raw}).status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_api_plan_serves_data(session):
    _publish_one_month(session)
    raw = _key(session, "api")
    try:
        client = _client(session)
        response = client.get("/api/v1/data/months", headers={"X-API-Key": raw})
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["reporting_label"] == "OAGF Jan 2024"
        assert response.json()[0]["covered_states"] == 37
    finally:
        app.dependency_overrides.clear()


def test_api_plan_serves_incremental_fiscal_events(session):
    _publish_one_month(session)
    state = session.scalar(select(State).where(State.code == "LA"))
    assert state is not None
    first_detected = datetime(2026, 8, 20, 12, 0, tzinfo=UTC)
    second_detected = datetime(2026, 8, 21, 12, 0, tzinfo=UTC)
    publish_fiscal_event(
        session,
        state_id=state.id,
        event_type="faac_decline",
        severity=FiscalEventSeverity.MEDIUM,
        effective_at=first_detected,
        detected_at=first_detected,
        evidence_status=EvidenceStatus.VERIFIED,
        evidence_ids=["claim:first"],
        explanation="Observed decline from retained evidence.",
        calculation={"change_pct": "-8.5"},
    )
    publish_fiscal_event(
        session,
        state_id=state.id,
        event_type="source_revised",
        severity=FiscalEventSeverity.HIGH,
        effective_at=second_detected,
        detected_at=second_detected,
        evidence_status=EvidenceStatus.VERIFIED,
        evidence_ids=["claim:second"],
        explanation="A retained source revision changed governed evidence.",
    )
    session.commit()
    raw = _key(session, "api")
    try:
        client = _client(session)
        response = client.get(
            "/api/v1/data/events",
            headers={"X-API-Key": raw},
            params={
                "jurisdiction": "NG-LA",
                "detected_after": "2026-08-20T18:00:00Z",
            },
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["evidence"]["record_count"] == 1
        assert payload["data"][0]["event_type"] == "source_revised"
        assert payload["data"][0]["jurisdiction"]["code"] == "NG-LA"
    finally:
        app.dependency_overrides.clear()


def test_event_feed_rejects_naive_detected_after(session):
    _publish_one_month(session)
    raw = _key(session, "api")
    try:
        client = _client(session)
        response = client.get(
            "/api/v1/data/events",
            headers={"X-API-Key": raw},
            params={"detected_after": "2026-08-20T18:00:00"},
        )
        assert response.status_code == 422
        assert "timezone" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()
