from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from gaiafaac_api.database.session import get_session
from gaiafaac_api.national_distribution_schemas import PublishedNationalDistribution
from gaiafaac_api.services.national_distribution import latest_published_national_distribution

router = APIRouter(prefix="/published/national-distribution", tags=["published data"])
DatabaseSession = Annotated[Session, Depends(get_session)]


@router.get(
    "/latest",
    response_model=PublishedNationalDistribution,
    summary="Latest published national FAAC distribution with reconciliation evidence",
)
def latest_national_distribution_endpoint(
    session: DatabaseSession,
) -> PublishedNationalDistribution:
    result = latest_published_national_distribution(session)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No published, human-verified national FAAC distribution is available yet.",
        )
    return result
