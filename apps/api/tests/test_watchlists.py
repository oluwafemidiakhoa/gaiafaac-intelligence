from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import select

from gaiafaac_api.database.enums import ReportedUnit
from gaiafaac_api.database.models import ReportingPeriod, SourceDocument, State, StateAllocation
from gaiafaac_api.database.seeds import seed_states
from gaiafaac_api.database.session import get_session
from gaiafaac_api.main import app


def _client(session) -> TestClient:
    app.dependency_overrides[get_session] = lambda: session
    return TestClient(app)


def _register(client: TestClient) -> str:
    response = client.post(
        "/api/v1/account/register",
        json={
            "full_name": "Watch Analyst",
            "email": "watch@example.com",
            "password": "a-long-secure-password",
            "organization_name": "Watch Research",
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


def test_watchlist_alerts_filter_deterministic_fiscal_watch_events(session):
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
    session.commit()

    client = _client(session)
    try:
        token = _register(client)
        headers = _authorization(token)
        created = client.post(
            "/api/v1/watchlists",
            headers=headers,
            json={"state_code": watched_state.code},
        )
        assert created.status_code == 201

        response = client.get("/api/v1/watchlists/alerts?year=2026", headers=headers)
        assert response.status_code == 200
        body = response.json()
        assert body["watchlist_count"] == 1
        assert body["alert_count"] == 1
        assert body["alerts"][0]["state_code"] == watched_state.code
        assert body["alerts"][0]["kind"] == "large_monthly_move"
        assert body["alerts"][0]["change_pct"] == -60.0
        assert body["alerts"][0]["event_key"].endswith(":large_monthly_move")
        assert "not credit ratings" in body["note"]
    finally:
        app.dependency_overrides.clear()
