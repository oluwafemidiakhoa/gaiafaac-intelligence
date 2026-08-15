from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.customer_models import CustomerSession
from gaiafaac_api.database.models import User

_SESSION_TTL = timedelta(days=14)


def _digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _expired(value: datetime) -> bool:
    now = datetime.now(UTC)
    if value.tzinfo is None:
        now = now.replace(tzinfo=None)
    return value <= now


def create_customer_session(session: Session, user: User) -> tuple[CustomerSession, str]:
    raw = "gfs_" + secrets.token_urlsafe(40)
    row = CustomerSession(
        user_id=user.id,
        token_hash=_digest(raw),
        expires_at=datetime.now(UTC) + _SESSION_TTL,
        last_seen_at=datetime.now(UTC),
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row, raw


def authenticate_customer_session(session: Session, raw: str) -> User | None:
    if not raw or not raw.startswith("gfs_"):
        return None
    row = session.scalar(
        select(CustomerSession).where(CustomerSession.token_hash == _digest(raw))
    )
    if row is None or _expired(row.expires_at):
        return None
    user = session.get(User, row.user_id)
    if user is None or not user.is_active:
        return None
    row.last_seen_at = datetime.now(UTC)
    session.commit()
    return user


def revoke_customer_session(session: Session, raw: str) -> None:
    row = session.scalar(
        select(CustomerSession).where(CustomerSession.token_hash == _digest(raw))
    )
    if row is not None:
        session.delete(row)
        session.commit()
