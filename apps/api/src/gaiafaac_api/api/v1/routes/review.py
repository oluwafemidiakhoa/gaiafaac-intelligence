from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from gaiafaac_api.database.session import get_session
from gaiafaac_api.review_schemas import PendingReviewItem
from gaiafaac_api.services.review_queue import list_pending_reviews

router = APIRouter(prefix="/review", tags=["review queue"])
DatabaseSession = Annotated[Session, Depends(get_session)]


@router.get(
    "/pending",
    response_model=list[PendingReviewItem],
    summary="Real months awaiting human review (metadata only, no figures)",
)
def pending_reviews(session: DatabaseSession) -> list[PendingReviewItem]:
    return list_pending_reviews(session)
