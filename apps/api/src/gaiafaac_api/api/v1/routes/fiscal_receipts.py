from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, status

from gaiafaac_api.api.v1.routes.evidence_rooms import require_decision_rooms
from gaiafaac_api.customer_auth import CurrentCustomer, DatabaseSession
from gaiafaac_api.fiscal_receipt_schemas import (
    FiscalReceiptResponse,
    FiscalReceiptSummary,
    FiscalReceiptVerification,
)
from gaiafaac_api.services.fiscal_receipts import (
    generate_receipt,
    get_private_receipt,
    list_receipts,
    verify_receipt,
)

router = APIRouter(tags=["fiscal receipts"])


@router.post(
    "/decision-rooms/{room_id}/fiscal-receipts",
    response_model=FiscalReceiptResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_fiscal_receipt(
    room_id: uuid.UUID,
    session: DatabaseSession,
    user: CurrentCustomer,
) -> FiscalReceiptResponse:
    organization_id, _membership = require_decision_rooms(session, user)
    receipt = generate_receipt(session, organization_id, room_id, user)
    if receipt is None:
        raise HTTPException(status_code=404, detail="Decision Room not found.")
    return receipt


@router.get(
    "/decision-rooms/{room_id}/fiscal-receipts",
    response_model=list[FiscalReceiptSummary],
)
def decision_room_receipts(
    room_id: uuid.UUID,
    session: DatabaseSession,
    user: CurrentCustomer,
) -> list[FiscalReceiptSummary]:
    organization_id, _membership = require_decision_rooms(session, user)
    receipts = list_receipts(session, organization_id, room_id)
    if receipts is None:
        raise HTTPException(status_code=404, detail="Decision Room not found.")
    return receipts


@router.get("/fiscal-receipts/{receipt_id}", response_model=FiscalReceiptResponse)
def fiscal_receipt(
    receipt_id: uuid.UUID,
    session: DatabaseSession,
    user: CurrentCustomer,
) -> FiscalReceiptResponse:
    organization_id, _membership = require_decision_rooms(session, user)
    receipt = get_private_receipt(session, organization_id, receipt_id)
    if receipt is None:
        raise HTTPException(status_code=404, detail="Fiscal Receipt not found.")
    return receipt


@router.get(
    "/fiscal-receipts/{receipt_id}/verify",
    response_model=FiscalReceiptVerification,
)
def public_fiscal_receipt_verification(
    receipt_id: uuid.UUID,
    session: DatabaseSession,
) -> FiscalReceiptVerification:
    receipt = verify_receipt(session, receipt_id)
    if receipt is None:
        raise HTTPException(status_code=404, detail="Fiscal Receipt not found.")
    return receipt
