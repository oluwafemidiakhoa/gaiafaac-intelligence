from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, aliased

from gaiafaac_api.database.enums import EvidenceStatus, SourceStatus
from gaiafaac_api.database.ledger_models import FiscalClaim
from gaiafaac_api.database.models import ReportingPeriod, SourceDocument, State
from gaiafaac_api.services.decision_packet import decision_packet
from gaiafaac_api.services.fiscal_intelligence import compare_jurisdictions
from gaiafaac_api.services.published_data import get_published_overview
from gaiafaac_api.services.published_igr import published_igr


class OneTimeFulfillmentUnavailable(ValueError):
    """Raised before charging when the requested governed evidence is unavailable."""


def _year(value: object) -> int:
    if value in (None, ""):
        raise OneTimeFulfillmentUnavailable("A year is required for this product.")
    try:
        year = int(value)
    except (TypeError, ValueError) as error:
        raise OneTimeFulfillmentUnavailable("Year must be a four-digit number.") from error
    if year < 2000 or year > 2100:
        raise OneTimeFulfillmentUnavailable("Year must be between 2000 and 2100.")
    return year


def _state(session: Session, value: object) -> State:
    raw = str(value or "").strip()
    if not raw:
        raise OneTimeFulfillmentUnavailable("A jurisdiction is required for this product.")
    state = session.scalar(
        select(State).where((State.slug == raw.lower()) | (State.code == raw.upper()))
    )
    if state is None:
        raise OneTimeFulfillmentUnavailable("The requested jurisdiction is not recognized by Gaia.")
    return state


def normalize_one_time_context(
    session: Session,
    *,
    product_code: str,
    context: dict[str, Any],
) -> dict[str, Any]:
    """Normalize the minimum inputs required for a deterministic deliverable."""

    if product_code in {"decision_pack", "due_diligence_snapshot"}:
        state_value = context.get("state_slug") or context.get("state_code") or context.get("state")
        year_value = context.get("year")
        if year_value in (None, "") and context.get("period"):
            year_value = str(context["period"])[:4]
        state = _state(session, state_value)
        return {"state_slug": state.slug, "state_code": state.code, "year": _year(year_value)}

    if product_code == "multi_state_comparison_pack":
        raw_states = context.get("state_slugs") or context.get("state_codes") or context.get("states")
        if isinstance(raw_states, str):
            raw_states = [part.strip() for part in raw_states.split(",") if part.strip()]
        if not isinstance(raw_states, list):
            raise OneTimeFulfillmentUnavailable(
                "Provide between two and six jurisdictions for a comparison pack."
            )
        states: list[State] = []
        for item in raw_states:
            state = _state(session, item)
            if all(existing.id != state.id for existing in states):
                states.append(state)
        if len(states) < 2 or len(states) > 6:
            raise OneTimeFulfillmentUnavailable(
                "Provide between two and six distinct jurisdictions for a comparison pack."
            )
        return {
            "state_slugs": [state.slug for state in states],
            "state_codes": [state.code for state in states],
            "year": _year(context.get("year")),
        }

    if product_code == "historical_evidence_export":
        state_value = context.get("state_slug") or context.get("state_code") or context.get("state")
        state = _state(session, state_value)
        domain = str(context.get("domain") or "igr").strip().lower()
        if domain not in {"igr", "faac"}:
            raise OneTimeFulfillmentUnavailable(
                "Historical exports currently support the IGR or FAAC governed evidence lane."
            )
        start_year = _year(context.get("start_year"))
        end_year = _year(context.get("end_year"))
        if end_year < start_year:
            raise OneTimeFulfillmentUnavailable("End year cannot be earlier than start year.")
        if end_year - start_year > 10:
            raise OneTimeFulfillmentUnavailable(
                "A single historical export can cover at most eleven calendar years."
            )
        return {
            "state_slug": state.slug,
            "state_code": state.code,
            "domain": domain,
            "start_year": start_year,
            "end_year": end_year,
        }

    raise OneTimeFulfillmentUnavailable("Unsupported one-time product.")


def _historical_igr_rows(session: Session, context: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for year in range(context["start_year"], context["end_year"] + 1):
        result = published_igr(session, year=year, state_slug=context["state_slug"])
        for record in result.records:
            rows.append(
                {
                    "domain": "igr",
                    "state_name": record.state_name,
                    "state_code": record.state_code,
                    "state_slug": record.state_slug,
                    "period": (
                        f"{record.fiscal_year}Q{record.quarter}"
                        if record.quarter is not None
                        else str(record.fiscal_year)
                    ),
                    "value": record.igr_amount,
                    "unit": record.reported_unit,
                    "source_organization": record.source.organization,
                    "source_url": record.source.source_url,
                    "source_sha256": record.source.sha256,
                    "verification_status": record.verification_status,
                }
            )
    return rows


def _historical_faac_rows(session: Session, context: dict[str, Any]) -> list[dict[str, Any]]:
    start = date(context["start_year"], 1, 1)
    end = date(context["end_year"] + 1, 1, 1)
    periods = session.scalars(
        select(ReportingPeriod)
        .where(
            ReportingPeriod.revenue_month >= start,
            ReportingPeriod.revenue_month < end,
        )
        .order_by(ReportingPeriod.revenue_month)
    ).all()
    rows: list[dict[str, Any]] = []
    for period in periods:
        overview = get_published_overview(session, period)
        if overview is None:
            continue
        allocation = next(
            (item for item in overview.allocations if item.state_slug == context["state_slug"]),
            None,
        )
        if allocation is None:
            continue
        rows.append(
            {
                "domain": "faac",
                "state_name": allocation.state_name,
                "state_code": allocation.state_code,
                "state_slug": allocation.state_slug,
                "period": overview.period.revenue_month.isoformat(),
                "value": allocation.net_allocation,
                "gross_total": allocation.gross_total,
                "total_deductions": allocation.total_deductions,
                "unit": allocation.reported_unit,
                "source_organization": overview.source.source_organization,
                "source_url": overview.source.source_url,
                "source_sha256": overview.source.sha256,
                "verification_status": "human_verified",
            }
        )
    return rows


def _current_verified_debt_claims(
    session: Session,
    *,
    state_slug: str,
    year: int,
) -> list[dict[str, Any]]:
    successor = aliased(FiscalClaim)
    successor_source = aliased(SourceDocument)
    eligible_successor = (
        select(successor.gaia_id)
        .join(successor_source, successor.source_document_id == successor_source.id)
        .where(
            successor.supersedes_gaia_id == FiscalClaim.gaia_id,
            successor.object_type == "debt",
            successor.metric == FiscalClaim.metric,
            successor.evidence_status == EvidenceStatus.VERIFIED,
            successor_source.source_status == SourceStatus.APPROVED,
            successor_source.is_demo.is_(False),
        )
        .correlate(FiscalClaim)
        .exists()
    )
    rows = session.execute(
        select(FiscalClaim, SourceDocument)
        .join(State, FiscalClaim.state_id == State.id)
        .join(SourceDocument, FiscalClaim.source_document_id == SourceDocument.id)
        .where(
            State.slug == state_slug,
            FiscalClaim.object_type == "debt",
            FiscalClaim.fiscal_period.like(f"{year}%"),
            FiscalClaim.evidence_status == EvidenceStatus.VERIFIED,
            SourceDocument.source_status == SourceStatus.APPROVED,
            SourceDocument.is_demo.is_(False),
            ~eligible_successor,
        )
        .order_by(FiscalClaim.fiscal_period, FiscalClaim.metric)
    ).all()
    return [
        {
            "gaia_id": claim.gaia_id,
            "fiscal_period": claim.fiscal_period,
            "metric": claim.metric,
            "value": claim.value_text,
            "unit": claim.unit,
            "currency": claim.currency,
            "source_organization": source.source_organization,
            "source_url": source.source_url,
            "source_sha256": claim.source_sha256,
            "evidence_status": claim.evidence_status.value,
        }
        for claim, source in rows
    ]


def build_one_time_fulfillment(
    session: Session,
    *,
    product_code: str,
    context: dict[str, Any],
) -> dict[str, Any]:
    """Build the governed deliverable that will be frozen to the paid order."""

    captured_at = datetime.now(UTC).isoformat()

    if product_code == "decision_pack":
        packet = decision_packet(
            session,
            state_slug=context["state_slug"],
            year=context["year"],
        )
        if packet is None or (not packet.months and not packet.igr_records):
            raise OneTimeFulfillmentUnavailable(
                "No governed evidence is available for the requested Decision Pack."
            )
        return {
            "schema": "gaia-one-time-decision-pack-v1",
            "captured_at": captured_at,
            "request": context,
            "decision_packet": packet.model_dump(mode="json"),
        }

    if product_code == "multi_state_comparison_pack":
        comparison = compare_jurisdictions(
            session,
            jurisdiction_codes=context["state_codes"],
            as_of=date(context["year"], 12, 31),
        )
        if not comparison.data.jurisdictions:
            raise OneTimeFulfillmentUnavailable(
                "No governed evidence is available for the requested comparison."
            )
        return {
            "schema": "gaia-one-time-multi-state-comparison-v1",
            "captured_at": captured_at,
            "request": context,
            "comparison": comparison.model_dump(mode="json"),
        }

    if product_code == "historical_evidence_export":
        rows = (
            _historical_igr_rows(session, context)
            if context["domain"] == "igr"
            else _historical_faac_rows(session, context)
        )
        if not rows:
            raise OneTimeFulfillmentUnavailable(
                "No governed evidence is available for the requested historical export."
            )
        return {
            "schema": "gaia-one-time-historical-export-v1",
            "captured_at": captured_at,
            "request": context,
            "rows": rows,
        }

    if product_code == "due_diligence_snapshot":
        packet = decision_packet(
            session,
            state_slug=context["state_slug"],
            year=context["year"],
        )
        debt_claims = _current_verified_debt_claims(
            session,
            state_slug=context["state_slug"],
            year=context["year"],
        )
        if (packet is None or (not packet.months and not packet.igr_records)) and not debt_claims:
            raise OneTimeFulfillmentUnavailable(
                "No governed evidence is available for the requested due-diligence snapshot."
            )
        return {
            "schema": "gaia-one-time-due-diligence-snapshot-v1",
            "captured_at": captured_at,
            "request": context,
            "decision_packet": packet.model_dump(mode="json") if packet is not None else None,
            "debt_claims": debt_claims,
            "statement": (
                "This snapshot preserves the governed evidence available to Gaia at the "
                "recorded capture time. It is evidence support, not legal, credit or investment advice."
            ),
        }

    raise OneTimeFulfillmentUnavailable("Unsupported one-time product.")
