from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException

from gaiafaac_api.customer_auth import DatabaseSession
from gaiafaac_api.project_receipt_schemas import ProjectReceiptVerification
from gaiafaac_api.services.project_receipts import verify_project_receipt

router = APIRouter(tags=["project receipt verification"])


@router.get(
    "/project-receipts/{purchase_id}/verify",
    response_model=ProjectReceiptVerification,
)
def public_project_receipt_verification(
    purchase_id: uuid.UUID,
    session: DatabaseSession,
) -> ProjectReceiptVerification:
    receipt = verify_project_receipt(session, purchase_id)
    if receipt is None:
        raise HTTPException(status_code=404, detail="Project Product receipt was not found.")
    return receipt
