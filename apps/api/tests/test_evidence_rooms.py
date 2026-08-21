from fastapi.testclient import TestClient
from sqlalchemy import select

from gaiafaac_api.database.evidence_room_models import EvidenceRoomEvidence
from gaiafaac_api.database.enums import SubscriptionStatus
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
            "full_name": "Evidence Analyst",
            "email": email,
            "password": "a-long-secure-password",
            "organization_name": f"Evidence Research {email}",
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


def _source(session, sha: str = "e" * 64) -> SourceDocument:
    source = SourceDocument(
        source_organization="OAGF",
        source_url="https://example.test/oagf.pdf",
        original_filename="oagf.pdf",
        storage_path="archive/oagf.pdf",
        sha256=sha,
        mime_type="application/pdf",
        is_demo=False,
    )
    session.add(source)
    session.commit()
    return source


def test_evidence_rooms_require_team_or_api_plan(session):
    client = _client(session)
    try:
        token = _register(client, "free-room@example.com")
        response = client.get("/api/v1/evidence-rooms", headers=_headers(token))
        assert response.status_code == 403
        assert "Team or API" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_room_captures_immutable_source_while_notes_remain_editable(session):
    client = _client(session)
    try:
        token = _register(client, "room-owner@example.com")
        _activate_team(session, "room-owner@example.com")
        source = _source(session)
        headers = _headers(token)

        created = client.post(
            "/api/v1/evidence-rooms",
            headers=headers,
            json={
                "title": "Lagos fiscal review",
                "description": "Credit committee evidence case file.",
            },
        )
        assert created.status_code == 201
        room_id = created.json()["id"]

        captured = client.post(
            f"/api/v1/evidence-rooms/{room_id}/evidence",
            headers=headers,
            json={
                "reference_kind": "source",
                "reference_id": source.sha256,
            },
        )
        assert captured.status_code == 201
        evidence = captured.json()
        assert evidence["source_sha256"] == source.sha256
        assert len(evidence["record_sha256"]) == 64
        first_record_hash = evidence["record_sha256"]

        duplicate = client.post(
            f"/api/v1/evidence-rooms/{room_id}/evidence",
            headers=headers,
            json={
                "reference_kind": "source",
                "reference_id": source.sha256,
            },
        )
        assert duplicate.status_code == 201
        assert duplicate.json()["id"] == evidence["id"]
        assert duplicate.json()["record_sha256"] == first_record_hash

        note = client.post(
            f"/api/v1/evidence-rooms/{room_id}/notes",
            headers=headers,
            json={"body": "Initial analyst interpretation."},
        )
        assert note.status_code == 201
        note_id = note.json()["id"]
        edited = client.patch(
            f"/api/v1/evidence-rooms/{room_id}/notes/{note_id}",
            headers=headers,
            json={"body": "Updated analyst interpretation after committee review."},
        )
        assert edited.status_code == 200

        detail = client.get(f"/api/v1/evidence-rooms/{room_id}", headers=headers)
        assert detail.status_code == 200
        body = detail.json()
        assert body["evidence_count"] == 1
        assert body["note_count"] == 1
        assert body["evidence"][0]["record_sha256"] == first_record_hash
        assert body["notes"][0]["body"].startswith("Updated analyst")
    finally:
        app.dependency_overrides.clear()


def test_evidence_rooms_are_strictly_organization_scoped(session):
    client = _client(session)
    try:
        owner_token = _register(client, "room-org-a@example.com")
        outsider_token = _register(client, "room-org-b@example.com")
        _activate_team(session, "room-org-a@example.com")
        _activate_team(session, "room-org-b@example.com")

        created = client.post(
            "/api/v1/evidence-rooms",
            headers=_headers(owner_token),
            json={"title": "Private organization evidence room"},
        )
        assert created.status_code == 201
        room_id = created.json()["id"]

        denied = client.get(
            f"/api/v1/evidence-rooms/{room_id}",
            headers=_headers(outsider_token),
        )
        assert denied.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_captured_evidence_model_rejects_mutation(session):
    client = _client(session)
    try:
        token = _register(client, "immutable-room@example.com")
        _activate_team(session, "immutable-room@example.com")
        source = _source(session, "f" * 64)
        created = client.post(
            "/api/v1/evidence-rooms",
            headers=_headers(token),
            json={"title": "Immutable evidence test"},
        )
        room_id = created.json()["id"]
        response = client.post(
            f"/api/v1/evidence-rooms/{room_id}/evidence",
            headers=_headers(token),
            json={"reference_kind": "source", "reference_id": source.sha256},
        )
        assert response.status_code == 201

        row = session.scalar(select(EvidenceRoomEvidence))
        assert row is not None
        row.reference_id = "changed"
        try:
            session.flush()
        except ValueError as exc:
            assert "immutable" in str(exc)
            session.rollback()
        else:
            raise AssertionError("Captured evidence mutation unexpectedly succeeded")
    finally:
        app.dependency_overrides.clear()
