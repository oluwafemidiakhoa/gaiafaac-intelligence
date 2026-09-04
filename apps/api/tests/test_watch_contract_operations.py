from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select

from gaiafaac_api.database.customer_models import OrganizationAlert
from gaiafaac_api.database.enums import SubscriptionStatus
from gaiafaac_api.database.evidence_room_models import EvidenceRoom
from gaiafaac_api.database.models import State, Subscription, User
from gaiafaac_api.database.session import get_session
from gaiafaac_api.database.watch_contract_models import (
    FiscalWatchContract,
    FiscalWatchContractDelivery,
    FiscalWatchContractMatch,
    FiscalWatchContractReview,
)
from gaiafaac_api.main import app
from gaiafaac_api.services.watch_contract_operations import ensure_operational_reviews


def _client(session) -> TestClient:
    app.dependency_overrides[get_session] = lambda: session
    return TestClient(app)


def _register(client: TestClient, email: str) -> str:
    response = client.post(
        "/api/v1/account/register",
        json={
            "full_name": "Watch Operator",
            "email": email,
            "password": "a-long-secure-password",
            "organization_name": f"Watch Operations {email}",
        },
    )
    assert response.status_code == 201
    return response.json()["token"]


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _activate_team(session, email: str) -> User:
    user = session.scalar(select(User).where(User.email == email))
    assert user is not None and user.organization_id is not None
    session.add(
        Subscription(
            organization_id=user.organization_id,
            status=SubscriptionStatus.ACTIVE,
            plan_code="team",
            external_customer_id=f"cus_{user.organization_id.hex[:12]}",
            external_subscription_id=f"sub_{user.organization_id.hex[:12]}",
        )
    )
    session.commit()
    return user


def _room(client: TestClient, headers: dict[str, str]) -> str:
    response = client.post(
        "/api/v1/evidence-rooms",
        headers=headers,
        json={
            "title": "Edo treasury monitoring decision",
            "decision_question": "Should this decision remain current after governed changes?",
            "jurisdictions": ["Edo"],
            "evidence_domains": ["FAAC"],
            "baseline_date": "2026-09-04",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_watch_operational_review_is_idempotent_tenant_scoped_and_does_not_clear_evidence_review(
    session,
):
    client = _client(session)
    try:
        owner_email = "watch-ops-owner@example.com"
        outsider_email = "watch-ops-outsider@example.com"
        owner_token = _register(client, owner_email)
        outsider_token = _register(client, outsider_email)
        owner = _activate_team(session, owner_email)
        outsider = _activate_team(session, outsider_email)
        assert owner.organization_id is not None
        room_id = _room(client, _headers(owner_token))

        created = client.post(
            "/api/v1/fiscal-watch-contracts",
            headers=_headers(owner_token),
            json={
                "room_id": room_id,
                "name": "Edo treasury SLA",
                "state_codes": ["ED"],
                "event_types": ["source_revised"],
                "minimum_severity": "watch",
                "escalation_after_minutes": 60,
            },
        )
        assert created.status_code == 201
        contract_id = created.json()["id"]

        state = State(
            name="Edo Test Operations",
            code="ED",
            slug="edo-test-operations",
            geopolitical_zone="South South",
            capital="Benin City",
            is_fct=False,
        )
        session.add(state)
        session.flush()
        alert = OrganizationAlert(
            organization_id=owner.organization_id,
            state_id=state.id,
            event_key="watch-ops-source-revised",
            source_kind="publication",
            event_type="source_revised",
            severity="material",
            occurred_at=datetime.now(UTC),
            payload={"headline": "Official source revision", "detail": "Retained source changed."},
        )
        session.add(alert)
        session.flush()
        contract = session.get(FiscalWatchContract, contract_id)
        assert contract is not None
        match = FiscalWatchContractMatch(
            contract_id=contract.id,
            organization_id=owner.organization_id,
            room_id=contract.room_id,
            organization_alert_id=alert.id,
        )
        session.add(match)
        session.flush()

        assert ensure_operational_reviews(session, contract, [match]) == 1
        assert ensure_operational_reviews(session, contract, [match]) == 0
        room = session.get(EvidenceRoom, contract.room_id)
        assert room is not None
        room.review_required = True
        session.commit()

        reviews = client.get(
            f"/api/v1/fiscal-watch-contracts/{contract_id}/reviews",
            headers=_headers(owner_token),
        )
        assert reviews.status_code == 200
        assert len(reviews.json()) == 1
        review = reviews.json()[0]
        assert review["status"] == "open"
        assert len(review["deliveries"]) == 1
        assert review["deliveries"][0]["channel"] == "in_app"
        assert review["deliveries"][0]["status"] == "delivered"

        outsider_reviews = client.get(
            f"/api/v1/fiscal-watch-contracts/{contract_id}/reviews",
            headers=_headers(outsider_token),
        )
        assert outsider_reviews.status_code == 404

        bad_assignment = client.patch(
            f"/api/v1/fiscal-watch-contracts/reviews/{review['id']}/assign",
            headers=_headers(owner_token),
            json={"assigned_user_id": str(outsider.id)},
        )
        assert bad_assignment.status_code == 422

        review_row = session.get(FiscalWatchContractReview, review["id"])
        assert review_row is not None
        review_row.due_at = datetime.now(UTC) - timedelta(minutes=1)
        session.commit()
        escalated = client.post(
            "/api/v1/fiscal-watch-contracts/reviews/escalate",
            headers=_headers(owner_token),
        )
        assert escalated.status_code == 200
        assert escalated.json()["escalated_count"] == 1
        repeated = client.post(
            "/api/v1/fiscal-watch-contracts/reviews/escalate",
            headers=_headers(owner_token),
        )
        assert repeated.status_code == 200
        assert repeated.json()["escalated_count"] == 0

        acknowledged = client.post(
            f"/api/v1/fiscal-watch-contracts/reviews/{review['id']}/acknowledge",
            headers=_headers(owner_token),
        )
        assert acknowledged.status_code == 200
        assert acknowledged.json()["status"] == "acknowledged"

        resolved = client.post(
            f"/api/v1/fiscal-watch-contracts/reviews/{review['id']}/resolve",
            headers=_headers(owner_token),
            json={"resolution_note": "Operations reviewed the delivery and routed the decision for re-review."},
        )
        assert resolved.status_code == 200
        assert resolved.json()["status"] == "resolved"
        assert resolved.json()["resolution_note"].startswith("Operations reviewed")

        session.refresh(room)
        assert room.review_required is True
        assert session.scalar(select(FiscalWatchContractDelivery)) is not None
    finally:
        app.dependency_overrides.clear()
