from datetime import UTC, datetime

from gaiafaac_api.database.models import Organization
from gaiafaac_api.services.api_keys import (
    authenticate_api_key,
    generate_api_key,
    record_request,
    requests_last_24h,
)


def _org(session):
    org = Organization(name="Acme", slug="acme")
    session.add(org)
    session.flush()
    return org


def test_generate_and_authenticate_roundtrip(session):
    org = _org(session)
    key, raw = generate_api_key(session, organization_id=org.id, name="prod", plan_code="api")
    assert raw.startswith("gfk_")
    assert key.key_prefix == raw[:12]
    found = authenticate_api_key(session, raw)
    assert found is not None
    assert found.id == key.id


def test_rejects_invalid_and_revoked_keys(session):
    org = _org(session)
    key, raw = generate_api_key(session, organization_id=org.id, name="prod", plan_code="api")
    assert authenticate_api_key(session, "gfk_not-real") is None
    assert authenticate_api_key(session, "no-prefix") is None
    key.revoked_at = datetime.now(UTC)
    session.flush()
    assert authenticate_api_key(session, raw) is None


def test_request_counting(session):
    org = _org(session)
    key, _raw = generate_api_key(session, organization_id=org.id, name="prod", plan_code="api")
    assert requests_last_24h(session, key) == 0
    record_request(session, key, "/api/v1/data/months", 200)
    record_request(session, key, "/api/v1/data/months", 200)
    assert requests_last_24h(session, key) == 2
    assert key.last_used_at is not None
