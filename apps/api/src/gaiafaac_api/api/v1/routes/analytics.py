from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from gaiafaac_api.analytics_schemas import (
    DependencyResponse,
    ForecastsResponse,
    RankingsResponse,
    VolatilityResponse,
)
from gaiafaac_api.database.session import get_session
from gaiafaac_api.services.analytics import (
    get_dependency,
    get_forecasts,
    get_rankings,
    get_volatility,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])
DatabaseSession = Annotated[Session, Depends(get_session)]

_NOT_FOUND = "No labelled demo analytics are available. Run compute-analytics first."


@router.get("/rankings", response_model=RankingsResponse, summary="Demo net-allocation rankings")
def rankings(session: DatabaseSession) -> RankingsResponse:
    result = get_rankings(session)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_NOT_FOUND)
    return result


@router.get("/volatility", response_model=VolatilityResponse, summary="Demo volatility")
def volatility(session: DatabaseSession) -> VolatilityResponse:
    result = get_volatility(session)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_NOT_FOUND)
    return result


@router.get("/dependency", response_model=DependencyResponse, summary="Demo revenue dependency")
def dependency(session: DatabaseSession) -> DependencyResponse:
    result = get_dependency(session)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_NOT_FOUND)
    return result


@router.get("/forecasts", response_model=ForecastsResponse, summary="Demo forecasts (estimates)")
def forecasts(session: DatabaseSession) -> ForecastsResponse:
    result = get_forecasts(session)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_NOT_FOUND)
    return result
