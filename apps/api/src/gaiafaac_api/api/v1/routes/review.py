import secrets
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from gaiafaac_api.config import get_settings
from gaiafaac_api.database.session import get_session
from gaiafaac_api.pipeline.approval import approve_import, publish_import, reject_import
from gaiafaac_api.pipeline.errors import ApprovalError
from gaiafaac_api.review_schemas import (
    ApproveReviewRequest,
    PendingReviewItem,
    PublishReviewRequest,
    RejectReviewRequest,
    ReviewActionResponse,
    ReviewPacket,
)
from gaiafaac_api.services.review_queue import (
    get_review_packet,
    list_active_review_actors,
    list_pending_reviews,
)

router = APIRouter(prefix="/review", tags=["review queue"])
DatabaseSession = Annotated[Session, Depends(get_session)]


def require_admin(x_admin_key: Annotated[str | None, Header()] = None) -> None:
    """Gate operational endpoints behind a shared admin key.

    An unset key denies all access (secure by default); comparison is
    constant-time to avoid leaking the key by timing.
    """
    expected = get_settings().admin_key
    if not expected or not x_admin_key or not secrets.compare_digest(x_admin_key, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Administrator access required.",
            headers={"WWW-Authenticate": "AdminKey"},
        )


@router.get(
    "/actors",
    summary="Active OAGF reviewers and administrators",
    dependencies=[Depends(require_admin)],
)
def review_actors(session: DatabaseSession) -> list[dict[str, object]]:
    return list_active_review_actors(session)


@router.get(
    "/pending",
    response_model=list[PendingReviewItem],
    summary="Real months awaiting human action (admin only, metadata only)",
    dependencies=[Depends(require_admin)],
)
def pending_reviews(session: DatabaseSession) -> list[PendingReviewItem]:
    return list_pending_reviews(session)


@router.get(
    "/{run_id}",
    response_model=ReviewPacket,
    summary="Accountant review packet for one unpublished import",
    dependencies=[Depends(require_admin)],
)
def review_packet(run_id: uuid.UUID, session: DatabaseSession) -> ReviewPacket:
    packet = get_review_packet(session, run_id)
    if packet is None:
        raise HTTPException(status_code=404, detail="Review packet not found.")
    return packet


@router.post(
    "/{run_id}/approve",
    response_model=ReviewActionResponse,
    summary="Human-verify a clean import without publishing it",
    dependencies=[Depends(require_admin)],
)
def approve_review(
    run_id: uuid.UUID,
    request: ApproveReviewRequest,
    session: DatabaseSession,
) -> ReviewActionResponse:
    if not request.attestation:
        raise HTTPException(
            status_code=422,
            detail="Reviewer attestation is required before approval.",
        )
    try:
        result = approve_import(
            session,
            run_id=run_id,
            reviewer_id=request.reviewer_id,
            note=request.note,
        )
    except ApprovalError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return ReviewActionResponse(
        run_id=result.run_id,
        status="human_verified",
        allocations_affected=result.allocations_approved,
        published=result.published,
    )


@router.post(
    "/{run_id}/reject",
    response_model=ReviewActionResponse,
    summary="Reject an import while preserving its evidence and audit trail",
    dependencies=[Depends(require_admin)],
)
def reject_review(
    run_id: uuid.UUID,
    request: RejectReviewRequest,
    session: DatabaseSession,
) -> ReviewActionResponse:
    try:
        result = reject_import(
            session,
            run_id=run_id,
            reviewer_id=request.reviewer_id,
            reason=request.reason,
        )
    except ApprovalError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return ReviewActionResponse(
        run_id=result.run_id,
        status="rejected",
        allocations_affected=result.allocations_approved,
        published=result.published,
    )


@router.post(
    "/{run_id}/publish",
    response_model=ReviewActionResponse,
    summary="Publish approved OAGF evidence under four-eyes control",
    dependencies=[Depends(require_admin)],
)
def publish_review(
    run_id: uuid.UUID,
    request: PublishReviewRequest,
    session: DatabaseSession,
) -> ReviewActionResponse:
    if not request.attestation:
        raise HTTPException(status_code=422, detail="Publisher attestation is required.")
    try:
        result = publish_import(
            session,
            run_id=run_id,
            reviewer_id=request.publisher_id,
        )
    except ApprovalError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return ReviewActionResponse(
        run_id=result.run_id,
        status="published",
        allocations_affected=result.allocations_approved,
        published=result.published,
    )
