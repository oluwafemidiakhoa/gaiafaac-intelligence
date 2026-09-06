from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Response
from sqlalchemy import select

from gaiafaac_api.customer_auth import CurrentCustomer, DatabaseSession
from gaiafaac_api.database.commercial_models import OneTimePurchase
from gaiafaac_api.services.account import membership_for
from gaiafaac_api.services.branded_one_time_exports import (
    build_one_time_excel,
    build_one_time_pdf,
)

router = APIRouter(prefix="/billing/one-time", tags=["customer billing"])
_FULFILLMENT_KEY = "_fulfillment"


def _paid_artifact(
    purchase_id: uuid.UUID,
    session: DatabaseSession,
    user: CurrentCustomer,
) -> tuple[OneTimePurchase, dict]:
    if user.organization_id is None or membership_for(session, user) is None:
        raise HTTPException(status_code=409, detail="Customer organization is not configured.")

    purchase = session.scalar(
        select(OneTimePurchase).where(
            OneTimePurchase.id == purchase_id,
            OneTimePurchase.organization_id == user.organization_id,
        )
    )
    if purchase is None:
        raise HTTPException(status_code=404, detail="One-time purchase was not found.")
    if purchase.status != "success":
        raise HTTPException(
            status_code=409,
            detail="Payment has not been confirmed for this order.",
        )
    if purchase.fulfillment_status != "ready":
        raise HTTPException(
            status_code=409,
            detail="The paid deliverable is not ready yet.",
        )

    metadata = dict(purchase.purchase_metadata or {})
    artifact = metadata.get(_FULFILLMENT_KEY)
    if not isinstance(artifact, dict):
        raise HTTPException(status_code=409, detail="The paid deliverable is not available yet.")
    return purchase, artifact


def _jurisdiction_label(artifact: dict) -> str | None:
    request = artifact.get("request")
    if not isinstance(request, dict):
        return None
    state = request.get("state_slug") or request.get("state_code")
    if state:
        return str(state).replace("-", " ").title()
    states = request.get("state_slugs") or request.get("state_codes")
    if isinstance(states, list) and states:
        return ", ".join(str(value).replace("-", " ").title() for value in states)
    return None


def _download_response(filename: str, media_type: str, body: bytes) -> Response:
    return Response(
        content=body,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "private, no-store",
        },
    )


@router.get("/purchases/{purchase_id}/download.xlsx")
def download_one_time_excel(
    purchase_id: uuid.UUID,
    session: DatabaseSession,
    user: CurrentCustomer,
) -> Response:
    purchase, artifact = _paid_artifact(purchase_id, session, user)
    filename, media_type, body = build_one_time_excel(
        purchase_id=str(purchase.id),
        product_code=purchase.product_code,
        amount_naira=str(purchase.amount_naira),
        currency=purchase.currency,
        completed_at=purchase.completed_at,
        artifact=artifact,
        jurisdiction=_jurisdiction_label(artifact),
    )
    return _download_response(filename, media_type, body)


@router.get("/purchases/{purchase_id}/download.pdf")
def download_one_time_pdf(
    purchase_id: uuid.UUID,
    session: DatabaseSession,
    user: CurrentCustomer,
) -> Response:
    purchase, artifact = _paid_artifact(purchase_id, session, user)
    filename, media_type, body = build_one_time_pdf(
        purchase_id=str(purchase.id),
        product_code=purchase.product_code,
        amount_naira=str(purchase.amount_naira),
        currency=purchase.currency,
        completed_at=purchase.completed_at,
        artifact=artifact,
        jurisdiction=_jurisdiction_label(artifact),
    )
    return _download_response(filename, media_type, body)
