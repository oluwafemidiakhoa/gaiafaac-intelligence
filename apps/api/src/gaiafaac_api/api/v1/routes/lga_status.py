from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from gaiafaac_api.database.session import get_session
from gaiafaac_api.lga_schemas import LgaPublicationStatus
from gaiafaac_api.services.lga_public_status import lga_publication_status

router = APIRouter(prefix="/published/local-governments", tags=["published data"])
DatabaseSession = Annotated[Session, Depends(get_session)]


@router.get(
    "/status/{state_code}",
    response_model=LgaPublicationStatus,
    summary="Governed OAGF Table IV publication status for a jurisdiction",
)
def lga_publication_status_endpoint(
    state_code: str,
    session: DatabaseSession,
) -> LgaPublicationStatus:
    result = lga_publication_status(session, state_code=state_code)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unknown jurisdiction code.",
        )
    return result
