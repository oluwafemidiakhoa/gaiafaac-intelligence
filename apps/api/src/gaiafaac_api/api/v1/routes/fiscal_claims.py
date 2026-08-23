from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from gaiafaac_api.database.session import get_session
from gaiafaac_api.fiscal_claim_schemas import FiscalClaimEnvelope, FiscalClaimQuery
from gaiafaac_api.services.fiscal_claims import governed_claims

router = APIRouter(tags=["fiscal claims"])
DatabaseSession = Annotated[Session, Depends(get_session)]


@router.get(
    "/claims",
    response_model=FiscalClaimEnvelope,
    summary="Browse governed immutable fiscal claims",
)
def fiscal_claims(
    session: DatabaseSession,
    jurisdiction: Annotated[str | None, Query(min_length=2, max_length=16)] = None,
    fiscal_domain: Annotated[str | None, Query(min_length=2, max_length=40)] = None,
    fiscal_period: Annotated[str | None, Query(min_length=2, max_length=32)] = None,
    metric: Annotated[str | None, Query(min_length=2, max_length=120)] = None,
    include_superseded: Annotated[bool, Query()] = False,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
) -> FiscalClaimEnvelope:
    return governed_claims(
        session,
        FiscalClaimQuery(
            jurisdiction=jurisdiction,
            fiscal_domain=fiscal_domain,
            fiscal_period=fiscal_period,
            metric=metric,
            include_superseded=include_superseded,
            limit=limit,
        ),
    )


@router.get(
    "/jurisdictions/{code}/claims",
    response_model=FiscalClaimEnvelope,
    summary="Browse governed fiscal claims for one jurisdiction",
)
def jurisdiction_fiscal_claims(
    code: str,
    session: DatabaseSession,
    fiscal_domain: Annotated[str | None, Query(min_length=2, max_length=40)] = None,
    fiscal_period: Annotated[str | None, Query(min_length=2, max_length=32)] = None,
    metric: Annotated[str | None, Query(min_length=2, max_length=120)] = None,
    include_superseded: Annotated[bool, Query()] = False,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
) -> FiscalClaimEnvelope:
    return fiscal_claims(
        session=session,
        jurisdiction=code,
        fiscal_domain=fiscal_domain,
        fiscal_period=fiscal_period,
        metric=metric,
        include_superseded=include_superseded,
        limit=limit,
    )
