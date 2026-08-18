from __future__ import annotations

import uuid
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from gaiafaac_api.api.v1.routes.review import require_admin
from gaiafaac_api.database.session import get_session
from gaiafaac_api.oagf_revision_schemas import (
    OagfRevisionCaseItem,
    ResolveOagfRevisionRequest,
    ResolveOagfRevisionResponse,
)
from gaiafaac_api.pipeline.errors import ApprovalError
from gaiafaac_api.services.oagf_revisions import (
    get_oagf_revision_bytes,
    get_oagf_revision_case,
    list_oagf_revision_cases,
    resolve_oagf_revision_case,
)

router = APIRouter(prefix="/review/oagf-revisions", tags=["OAGF revision review"])
DatabaseSession = Annotated[Session, Depends(get_session)]


@router.get(
    "",
    response_model=list[OagfRevisionCaseItem],
    dependencies=[Depends(require_admin)],
)
def revision_cases(session: DatabaseSession) -> list[OagfRevisionCaseItem]:
    return list_oagf_revision_cases(session)


@router.get(
    "/{case_id}",
    response_model=OagfRevisionCaseItem,
    dependencies=[Depends(require_admin)],
)
def revision_case(case_id: uuid.UUID, session: DatabaseSession) -> OagfRevisionCaseItem:
    item = get_oagf_revision_case(session, case_id)
    if item is None:
        raise HTTPException(status_code=404, detail="OAGF revision case not found.")
    return item


@router.get(
    "/{case_id}/source/{version}",
    dependencies=[Depends(require_admin)],
)
def revision_source(
    case_id: uuid.UUID,
    version: Literal["current", "previous"],
    session: DatabaseSession,
) -> Response:
    archived = get_oagf_revision_bytes(session, case_id=case_id, version=version)
    if archived is None:
        raise HTTPException(
            status_code=404,
            detail="Retained source bytes are unavailable for this version.",
        )
    return Response(
        content=bytes(archived.content),
        media_type=archived.content_type,
        headers={"Content-Disposition": f'inline; filename="{archived.original_filename}"'},
    )


@router.post(
    "/{case_id}/resolve",
    response_model=ResolveOagfRevisionResponse,
    dependencies=[Depends(require_admin)],
)
def resolve_revision(
    case_id: uuid.UUID,
    request: ResolveOagfRevisionRequest,
    session: DatabaseSession,
) -> ResolveOagfRevisionResponse:
    if not request.attestation:
        raise HTTPException(status_code=422, detail="Revision-review attestation is required.")
    try:
        item = resolve_oagf_revision_case(
            session,
            case_id=case_id,
            reviewer_id=request.reviewer_id,
            resolution_code=request.resolution_code,
            note=request.note,
        )
    except ApprovalError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return ResolveOagfRevisionResponse(
        id=item.id,
        status=item.status,
        resolution_code=item.resolution_code or request.resolution_code,
    )
