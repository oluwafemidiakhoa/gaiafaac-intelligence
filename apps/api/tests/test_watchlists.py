from datetime import UTC, date, datetime
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import select

from gaiafaac_api.database.customer_models import CustomerAlert
from gaiafaac_api.database.enums import (
    EvidenceStatus,
    FiscalEventSeverity,
    ReportedUnit,
)
from gaiafaac_api.database.models import ReportingPeriod, SourceDocument, State, StateAllocation
from gaiafaac_api.database.seeds import seed_states
from gaiafaac_api.database.session import get_session
from gaiafaac_api.main import app
from gaiafaac_api.services.fiscal_institutional import publish_fiscal_event


def _client(session) -> TestClient:
    app.dependency_overrides[get_session] = lambda: session
    return TestClient(app)


def _register(client: TestClient, *, email: str = "watch@example.com") -> str:
    response = client.post(
        "/api/v1/account/register",
        json={
            "full_name": "Watch Analyst",
            "email": email,
            "password": "a-long-secure-password",
            "organization_name": f"Watch Research {email}",
        },
    )
    assert response.status_code == 201
    return response.json()["token"]


def _authorization(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _source(session) -> SourceDocument:
    source = SourceDocument(
        source_organization="OAGF",
        original_filename="watchlist.pdf",
        storage_path="watchlist.pdf",
        sha256="d" * 64,
        mime_type="application/pdf",
    )
    session.add(source)
    session.flush()
    return source


def _period(session, month: int) -> ReportingPeriod:
    period = ReportingPeriod(
        revenue_month=date(2026, month, 1),
        reporting_label=f"2026-{month:02d}",
        is_demo=False,
        is_published=True,
    )
    session.add(period)
    session.flush()
    return period


def _allocation(session, source, period, state, net: str) -> None:
    session.add(
        StateAllocation(
            reporting_period_id=period.id,
            state_id=state.id,
            source_document_id=source.id,
            gross_total=Decimal("100.00"),
            total_deductions=Decimal("10.00"),
            net_allocation=Decimal(net),
            reported_unit=ReportedUnit.NAIRA,
            is_demo=False,
            is_published=True,
        )
    )


def test_watchlists_require_customer_authentication(session):
    client = _client(session)
    try:
        response = client.get("/api/v1/watchlists")
        assert response.status_code == 401
        assert client.get("/api/v1/watchlists/alerts?year=2026").status_code == 401
    finally:
        app.dependency_overrides.clear()


def test_customer_can_add_list_and_remove_state_watchlist(session):
    seed_states(session)
    client = _client(session)
    try:
        token = _register(client)
        headers = _authorization(token)
        state = session.scalars(select(State).order_by(State.name)).first()
        assert state is not None

        empty = client.get("/api/v1/watchlists", headers=headers)
        assert empty.status_code == 200
        assert empty.json() == []

        created = client.post(
            "/api/v1/watchlists",
            headers=headers,
            json={"state_code": state.code.lower()},
        )
        assert created.status_code == 201
        assert created.json()["state_code"] == state.code

        duplicate = client.post(
            "/api/v1/watchlists",
            headers=headers,
            json={"state_code": state.code},
        )
        assert duplicate.status_code == 201
        assert duplicate.json()["id"] == created.json()["id"]

        listed = client.get("/api/v1/watchlists", headers=headers)
        assert listed.status_code == 200
        assert len(listed.json()) == 1

        removed = client.delete(
            f"/api/v1/watchlists/{created.json()['id']}", headers=headers
        )
        assert removed.status_code == 204
        assert client.get("/api/v1/watchlists", headers=headers).json() == []
    finally:
        app.dependency_overrides.clear()


def test_inbox_persists_fiscal_watch_and_lifecycle_events_idempotently(session):
    seed_states(session)
    states = list(session.scalars(select(State).where(State.is_fct.is_(False)).order_by(State.name)))
    assert len(states) >= 2
    watched_state, unwatched_state = states[:2]

    source = _source(session)
    january = _period(session, 1)
    february = _period(session, 2)
    _allocation(session, source, january, watched_state, "100.00")
    _allocation(session, source, february, watched_state, "40.00")
    _allocation(session, source, january, unwatched_state, "100.00")
    _allocation(session, source, february, unwatched_state, "20.00")
    publish_fiscal_event(
        session,
        state_id=watched_state.id,
        event_type="source_revised",
        severity=FiscalEventSeverity.MATERIAL,
        effective_at=datetime(2026, 2, 15, tzinfo=UTC),
        detected_at=datetime(2026, 2, 16, tzinfo=UTC),
        evidence_status=EvidenceStatus.VERIFIED,
        evidence_ids=["source-sha-1", "source-sha-2"],
        explanation="A revised official source was retained without rewriting prior evidence.",
    )
    publish_fiscal_event(
        session,
        state_id=unwatched_state.id,
        event_type="source_revised",
        severity=FiscalEventSeverity.MATERIAL,
        effective_at=datetime(2026, 2, 15, tzinfo=UTC),
        detected_at=datetime(2026, 2, 16, tzinfo=UTC),
        evidence_status=EvidenceStatus.VERIFIED,
        evidence_ids=["other-source"],
        explanation="This event belongs to an unwatched state.",
    )
    session.commit()

    client = _client(session)
    try:
        token = _register(client)
        headers = _authorization(token)
        assert (
            client.post(
                "/api/v1/watchlists",
                headers=headers,
                json={"state_code": watched_state.code},
            ).status_code
            == 201
        )

        first = client.get("/api/v1/watchlists/alerts?year=2026", headers=headers)
        assert first.status_code == 200
        body = first.json()
        assert body["watchlist_count"] == 1
        assert body["alert_count"] == 2
        assert body["unread_count"] == 2
        assert {item["source_kind"] for item in body["alerts"]} == {
            "fiscal_watch",
            "fiscal_event",
        }
        assert {item["state_code"] for item in body["alerts"]} == {watched_state.code}
        lifecycle = next(item for item in body["alerts"] if item["source_kind"] == "fiscal_event")
        assert lifecycle["event_type"] == "source_revised"
        assert lifecycle["evidence_ids"] == ["source-sha-1", "source-sha-2"]
        assert lifecycle["is_read"] is False

        second = client.get("/api/v1/watchlists/alerts?year=2026", headers=headers)
        assert second.status_code == 200
        assert second.json()["alert_count"] == 2
        assert len(session.scalars(select(CustomerAlert)).all()) == 2
    finally:
        app.dependency_overrides.clear()


def test_customer_can_mark_one_or_all_alerts_read_without_cross_account_access(session):
    seed_states(session)
    state = session.scalars(select(State).where(State.is_fct.is_(False)).order_by(State.name)).first()
    assert state is not None
    source = _source(session)
    january = _period(session, 1)
    february = _period(session, 2)
    _allocation(session, source, january, state, "100.00")
    _allocation(session, source, february, state, "40.00")
    publish_fiscal_event(
        session,
        state_id=state.id,
        event_type="fiscal_state_changed",
        severity=FiscalEventSeverity.NOTABLE,
        effective_at=datetime(2026, 2, 20, tzinfo=UTC),
        detected_at=datetime(2026, 2, 20, tzinfo=UTC),
        evidence_status=EvidenceStatus.VERIFIED,
        evidence_ids=["GFS-NG-TEST"],
        explanation="The published Fiscal State changed after governed evidence was updated.",
    )
    session.commit()

    client = _client(session)
    try:
        owner = _authorization(_register(client, email="owner@example.com"))
        other = _authorization(_register(client, email="other@example.com"))
        assert client.post(
            "/api/v1/watchlists", headers=owner, json={"state_code": state.code}
        ).status_code == 201

        inbox = client.get("/api/v1/watchlists/alerts?year=2026", headers=owner).json()
        assert inbox["unread_count"] == 2
        first_id = inbox["alerts"][0]["id"]

        assert client.post(f"/api/v1/watchlists/alerts/{first_id}/read", headers=other).status_code == 404
        assert client.post(f"/api/v1/watchlists/alerts/{first_id}/read", headers=owner).status_code == 204
        after_one = client.get("/api/v1/watchlists/alerts?year=2026", headers=owner).json()
        assert after_one["unread_count"] == 1
        assert sum(item["is_read"] for item in after_one["alerts"]) == 1

        assert client.post("/api/v1/watchlists/alerts/read-all?year=2026", headers=owner).status_code == 204
        after_all = client.get("/api/v1/watchlists/alerts?year=2026", headers=owner).json()
        assert after_all["unread_count"] == 0
        assert all(item["is_read"] for item in after_all["alerts"])
    finally:
        app.dependency_overrides.clear()
