from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from gaiafaac_api.database.session import get_session
from gaiafaac_api.fiscal_pulse_schemas import FiscalPulseResponse
from gaiafaac_api.published_analytics_schemas import PublishedAnalytics
from gaiafaac_api.published_schemas import PublishedOverviewResponse, PublishedSourceItem
from gaiafaac_api.services.fiscal_pulse import fiscal_pulse
from gaiafaac_api.services.published_analytics import published_analytics
from gaiafaac_api.services.published_data import (
    get_published_overview,
    latest_published_period,
    published_sources,
)

router = APIRouter(prefix="/published", tags=["published data"])
DatabaseSession = Annotated[Session, Depends(get_session)]


@router.get(
    "/analytics",
    response_model=PublishedAnalytics,
    summary="Analytics over published, human-verified FAAC data",
)
def published_analytics_endpoint(session: DatabaseSession) -> PublishedAnalytics:
    return published_analytics(session)


@router.get(
    "/fiscal-pulse",
    response_model=FiscalPulseResponse,
    summary="Derived fiscal signals over published, human-verified FAAC data",
)
def fiscal_pulse_endpoint(
    session: DatabaseSession,
    year: Annotated[int, Query(ge=2000, le=2100)] = 2024,
) -> FiscalPulseResponse:
    return fiscal_pulse(session, year)


@router.get(
    "/sources",
    response_model=list[PublishedSourceItem],
    summary="Source document for every published month",
)
def published_sources_endpoint(session: DatabaseSession) -> list[PublishedSourceItem]:
    return published_sources(session)


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
