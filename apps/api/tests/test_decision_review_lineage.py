import uuid

from fastapi.testclient import TestClient
from sqlalchemy import select

from gaiafaac_api.database.enums import SubscriptionStatus
from gaiafaac_api.database.evidence_room_models import EvidenceRoom
from gaiafaac_api.database.models import SourceDocument, Subscription, User
from gaiafaac_api.database.session import get_session
from gaiafaac_api.main import app


def _client(session) -> TestClient:
    app.dependency_overrides[get_session] = lambda: session
    return TestClient(app)


def _register(client: TestClient, email: str) -> str:
    response = client.post(
        "/api/v1/account/register",
        json={
            "full_name": "Decision Reviewer",
            "email": email,
            "password": "a-long-secure-password",
            "organization_name": f"Decision Review {email}",
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


def _source(session, sha: str) -> SourceDocument:
    source = SourceDocument(
        source_organization="OAGF",
        source_url=f"https://example.test/{sha}.pdf",
        original_filename=f"{sha}.pdf",
        storage_path=f"archive/{sha}.pdf",
        sha256=sha,
        mime_type="application/pdf",
        is_demo=False,
    )
    session.add(source)
    session.commit()
    return source


def _room(client: TestClient, headers: dict[str, str]) -> str:
    response = client.post(
        "/api/v1/evidence-rooms",
        headers=headers,
        json={
            "title": "Edo credit committee decision",
            "decision_question": "Should the committee reopen this fiscal decision?",
            "jurisdictions": ["Edo"],
            "evidence_domains": ["FAAC"],
            "baseline_date": "2026-09-04",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_review_state_is_tenant_scoped(session):
    client = _client(session)
    try:
        owner_token = _register(client, "review-owner@example.com")
        outsider_token = _register(client, "review-outsider@example.com")
        _activate_team(session, "review-owner@example.com")
        _activate_team(session, "review-outsider@example.com")
        room_id = _room(client, _headers(owner_token))

        allowed = client.get(
            f"/api/v1/decision-rooms/{room_id}/review-state",
            headers=_headers(owner_token),
        )
        denied = client.get(
            f"/api/v1/decision-rooms/{room_id}/review-state",
            headers=_headers(outsider_token),
        )

        assert allowed.status_code == 200
        assert allowed.json()["review_required"] is False
        assert allowed.json()["latest_receipt_id"] is None
        assert denied.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_changed_evidence_creates_predecessor_receipt_lineage(session):
    client = _client(session)
    try:
        token = _register(client, "review-lineage@example.com")
        _activate_team(session, "review-lineage@example.com")
        headers = _headers(token)
        room_id = _room(client, headers)
        first_source = _source(session, "1" * 64)
        second_source = _source(session, "2" * 64)

        client.post(
            f"/api/v1/evidence-rooms/{room_id}/evidence",
            headers=headers,
            json={"reference_kind": "source", "reference_id": first_source.sha256},
        )
        first = client.post(
            f"/api/v1/decision-rooms/{room_id}/fiscal-receipts",
            headers=headers,
        )
        assert first.status_code == 201

        client.post(
            f"/api/v1/evidence-rooms/{room_id}/evidence",
            headers=headers,
            json={"reference_kind": "source", "reference_id": second_source.sha256},
        )
        second = client.post(
            f"/api/v1/decision-rooms/{room_id}/fiscal-receipts",
            headers=headers,
        )
        assert second.status_code == 201
        assert second.json()["id"] != first.json()["id"]
        assert second.json()["predecessor_receipt_id"] == first.json()["id"]
        assert (
            second.json()["manifest"]["lineage"]["predecessor_receipt_sha256"]
            == first.json()["receipt_sha256"]
        )
        assert (
            second.json()["manifest"]["content_sha256"]
            != first.json()["manifest"]["content_sha256"]
        )

        verified = client.get(f"/api/v1/fiscal-receipts/{second.json()['id']}/verify")
        assert verified.status_code == 200
        assert verified.json()["predecessor_receipt_id"] == first.json()["id"]
        assert verified.json()["predecessor_receipt_sha256"] == first.json()["receipt_sha256"]
        assert len(verified.json()["content_sha256"]) == 64
    finally:
        app.dependency_overrides.clear()


def test_successor_receipt_resolves_review_required_with_attribution(session):
    client = _client(session)
    try:
        email = "review-resolution@example.com"
        token = _register(client, email)
        user = _activate_team(session, email)
        headers = _headers(token)
        room_id = _room(client, headers)

        initial = client.post(
            f"/api/v1/decision-rooms/{room_id}/fiscal-receipts",
            headers=headers,
        )
        assert initial.status_code == 201

        room = session.scalar(select(EvidenceRoom).where(EvidenceRoom.id == uuid.UUID(room_id)))
        assert room is not None
        room.review_required = True
        session.commit()

        pending = client.get(
            f"/api/v1/decision-rooms/{room_id}/review-state",
            headers=headers,
        )
        assert pending.status_code == 200
        assert pending.json()["review_required"] is True

        successor = client.post(
            f"/api/v1/decision-rooms/{room_id}/fiscal-receipts",
            headers=headers,
        )
        assert successor.status_code == 201
        assert successor.json()["id"] != initial.json()["id"]
        assert successor.json()["predecessor_receipt_id"] == initial.json()["id"]

        resolved = client.get(
            f"/api/v1/decision-rooms/{room_id}/review-state",
            headers=headers,
        )
        assert resolved.status_code == 200
        body = resolved.json()
        assert body["review_required"] is False
        assert body["last_reviewed_at"] is not None
        assert body["reviewed_by_user_id"] == str(user.id)
        assert body["latest_receipt_id"] == successor.json()["id"]
    finally:
        app.dependency_overrides.clear()
