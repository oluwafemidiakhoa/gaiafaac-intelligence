import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from gaiafaac_api.api.v1.routes.review import require_admin
from gaiafaac_api.database.session import get_session
from gaiafaac_api.dmo_review_schemas import (
    DmoApproveRequest,
    DmoPublishRequest,
    DmoReviewActionResponse,
    DmoReviewPacket,
    PendingDmoReviewItem,
)
from gaiafaac_api.pipeline.dmo.approval import approve_debt_source, publish_debt_source
from gaiafaac_api.pipeline.errors import ApprovalError
from gaiafaac_api.services.dmo_review_queue import get_dmo_review_packet, list_pending_dmo_reviews

router = APIRouter(prefix="/dmo-review", tags=["dmo review queue"])
DatabaseSession = Annotated[Session, Depends(get_session)]


@router.get(
    "/pending",
    response_model=list[PendingDmoReviewItem],
    summary="Real DMO debt sources awaiting human action (admin only)",
    dependencies=[Depends(require_admin)],
)
def pending_dmo_reviews(session: DatabaseSession) -> list[PendingDmoReviewItem]:
    return list_pending_dmo_reviews(session)


@router.get(
    "/{source_document_id}",
    response_model=DmoReviewPacket,
    summary="Review packet for one archived DMO debt source",
    dependencies=[Depends(require_admin)],
)
def dmo_review_packet(source_document_id: uuid.UUID, session: DatabaseSession) -> DmoReviewPacket:
    packet = get_dmo_review_packet(session, source_document_id)
    if packet is None:
        raise HTTPException(status_code=404, detail="DMO review packet not found.")
    return packet


@router.post(
    "/{source_document_id}/approve",
    response_model=DmoReviewActionResponse,
    summary="Human-verify a complete DMO debt source without publishing it",
    dependencies=[Depends(require_admin)],
)
def approve_dmo_review(
    source_document_id: uuid.UUID,
    request: DmoApproveRequest,
    session: DatabaseSession,
) -> DmoReviewActionResponse:
    if not request.attestation:
        raise HTTPException(status_code=422, detail="Reviewer attestation is required.")
    try:
        result = approve_debt_source(
            session,
            source_document_id=source_document_id,
            reviewer_id=request.reviewer_id,
        )
    except ApprovalError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return DmoReviewActionResponse(
        source_document_id=result.source_document_id,
        debt_kind=result.debt_kind,
        as_of_date=result.as_of_date,
        records_affected=result.records_affected,
        published=result.published,
    )


@router.post(
    "/{source_document_id}/publish",
    response_model=DmoReviewActionResponse,
    summary="Publish approved DMO debt evidence under four-eyes control",
    dependencies=[Depends(require_admin)],
)
def publish_dmo_review(
    source_document_id: uuid.UUID,
    request: DmoPublishRequest,
    session: DatabaseSession,
) -> DmoReviewActionResponse:
    if not request.attestation:
        raise HTTPException(status_code=422, detail="Publisher attestation is required.")
    try:
        result = publish_debt_source(
            session,
            source_document_id=source_document_id,
            reviewer_id=request.publisher_id,
        )
    except ApprovalError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return DmoReviewActionResponse(
        source_document_id=result.source_document_id,
        debt_kind=result.debt_kind,
        as_of_date=result.as_of_date,
        records_affected=result.records_affected,
        published=result.published,
    )
