from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import select

from gaiafaac_api.database.enums import ReportedUnit
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
    state = session.scalars(select(State).limit(1)).first()
    period = ReportingPeriod(
        revenue_month=date(2024, 1, 1),
        reporting_label="OAGF Jan 2024",
        is_demo=False,
        is_published=True,
    )
    session.add(period)
    session.flush()
    source.reporting_period_id = period.id
    session.add(
        StateAllocation(
            reporting_period_id=period.id,
            state_id=state.id,
            source_document_id=source.id,
            net_allocation=Decimal("900"),
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
    finally:
        app.dependency_overrides.clear()
