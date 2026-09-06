from __future__ import annotations

import hashlib
import json
import uuid
from collections.abc import Iterable
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.commercial_models import OneTimePurchase
from gaiafaac_api.database.models import SourceDocument
from gaiafaac_api.project_receipt_schemas import ProjectReceiptVerification
from gaiafaac_api.services.document_branding import document_fingerprint
from gaiafaac_api.services.product_catalog import product_by_code

_ARTIFACT_HASH_KEY = "_artifact_sha256"
_FULFILLMENT_KEY = "_fulfillment"


def canonical_artifact_sha256(artifact: dict[str, Any]) -> str:
    payload = json.dumps(
        artifact,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _walk(value: Any) -> Iterable[Any]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def artifact_source_sha256s(artifact: dict[str, Any]) -> list[str]:
    hashes: set[str] = set()
    for node in _walk(artifact):
        if not isinstance(node, dict):
            continue
        for key in ("source_sha256", "sha256"):
            value = node.get(key)
            if isinstance(value, str) and len(value) == 64:
                try:
                    int(value, 16)
                except ValueError:
                    continue
                hashes.add(value.lower())
    return sorted(hashes)


def artifact_jurisdictions(artifact: dict[str, Any]) -> list[str]:
    request = artifact.get("request")
    if not isinstance(request, dict):
        return []
    values: list[str] = []
    single = request.get("state_slug") or request.get("state_code") or request.get("state")
    if single:
        values.append(str(single).replace("-", " ").title())
    many = request.get("state_slugs") or request.get("state_codes") or request.get("states")
    if isinstance(many, list):
        values.extend(str(item).replace("-", " ").title() for item in many if item)
    return list(dict.fromkeys(values))


def _revision_state(
    session: Session,
    source_hashes: list[str],
) -> tuple[str, list[str], list[str]]:
    if not source_hashes:
        return "source_registry_partial", [], []

    sources = list(
        session.scalars(select(SourceDocument).where(SourceDocument.sha256.in_(source_hashes)))
    )
    by_hash = {source.sha256.lower(): source for source in sources}
    unknown = [digest for digest in source_hashes if digest not in by_hash]
    known_ids = [source.id for source in sources]
    revised: set[str] = set()
    if known_ids:
        successors = list(
            session.scalars(
                select(SourceDocument).where(SourceDocument.supersedes_document_id.in_(known_ids))
            )
        )
        predecessor_hash_by_id = {source.id: source.sha256.lower() for source in sources}
        for successor in successors:
            predecessor_hash = predecessor_hash_by_id.get(successor.supersedes_document_id)
            if predecessor_hash:
                revised.add(predecessor_hash)

    if revised:
        return "review_recommended", sorted(revised), unknown
    if unknown:
        return "source_registry_partial", [], unknown
    return "no_known_revision", [], []


def verify_project_receipt(
    session: Session,
    purchase_id: uuid.UUID,
) -> ProjectReceiptVerification | None:
    purchase = session.scalar(
        select(OneTimePurchase).where(
            OneTimePurchase.id == purchase_id,
            OneTimePurchase.status == "success",
            OneTimePurchase.fulfillment_status == "ready",
        )
    )
    if purchase is None:
        return None

    metadata = dict(purchase.purchase_metadata or {})
    artifact = metadata.get(_FULFILLMENT_KEY)
    if not isinstance(artifact, dict):
        return None

    computed_hash = canonical_artifact_sha256(artifact)
    recorded_hash = metadata.get(_ARTIFACT_HASH_KEY)
    integrity_status = "verified" if recorded_hash == computed_hash else "integrity_failure"

    jurisdictions = artifact_jurisdictions(artifact)
    jurisdiction = ", ".join(jurisdictions) if jurisdictions else None
    document_id = document_fingerprint(
        sample=False,
        order_id=str(purchase.id),
        jurisdiction=jurisdiction,
        generated_at=artifact.get("captured_at"),
    )
    source_hashes = artifact_source_sha256s(artifact)
    if integrity_status == "integrity_failure":
        revision_status = "integrity_failure"
        revised: list[str] = []
        unknown: list[str] = []
    else:
        revision_status, revised, unknown = _revision_state(session, source_hashes)

    product = product_by_code(purchase.product_code)
    return ProjectReceiptVerification(
        purchase_id=purchase.id,
        document_id=document_id,
        artifact_sha256=computed_hash,
        product_code=purchase.product_code,
        product_label=product.label if product is not None else purchase.product_code.replace("_", " ").title(),
        artifact_schema=str(artifact.get("schema")) if artifact.get("schema") else None,
        evidence_captured_at=(
            str(artifact.get("captured_at")) if artifact.get("captured_at") else None
        ),
        issued_at=purchase.fulfilled_at or purchase.completed_at,
        jurisdictions=jurisdictions,
        source_sha256s=source_hashes,
        source_count=len(source_hashes),
        integrity_status=integrity_status,
        revision_status=revision_status,
        revised_source_sha256s=revised,
        unknown_source_sha256s=unknown,
        statement=(
            "This receipt verifies the frozen Gaia Fiscal Intelligence project artifact, "
            "its document fingerprint and the source fingerprints captured at fulfillment."
        ),
        limitations=[
            "Verification proves the recorded Gaia artifact boundary and integrity, not the truth of an external publisher.",
            "A later source revision does not rewrite the paid artifact; it indicates that a fresh review may be appropriate.",
            "This receipt is evidence support and is not a credit rating, legal opinion, investment recommendation or government certification.",
        ],
    )
