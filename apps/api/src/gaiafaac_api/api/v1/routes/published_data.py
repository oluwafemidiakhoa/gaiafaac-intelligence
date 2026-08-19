from datetime import date
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from gaiafaac_api.database.session import get_session
from gaiafaac_api.decision_packet_schemas import DecisionPacketResponse
from gaiafaac_api.fiscal_design_schemas import FiscalDesignResponse
from gaiafaac_api.fiscal_proof_schemas import FiscalProofResponse
from gaiafaac_api.fiscal_pulse_schemas import FiscalPulseResponse
from gaiafaac_api.fiscal_watch_schemas import FiscalWatchResponse
from gaiafaac_api.gaia_analyst_schemas import GaiaAnalystResponse
from gaiafaac_api.igr_schemas import PublishedIgrRecord, PublishedIgrResponse
from gaiafaac_api.lga_schemas import PublishedLgaDetailResponse, PublishedLgaStateResponse
from gaiafaac_api.published_analytics_schemas import PublishedAnalytics
from gaiafaac_api.published_schemas import PublishedOverviewResponse, PublishedSourceItem
from gaiafaac_api.services.decision_packet import decision_packet
from gaiafaac_api.services.fiscal_design import fiscal_design
from gaiafaac_api.services.fiscal_proof import get_fiscal_proof
from gaiafaac_api.services.fiscal_pulse import fiscal_pulse
from gaiafaac_api.services.fiscal_watch import fiscal_watch
from gaiafaac_api.services.gaia_analyst_igr import gaia_analyst
from gaiafaac_api.services.published_analytics import published_analytics
from gaiafaac_api.services.published_data import (
    get_published_overview,
    latest_published_period,
    published_sources,
)
from gaiafaac_api.services.published_igr import latest_published_igr, published_igr
from gaiafaac_api.services.published_lga import published_lga_history, published_lgas_for_state

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
    "/fiscal-design/{state_slug}",
    response_model=FiscalDesignResponse,
    summary="Hypothetical fiscal-resilience scenarios over governed FAAC and IGR evidence",
)
def fiscal_design_endpoint(
    state_slug: str,
    session: DatabaseSession,
    year: Annotated[int, Query(ge=2000, le=2100)] = 2026,
    faac_shock_pct: Annotated[Decimal, Query(ge=-100, le=100)] = Decimal("-20"),
    igr_shock_pct: Annotated[Decimal, Query(ge=-100, le=100)] = Decimal("0"),
    reserve_share_pct: Annotated[Decimal, Query(ge=0, le=100)] = Decimal("10"),
    debt_change_pct: Annotated[Decimal, Query(ge=-100, le=100)] = Decimal("0"),
    debt_service_change_pct: Annotated[Decimal, Query(ge=-100, le=100)] = Decimal("0"),
    expenditure_change_pct: Annotated[Decimal, Query(ge=-100, le=100)] = Decimal("0"),
    capital_spending_change_pct: Annotated[Decimal, Query(ge=-100, le=100)] = Decimal("0"),
    inflation_assumption_pct: Annotated[Decimal, Query(ge=-99, le=100)] = Decimal("0"),
) -> FiscalDesignResponse:
    result = fiscal_design(
        session,
        state_slug=state_slug,
        year=year,
        faac_shock_pct=faac_shock_pct,
        igr_shock_pct=igr_shock_pct,
        reserve_share_pct=reserve_share_pct,
        debt_change_pct=debt_change_pct,
        debt_service_change_pct=debt_service_change_pct,
        expenditure_change_pct=expenditure_change_pct,
        capital_spending_change_pct=capital_spending_change_pct,
        inflation_assumption_pct=inflation_assumption_pct,
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No published fiscal evidence exists for this state and year.",
        )
    return result


@router.get(
    "/gaia-analyst",
    response_model=GaiaAnalystResponse,
    summary="Evidence-grounded natural-language questions over published FAAC and IGR data",
)
def gaia_analyst_endpoint(
    session: DatabaseSession,
    question: Annotated[str, Query(min_length=3, max_length=500)],
    year: Annotated[int, Query(ge=2000, le=2100)] = 2026,
) -> GaiaAnalystResponse:
    return gaia_analyst(session, question=question, year=year)


@router.get(
    "/igr/latest",
    response_model=PublishedIgrRecord,
    summary="Latest published, human-verified IGR evidence for a state",
)
def latest_published_igr_endpoint(
    session: DatabaseSession,
    state_slug: Annotated[str, Query(min_length=2, max_length=100)],
) -> PublishedIgrRecord:
    record = latest_published_igr(session, state_slug=state_slug)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No published IGR evidence exists for this state.",
        )
    return record


@router.get(
    "/igr",
    response_model=PublishedIgrResponse,
    summary="Published, human-verified state internally generated revenue evidence",
)
def published_igr_endpoint(
    session: DatabaseSession,
    year: Annotated[int, Query(ge=2000, le=2100)],
    state_slug: Annotated[str | None, Query(min_length=2, max_length=100)] = None,
) -> PublishedIgrResponse:
    return published_igr(session, year=year, state_slug=state_slug)


@router.get(
    "/local-governments/{state_code}",
    response_model=PublishedLgaStateResponse,
    summary="Latest published OAGF Table IV evidence for every LGA in a state",
)
def published_lgas_for_state_endpoint(
    state_code: str,
    session: DatabaseSession,
) -> PublishedLgaStateResponse:
    result = published_lgas_for_state(session, state_code=state_code)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No published local-government evidence exists for this jurisdiction.",
        )
    return result


@router.get(
    "/local-governments/{state_code}/{local_government_slug}",
    response_model=PublishedLgaDetailResponse,
    summary="Published OAGF Table IV allocation history for one local government",
)
def published_lga_history_endpoint(
    state_code: str,
    local_government_slug: str,
    session: DatabaseSession,
) -> PublishedLgaDetailResponse:
    result = published_lga_history(
        session,
        state_code=state_code,
        local_government_slug=local_government_slug,
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No published evidence exists for this local government.",
        )
    return result


@router.get(
    "/decision-packet/{state_slug}",
    response_model=DecisionPacketResponse,
    summary="Print-ready evidence dossier for a state and year",
)
def decision_packet_endpoint(
    state_slug: str,
    session: DatabaseSession,
    year: Annotated[int, Query(ge=2000, le=2100)] = 2026,
) -> DecisionPacketResponse:
    packet = decision_packet(session, state_slug=state_slug, year=year)
    if packet is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No published Decision Packet exists for this state and year.",
        )
    return packet


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
