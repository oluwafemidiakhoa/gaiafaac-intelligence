import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from gaiafaac_api.api.v1.routes.review import require_admin
from gaiafaac_api.database.session import get_session
from gaiafaac_api.nbs_igr_review_schemas import (
    IgrApproveRequest,
    IgrPublishRequest,
    IgrReviewActionResponse,
    IgrReviewPacket,
    PendingIgrReviewItem,
)
from gaiafaac_api.pipeline.errors import ApprovalError
from gaiafaac_api.pipeline.nbs_igr.approval import approve_igr_source, publish_igr_source
from gaiafaac_api.services.nbs_igr_review_queue import (
    get_igr_review_packet,
    list_pending_igr_reviews,
)

router = APIRouter(prefix="/nbs-igr-review", tags=["nbs igr review queue"])
DatabaseSession = Annotated[Session, Depends(get_session)]


@router.get(
    "/pending",
    response_model=list[PendingIgrReviewItem],
    summary="Real NBS IGR sources awaiting human action (admin only)",
    dependencies=[Depends(require_admin)],
)
def pending_igr_reviews(session: DatabaseSession) -> list[PendingIgrReviewItem]:
    return list_pending_igr_reviews(session)


@router.get(
    "/{source_document_id}",
    response_model=IgrReviewPacket,
    summary="Review packet for one archived NBS IGR source",
    dependencies=[Depends(require_admin)],
)
def igr_review_packet(source_document_id: uuid.UUID, session: DatabaseSession) -> IgrReviewPacket:
    packet = get_igr_review_packet(session, source_document_id)
    if packet is None:
        raise HTTPException(status_code=404, detail="NBS IGR review packet not found.")
    return packet


@router.post(
    "/{source_document_id}/approve",
    response_model=IgrReviewActionResponse,
    summary="Human-verify a complete NBS IGR source without publishing it",
    dependencies=[Depends(require_admin)],
)
def approve_igr_review(
    source_document_id: uuid.UUID,
    request: IgrApproveRequest,
    session: DatabaseSession,
) -> IgrReviewActionResponse:
    if not request.attestation:
        raise HTTPException(status_code=422, detail="Reviewer attestation is required.")
    try:
        result = approve_igr_source(
            session,
            source_document_id=source_document_id,
            reviewer_id=request.reviewer_id,
        )
    except ApprovalError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return IgrReviewActionResponse(
        source_document_id=result.source_document_id,
        fiscal_year=result.fiscal_year,
        records_affected=result.records_affected,
        published=result.published,
    )


@router.post(
    "/{source_document_id}/publish",
    response_model=IgrReviewActionResponse,
    summary="Publish approved NBS IGR evidence under four-eyes control",
    dependencies=[Depends(require_admin)],
)
def publish_igr_review(
    source_document_id: uuid.UUID,
    request: IgrPublishRequest,
    session: DatabaseSession,
) -> IgrReviewActionResponse:
    if not request.attestation:
        raise HTTPException(status_code=422, detail="Publisher attestation is required.")
    try:
        result = publish_igr_source(
            session,
            source_document_id=source_document_id,
            reviewer_id=request.publisher_id,
        )
    except ApprovalError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return IgrReviewActionResponse(
        source_document_id=result.source_document_id,
        fiscal_year=result.fiscal_year,
        records_affected=result.records_affected,
        published=result.published,
    )
