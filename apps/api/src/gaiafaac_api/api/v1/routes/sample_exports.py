from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from gaiafaac_api.database.session import get_session
from gaiafaac_api.services.branded_one_time_exports import (
    build_one_time_excel,
    build_one_time_pdf,
)
from gaiafaac_api.services.decision_packet import decision_packet
from gaiafaac_api.services.document_branding import SAMPLE_NOTICE

router = APIRouter(prefix="/published/samples", tags=["published samples"])
DatabaseSession = Annotated[Session, Depends(get_session)]
_SAMPLE_PRICE_NAIRA = "50000"


def _sample_artifact(session: Session, *, state_slug: str, year: int) -> tuple[dict, str]:
    packet = decision_packet(session, state_slug=state_slug, year=year)
    if packet is None or (not packet.months and not packet.igr_records):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No governed evidence is available for this Decision Pack sample.",
        )

    jurisdiction = state_slug.replace("-", " ").title()
    artifact = {
        "schema": "gaia-sample-decision-pack-v1",
        "captured_at": datetime.now(UTC).isoformat(),
        "request": {
            "state_slug": state_slug,
            "year": year,
            "sample": True,
        },
        "decision_packet": packet.model_dump(mode="json"),
        "statement": SAMPLE_NOTICE,
    }
    return artifact, jurisdiction


def _response(filename: str, media_type: str, body: bytes) -> Response:
    return Response(
        content=body,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "public, max-age=300",
            "X-Gaia-Document-Class": "sample",
        },
    )


@router.get("/decision-pack/{state_slug}.pdf")
def sample_decision_pack_pdf(
    state_slug: str,
    session: DatabaseSession,
    year: Annotated[int, Query(ge=2000, le=2100)] = 2026,
) -> Response:
    artifact, jurisdiction = _sample_artifact(session, state_slug=state_slug, year=year)
    filename, media_type, body = build_one_time_pdf(
        purchase_id=f"SAMPLE-{state_slug}-{year}",
        product_code="decision_pack",
        amount_naira=_SAMPLE_PRICE_NAIRA,
        currency="NGN",
        completed_at="Not applicable — demonstration sample",
        artifact=artifact,
        sample=True,
        jurisdiction=jurisdiction,
    )
    return _response(filename, media_type, body)


@router.get("/decision-pack/{state_slug}.xlsx")
def sample_decision_pack_excel(
    state_slug: str,
    session: DatabaseSession,
    year: Annotated[int, Query(ge=2000, le=2100)] = 2026,
) -> Response:
    artifact, jurisdiction = _sample_artifact(session, state_slug=state_slug, year=year)
    filename, media_type, body = build_one_time_excel(
        purchase_id=f"SAMPLE-{state_slug}-{year}",
        product_code="decision_pack",
        amount_naira=_SAMPLE_PRICE_NAIRA,
        currency="NGN",
        completed_at="Not applicable — demonstration sample",
        artifact=artifact,
        sample=True,
        jurisdiction=jurisdiction,
    )
    return _response(filename, media_type, body)
