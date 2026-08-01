import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from gaiafaac_api.config import get_settings
from gaiafaac_api.database.session import get_session
from gaiafaac_api.review_schemas import PendingReviewItem
from gaiafaac_api.services.review_queue import list_pending_reviews

router = APIRouter(prefix="/review", tags=["review queue"])
DatabaseSession = Annotated[Session, Depends(get_session)]


def require_admin(x_admin_key: Annotated[str | None, Header()] = None) -> None:
    """Gate operational endpoints behind a shared admin key.

    An unset key denies all access (secure by default); comparison is
    constant-time to avoid leaking the key by timing.
    """
    expected = get_settings().admin_key
    if not expected or not x_admin_key or not secrets.compare_digest(x_admin_key, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Administrator access required.",
            headers={"WWW-Authenticate": "AdminKey"},
        )


@router.get(
    "/pending",
    response_model=list[PendingReviewItem],
    summary="Real months awaiting human review (admin only, metadata only)",
    dependencies=[Depends(require_admin)],
)
def pending_reviews(session: DatabaseSession) -> list[PendingReviewItem]:
    return list_pending_reviews(session)
