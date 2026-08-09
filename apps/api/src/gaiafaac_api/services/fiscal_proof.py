from __future__ import annotations

import hashlib
import json
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.enums import VerificationStatus
from gaiafaac_api.database.models import ReportingPeriod, SourceDocument, State, StateAllocation
from gaiafaac_api.fiscal_proof_schemas import (
    FiscalProofFinancials,
    FiscalProofResponse,
    FiscalProofSource,
    FiscalProofVerification,
)


def _money(value: Decimal | None) -> str | None:
    return format(value, ".2f") if value is not None else None


def _reconciliation(
    gross: Decimal | None,
    deductions: Decimal | None,
    net: Decimal | None,
) -> tuple[str, str | None]:
    if gross is None or deductions is None or net is None:
        return "not_applicable", None
    delta = gross - deductions - net
    status = "reconciled" if abs(delta) <= Decimal("0.01") else "mismatch"
    return status, _money(delta)


def get_fiscal_proof(
    session: Session,
    *,
    state_slug: str,
    revenue_month: date,
) -> FiscalProofResponse | None:
    row = session.execute(
        select(StateAllocation, State, ReportingPeriod, SourceDocument)
        .join(State, StateAllocation.state_id == State.id)
        .join(ReportingPeriod, StateAllocation.reporting_period_id == ReportingPeriod.id)
        .join(SourceDocument, StateAllocation.source_document_id == SourceDocument.id)
        .where(
            State.slug == state_slug,
            ReportingPeriod.revenue_month == revenue_month,
            ReportingPeriod.is_published.is_(True),
            ReportingPeriod.is_demo.is_(False),
            StateAllocation.is_published.is_(True),
            StateAllocation.is_demo.is_(False),
            SourceDocument.is_demo.is_(False),
        )
        .limit(1)
    ).first()
    if row is None:
        return None

    allocation, state, period, source = row
    reconciliation_status, reconciliation_delta = _reconciliation(
        allocation.gross_total,
        allocation.total_deductions,
        allocation.net_allocation,
    )

    canonical = {
        "proof_version": "1",
        "state_code": state.code,
        "state_slug": state.slug,
        "revenue_month": period.revenue_month.isoformat(),
        "reporting_label": period.reporting_label,
        "gross_total": _money(allocation.gross_total),
        "total_deductions": _money(allocation.total_deductions),
        "net_allocation": _money(allocation.net_allocation),
        "reported_unit": allocation.reported_unit.value,
        "source_sha256": source.sha256,
        "allocation_verification_status": allocation.verification_status.value,
        "period_verification_status": period.verification_status.value,
    }
    payload = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()
    digest = hashlib.sha256(payload).hexdigest()
    proof_id = f"GF1-NG-{state.code}-{period.revenue_month:%Y%m}-{digest[:12].upper()}"

    net = _money(allocation.net_allocation)
    claim = (
        f"{state.name} published net FAAC allocation for {period.revenue_month:%B %Y}: "
        f"NGN {net}."
        if net is not None
        else f"{state.name} has a published FAAC record for {period.revenue_month:%B %Y}; net allocation is unavailable."
    )

    return FiscalProofResponse(
        proof_id=proof_id,
        proof_digest_sha256=digest,
        claim=claim,
        state_name=state.name,
        state_slug=state.slug,
        state_code=state.code,
        geopolitical_zone=state.geopolitical_zone,
        revenue_month=period.revenue_month,
        reporting_label=period.reporting_label,
        financials=FiscalProofFinancials(
            gross_total=_money(allocation.gross_total),
            total_deductions=_money(allocation.total_deductions),
            net_allocation=net,
            reported_unit=allocation.reported_unit.value,
            reconciliation_status=reconciliation_status,
            reconciliation_delta=reconciliation_delta,
        ),
        source=FiscalProofSource(
            source_organization=source.source_organization,
            source_url=source.source_url,
            original_filename=source.original_filename,
            sha256=source.sha256,
            publication_date=source.publication_date,
            document_version=source.document_version,
        ),
        verification=FiscalProofVerification(
            allocation_status=allocation.verification_status.value,
            period_status=period.verification_status.value,
            source_status=source.source_status.value,
            reviewed_at=allocation.reviewed_at,
            published_at=allocation.published_at,
            human_verified=(
                allocation.verification_status is VerificationStatus.HUMAN_VERIFIED
                and period.verification_status is VerificationStatus.HUMAN_VERIFIED
            ),
        ),
        disclaimer=(
            "GaiaFAAC Fiscal Proof is a deterministic evidence record over a published allocation. "
            "The proof digest is content-derived for reproducibility; it is not a cryptographic "
            "signature by the source organization and does not make GaiaFAAC a government authority."
        ),
    )
