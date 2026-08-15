from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from gaiafaac_api.database.models import User
from gaiafaac_api.database.session import get_session
from gaiafaac_api.services.customer_sessions import authenticate_customer_session

DatabaseSession = Annotated[Session, Depends(get_session)]


def bearer_token(authorization: str | None) -> str:
    if not authorization:
        return ""
    scheme, _, token = authorization.partition(" ")
    return token.strip() if scheme.lower() == "bearer" else ""


def require_customer(
    session: DatabaseSession,
    authorization: Annotated[str | None, Header()] = None,
) -> User:
    user = authenticate_customer_session(session, bearer_token(authorization))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sign in to continue.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


CurrentCustomer = Annotated[User, Depends(require_customer)]
