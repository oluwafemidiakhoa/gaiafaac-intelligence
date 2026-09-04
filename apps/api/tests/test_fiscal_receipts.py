from fastapi.testclient import TestClient
from sqlalchemy import select

from gaiafaac_api.database.enums import SubscriptionStatus
from gaiafaac_api.database.evidence_room_models import FiscalReceipt
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
            "full_name": "Decision Analyst",
            "email": email,
            "password": "a-long-secure-password",
            "organization_name": f"Decision Research {email}",
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
        source_url="https://example.test/source.pdf",
        original_filename="source.pdf",
        storage_path=f"archive/{sha}.pdf",
        sha256=sha,
        mime_type="application/pdf",
        is_demo=False,
    )
    session.add(source)
    session.commit()
    return source


def _decision_room(client: TestClient, headers: dict[str, str]) -> str:
    response = client.post(
        "/api/v1/evidence-rooms",
        headers=headers,
        json={
            "title": "Edo infrastructure facility FY2026",
            "description": "Committee diligence workspace.",
            "decision_question": "Can the committee defend the fiscal evidence boundary used for this facility?",
            "jurisdictions": ["Edo"],
            "evidence_domains": ["FAAC", "IGR"],
            "baseline_date": "2026-09-03",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_receipt_generation_is_idempotent_for_same_evidence_boundary(session):
    client = _client(session)
    try:
        token = _register(client, "receipt-owner@example.com")
        _activate_team(session, "receipt-owner@example.com")
        source = _source(session, "a" * 64)
        headers = _headers(token)
        room_id = _decision_room(client, headers)

        captured = client.post(
            f"/api/v1/evidence-rooms/{room_id}/evidence",
            headers=headers,
            json={"reference_kind": "source", "reference_id": source.sha256},
        )
        assert captured.status_code == 201

        first = client.post(
            f"/api/v1/decision-rooms/{room_id}/fiscal-receipts",
            headers=headers,
        )
        second = client.post(
            f"/api/v1/decision-rooms/{room_id}/fiscal-receipts",
            headers=headers,
        )
        assert first.status_code == 201
        assert second.status_code == 201
        assert first.json()["id"] == second.json()["id"]
        assert first.json()["receipt_sha256"] == second.json()["receipt_sha256"]
        assert len(first.json()["receipt_sha256"]) == 64
        assert first.json()["manifest"]["evidence_count"] == 1
        assert first.json()["manifest"]["decision_question"].startswith("Can the committee")
    finally:
        app.dependency_overrides.clear()


def test_adding_governed_evidence_changes_receipt_hash(session):
    client = _client(session)
    try:
        token = _register(client, "receipt-change@example.com")
        _activate_team(session, "receipt-change@example.com")
        first_source = _source(session, "b" * 64)
        second_source = _source(session, "c" * 64)
        headers = _headers(token)
        room_id = _decision_room(client, headers)

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
        assert second.json()["receipt_sha256"] != first.json()["receipt_sha256"]
        assert second.json()["manifest"]["evidence_count"] == 2
    finally:
        app.dependency_overrides.clear()


def test_private_receipt_is_strictly_organization_scoped(session):
    client = _client(session)
    try:
        owner_token = _register(client, "receipt-org-a@example.com")
        outsider_token = _register(client, "receipt-org-b@example.com")
        _activate_team(session, "receipt-org-a@example.com")
        _activate_team(session, "receipt-org-b@example.com")
        headers = _headers(owner_token)
        room_id = _decision_room(client, headers)
        receipt = client.post(
            f"/api/v1/decision-rooms/{room_id}/fiscal-receipts",
            headers=headers,
        )
        assert receipt.status_code == 201
        receipt_id = receipt.json()["id"]

        denied = client.get(
            f"/api/v1/fiscal-receipts/{receipt_id}",
            headers=_headers(outsider_token),
        )
        assert denied.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_public_verifier_exposes_hash_manifest_not_private_decision_context(session):
    client = _client(session)
    try:
        token = _register(client, "receipt-public@example.com")
        _activate_team(session, "receipt-public@example.com")
        source = _source(session, "d" * 64)
        headers = _headers(token)
        room_id = _decision_room(client, headers)
        client.post(
            f"/api/v1/evidence-rooms/{room_id}/evidence",
            headers=headers,
            json={"reference_kind": "source", "reference_id": source.sha256},
        )
        receipt = client.post(
            f"/api/v1/decision-rooms/{room_id}/fiscal-receipts",
            headers=headers,
        )
        receipt_id = receipt.json()["id"]

        verified = client.get(f"/api/v1/fiscal-receipts/{receipt_id}/verify")
        assert verified.status_code == 200
        body = verified.json()
        assert body["evidence_count"] == 1
        assert body["jurisdictions"] == ["Edo"]
        assert body["source_sha256s"] == [source.sha256]
        assert "decision_question" not in body
        assert "organization_id" not in body
        assert "created_by_user_id" not in body
        assert "notes" not in body
        assert any("does not certify" in item for item in body["limitations"])
    finally:
        app.dependency_overrides.clear()


def test_fiscal_receipt_model_rejects_mutation(session):
    client = _client(session)
    try:
        token = _register(client, "receipt-immutable@example.com")
        _activate_team(session, "receipt-immutable@example.com")
        headers = _headers(token)
        room_id = _decision_room(client, headers)
        response = client.post(
            f"/api/v1/decision-rooms/{room_id}/fiscal-receipts",
            headers=headers,
        )
        assert response.status_code == 201

        row = session.scalar(select(FiscalReceipt))
        assert row is not None
        row.receipt_sha256 = "0" * 64
        try:
            session.flush()
        except ValueError as exc:
            assert "immutable" in str(exc)
            session.rollback()
        else:
            raise AssertionError("Fiscal Receipt mutation unexpectedly succeeded")
    finally:
        app.dependency_overrides.clear()
