from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from gaiafaac_api.database.session import get_session
from gaiafaac_api.published_schemas import PublishedOverviewResponse
from gaiafaac_api.services.published_data import (
    get_published_overview,
    latest_published_period,
)

router = APIRouter(prefix="/published", tags=["published data"])
DatabaseSession = Annotated[Session, Depends(get_session)]


@router.get(
    "/overview/latest",
    response_model=PublishedOverviewResponse,
    summary="Latest published (real, human-approved) FAAC overview",
)
def published_overview_latest(session: DatabaseSession) -> PublishedOverviewResponse:
    period = latest_published_period(session)
    result = get_published_overview(session, period) if period is not None else None
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No published FAAC data is available yet.",
        )
    return result
