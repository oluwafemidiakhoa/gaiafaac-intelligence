from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from gaiafaac_api.database.models import ApiKey, ApiRequest

_PREFIX = "gfk_"


def _hash(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def generate_api_key(
    session: Session, *, organization_id: uuid.UUID, name: str, plan_code: str
) -> tuple[ApiKey, str]:
    """Create an API key. Returns the row and the plaintext key (shown once, never stored)."""
    raw = _PREFIX + secrets.token_urlsafe(32)
    key = ApiKey(
        organization_id=organization_id,
        name=name,
        key_prefix=raw[:12],
        key_hash=_hash(raw),
        plan_code=plan_code,
    )
    session.add(key)
    session.flush()
    return key, raw


def authenticate_api_key(session: Session, raw: str) -> ApiKey | None:
    """Return the active ApiKey for a plaintext key, or None if invalid/revoked."""
    if not raw or not raw.startswith(_PREFIX):
        return None
    return session.scalar(
        select(ApiKey).where(ApiKey.key_hash == _hash(raw), ApiKey.revoked_at.is_(None))
    )


def requests_last_24h(session: Session, api_key: ApiKey) -> int:
    since = datetime.now(UTC) - timedelta(hours=24)
    return (
        session.scalar(
            select(func.count())
            .select_from(ApiRequest)
            .where(ApiRequest.api_key_id == api_key.id, ApiRequest.created_at >= since)
        )
        or 0
    )


def record_request(session: Session, api_key: ApiKey, endpoint: str, status_code: int) -> None:
    session.add(ApiRequest(api_key_id=api_key.id, endpoint=endpoint, status_code=status_code))
    api_key.last_used_at = datetime.now(UTC)
    session.commit()
