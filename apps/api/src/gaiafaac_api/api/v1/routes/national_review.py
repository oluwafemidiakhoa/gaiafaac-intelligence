from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from gaiafaac_api.api.v1.routes.review import require_admin
from gaiafaac_api.database.session import get_session
from gaiafaac_api.pipeline.errors import ApprovalError
from gaiafaac_api.pipeline.national_distribution import (
    approve_national_distribution,
    publish_national_distribution,
)
from gaiafaac_api.services.national_review import (
    get_national_review_packet,
    list_active_national_actors,
    list_pending_national_reviews,
)

router = APIRouter(
    prefix="/review/national",
    tags=["national review queue"],
    dependencies=[Depends(require_admin)],
)
DatabaseSession = Annotated[Session, Depends(get_session)]


class NationalApprovalRequest(BaseModel):
    reviewer_id: uuid.UUID
    attestation: bool
    note: str | None = None


class NationalPublicationRequest(BaseModel):
    publisher_id: uuid.UUID
    attestation: bool


@router.get("/actors", summary="Active national reviewers and administrators")
def national_review_actors(session: DatabaseSession) -> list[dict[str, object]]:
    return list_active_national_actors(session)


@router.get("/pending", summary="National evidence awaiting human action")
def pending_national_reviews(session: DatabaseSession) -> list[dict[str, object]]:
    return list_pending_national_reviews(session)


@router.get("/{run_id}", summary="National evidence review packet")
def national_review_packet(
    run_id: uuid.UUID, session: DatabaseSession
) -> dict[str, object]:
    packet = get_national_review_packet(session, run_id)
    if packet is None:
        raise HTTPException(status_code=404, detail="National review packet not found.")
    return packet


@router.post("/{run_id}/approve", summary="Human-verify clean national evidence")
def approve_national_review(
    run_id: uuid.UUID,
    request: NationalApprovalRequest,
    session: DatabaseSession,
) -> dict[str, object]:
    if not request.attestation:
        raise HTTPException(status_code=422, detail="Reviewer attestation is required.")
    try:
        result = approve_national_distribution(
            session,
            run_id=run_id,
            reviewer_id=request.reviewer_id,
            note=request.note,
        )
    except ApprovalError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return {
        "run_id": result.run_id,
        "distribution_id": result.distribution_id,
        "status": "human_verified",
        "published": result.published,
    }


@router.post("/{run_id}/publish", summary="Publish approved national evidence under four-eyes control")
def publish_national_review(
    run_id: uuid.UUID,
    request: NationalPublicationRequest,
    session: DatabaseSession,
) -> dict[str, object]:
    if not request.attestation:
        raise HTTPException(status_code=422, detail="Publisher attestation is required.")
    try:
        result = publish_national_distribution(
            session,
            run_id=run_id,
            reviewer_id=request.publisher_id,
        )
    except ApprovalError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return {
        "run_id": result.run_id,
        "distribution_id": result.distribution_id,
        "status": "published",
        "published": result.published,
    }
