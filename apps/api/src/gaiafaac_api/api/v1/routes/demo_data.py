from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from gaiafaac_api.database.session import get_session
from gaiafaac_api.demo_schemas import (
    DemoComparisonResponse,
    DemoOverviewResponse,
    DemoSourcesResponse,
    DemoStateDetailResponse,
    DemoStatesResponse,
)
from gaiafaac_api.services.demo_data import (
    DEMO_SCOPE_NOTE,
    get_demo_overview,
    get_demo_sources,
    get_demo_state,
    get_demo_states,
    latest_demo_period,
)

router = APIRouter(tags=["demo data"])
DatabaseSession = Annotated[Session, Depends(get_session)]


def _period_or_404(session: Session):
    period = latest_demo_period(session)
    if period is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No labelled demo reporting period is available.",
        )
    return period


@router.get(
    "/overview/latest",
    response_model=DemoOverviewResponse,
    summary="Get the latest labelled demo overview",
)
def overview_latest(session: DatabaseSession) -> DemoOverviewResponse:
    period = _period_or_404(session)
    return get_demo_overview(session, period)


@router.get(
    "/states",
    response_model=DemoStatesResponse,
    summary="List states with labelled demo availability",
)
def states(session: DatabaseSession) -> DemoStatesResponse:
    period = _period_or_404(session)
    return get_demo_states(session, period)


@router.get(
    "/states/{slug}",
    response_model=DemoStateDetailResponse,
    summary="Get one state's labelled demo allocation",
)
def state_detail(slug: str, session: DatabaseSession) -> DemoStateDetailResponse:
    period = _period_or_404(session)
    result = get_demo_state(session, period, slug)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="State does not exist.")
    return result


@router.get(
    "/compare",
    response_model=DemoComparisonResponse,
    summary="Compare two to six states using labelled demo data",
)
def compare(
    session: DatabaseSession,
    states: Annotated[list[str], Query(min_length=2, max_length=6)],
) -> DemoComparisonResponse:
    if len(set(states)) != len(states):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Comparison states must be unique.",
        )
    period = _period_or_404(session)
    results = [get_demo_state(session, period, slug) for slug in states]
    if any(result is None for result in results):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or more comparison states do not exist.",
        )
    return DemoComparisonResponse(
        scope_note=DEMO_SCOPE_NOTE,
        period=results[0].period,
        states=[result for result in results if result is not None],
    )


@router.get(
    "/sources",
    response_model=DemoSourcesResponse,
    summary="List labelled demo source documents",
)
def sources(session: DatabaseSession) -> DemoSourcesResponse:
    return get_demo_sources(session)
