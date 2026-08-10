from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from gaiafaac_api.database.session import get_session
from gaiafaac_api.fiscal_proof_schemas import FiscalProofResponse
from gaiafaac_api.fiscal_pulse_schemas import FiscalPulseResponse
from gaiafaac_api.fiscal_watch_schemas import FiscalWatchResponse
from gaiafaac_api.gaia_analyst_schemas import GaiaAnalystResponse
from gaiafaac_api.published_analytics_schemas import PublishedAnalytics
from gaiafaac_api.published_schemas import PublishedOverviewResponse, PublishedSourceItem
from gaiafaac_api.services.fiscal_proof import get_fiscal_proof
from gaiafaac_api.services.fiscal_pulse import fiscal_pulse
from gaiafaac_api.services.fiscal_watch import fiscal_watch
from gaiafaac_api.services.gaia_analyst import gaia_analyst
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
    "/fiscal-watch",
    response_model=FiscalWatchResponse,
    summary="Deterministic monitoring signals over published FAAC data",
)
def fiscal_watch_endpoint(
    session: DatabaseSession,
    year: Annotated[int, Query(ge=2000, le=2100)] = 2026,
) -> FiscalWatchResponse:
    return fiscal_watch(session, year)


@router.get(
    "/gaia-analyst",
    response_model=GaiaAnalystResponse,
    summary="Evidence-grounded natural-language questions over published FAAC data",
)
def gaia_analyst_endpoint(
    session: DatabaseSession,
    question: Annotated[str, Query(min_length=3, max_length=500)],
    year: Annotated[int, Query(ge=2000, le=2100)] = 2026,
) -> GaiaAnalystResponse:
    return gaia_analyst(session, question=question, year=year)


@router.get(
    "/fiscal-proof/{state_slug}/{revenue_month}",
    response_model=FiscalProofResponse,
    summary="Deterministic evidence proof for a published state allocation",
)
def fiscal_proof_endpoint(
    state_slug: str,
    revenue_month: date,
    session: DatabaseSession,
) -> FiscalProofResponse:
    proof = get_fiscal_proof(session, state_slug=state_slug, revenue_month=revenue_month)
    if proof is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No published allocation proof exists for this state and revenue month.",
        )
    return proof


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
