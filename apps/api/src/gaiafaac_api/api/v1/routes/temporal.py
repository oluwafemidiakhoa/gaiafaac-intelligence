from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from gaiafaac_api.database.session import get_session
from gaiafaac_api.services.temporal_intelligence import temporal_fiscal_snapshot
from gaiafaac_api.temporal_schemas import TemporalFiscalSnapshotEnvelope

router = APIRouter(tags=["temporal fiscal intelligence"])
DatabaseSession = Annotated[Session, Depends(get_session)]


@router.get(
    "/jurisdictions/{code}/temporal-snapshot",
    response_model=TemporalFiscalSnapshotEnvelope,
    summary="Bitemporal fiscal claim snapshot for a jurisdiction",
)
def jurisdiction_temporal_snapshot(
    code: str,
    session: DatabaseSession,
    effective_as_of: Annotated[datetime, Query()],
    known_as_of: Annotated[datetime, Query()],
) -> TemporalFiscalSnapshotEnvelope:
    try:
        snapshot = temporal_fiscal_snapshot(
            session,
            jurisdiction_code=code,
            effective_as_of=effective_as_of,
            known_as_of=known_as_of,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Jurisdiction not found.")
    return snapshot
