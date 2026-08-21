from datetime import date, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.enums import EvidenceStatus, FiscalEventSeverity
from gaiafaac_api.database.models import ApiKey, ReportingPeriod
from gaiafaac_api.database.session import get_session
from gaiafaac_api.entitlements import entitlements_for
from gaiafaac_api.fiscal_ledger_schemas import FiscalEventStreamEnvelope
from gaiafaac_api.published_analytics_schemas import TrendPoint
from gaiafaac_api.published_schemas import PublishedOverviewResponse
from gaiafaac_api.services.api_keys import (
    authenticate_api_key,
    record_request,
    requests_last_24h,
)
from gaiafaac_api.services.institutional_feed import institutional_event_feed
from gaiafaac_api.services.published_data import get_published_overview

router = APIRouter(prefix="/data", tags=["data api"])
DatabaseSession = Annotated[Session, Depends(get_session)]


def require_api_access(
    request: Request,
    session: DatabaseSession,
    x_api_key: Annotated[str | None, Header()] = None,
) -> ApiKey:
    """Authenticate an API key, enforce the plan's API entitlement + daily rate limit,
    and record the request. Free/public endpoints do not use this dependency."""
    key = authenticate_api_key(session, x_api_key or "")
    if key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A valid API key is required.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    plan = entitlements_for(key.plan_code)
    if not plan.api_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This plan does not include API access.",
        )
    if requests_last_24h(session, key) >= plan.api_rate_limit_per_day:
        record_request(session, key, request.url.path, status.HTTP_429_TOO_MANY_REQUESTS)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Daily API rate limit exceeded.",
        )
    record_request(session, key, request.url.path, status.HTTP_200_OK)
    return key


ApiAccess = Annotated[ApiKey, Depends(require_api_access)]


@router.get(
    "/months",
    response_model=list[TrendPoint],
    summary="All published months (API key required)",
)
def data_months(session: DatabaseSession, _key: ApiAccess) -> list[TrendPoint]:
    periods = session.scalars(
        select(ReportingPeriod)
        .where(
            ReportingPeriod.is_published.is_(True),
            ReportingPeriod.is_demo.is_(False),
        )
        .order_by(ReportingPeriod.revenue_month)
    ).all()
    points: list[TrendPoint] = []
    for period in periods:
        overview = get_published_overview(session, period)
        if overview is None:
            continue
        points.append(
            TrendPoint(
                revenue_month=period.revenue_month,
                reporting_label=period.reporting_label,
                total_net=overview.total_net or "0.00",
                covered_states=overview.covered_states,
            )
        )
    return points


@router.get(
    "/allocations",
    response_model=PublishedOverviewResponse,
    summary="Full allocations for a published month (API key required)",
)
def data_allocations(
    session: DatabaseSession, _key: ApiAccess, month: date
) -> PublishedOverviewResponse:
    period = session.scalar(
        select(ReportingPeriod).where(
            ReportingPeriod.revenue_month == month,
            ReportingPeriod.is_published.is_(True),
            ReportingPeriod.is_demo.is_(False),
        )
    )
    overview = get_published_overview(session, period) if period is not None else None
    if overview is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No published month for that date.",
        )
    return overview


@router.get(
    "/events",
    response_model=FiscalEventStreamEnvelope,
    summary="Entitled incremental Fiscal Event feed (API key required)",
)
def data_events(
    session: DatabaseSession,
    _key: ApiAccess,
    jurisdiction: Annotated[str | None, Query(min_length=2, max_length=16)] = None,
    event_type: Annotated[str | None, Query(min_length=2, max_length=80)] = None,
    severity: Annotated[FiscalEventSeverity | None, Query()] = None,
    evidence_status: Annotated[EvidenceStatus | None, Query()] = None,
    detected_after: Annotated[datetime | None, Query()] = None,
    date_from: Annotated[date | None, Query()] = None,
    date_to: Annotated[date | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 250,
) -> FiscalEventStreamEnvelope:
    if date_from and date_to and date_from > date_to:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="date_from cannot be after date_to.",
        )
    try:
        return institutional_event_feed(
            session,
            jurisdiction_code=jurisdiction,
            event_type=event_type,
            severity=severity,
            evidence_status=evidence_status,
            detected_after=detected_after,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
