from __future__ import annotations

from datetime import UTC, date, datetime, time

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.enums import EvidenceStatus, FiscalEventSeverity
from gaiafaac_api.database.ledger_models import FiscalEvent
from gaiafaac_api.database.models import State
from gaiafaac_api.fiscal_ledger_schemas import (
    FiscalEventData,
    FiscalEventStreamEnvelope,
    FiscalEventStreamEvidence,
    JurisdictionIdentity,
    LedgerMeta,
)
from gaiafaac_api.services.fiscal_institutional import (
    INSTITUTIONAL_METHODOLOGY_VERSION,
    INSTITUTIONAL_SCHEMA_VERSION,
)


def _stored_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def institutional_event_feed(
    session: Session,
    *,
    jurisdiction_code: str | None = None,
    event_type: str | None = None,
    severity: FiscalEventSeverity | None = None,
    evidence_status: EvidenceStatus | None = None,
    detected_after: datetime | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    limit: int = 100,
) -> FiscalEventStreamEnvelope:
    """Return an entitled incremental view over the immutable Fiscal Event ledger."""

    query = select(FiscalEvent, State).join(State, FiscalEvent.state_id == State.id)
    if jurisdiction_code:
        query = query.where(State.code == jurisdiction_code.strip().upper().removeprefix("NG-"))
    if event_type:
        query = query.where(FiscalEvent.event_type == event_type.strip().lower())
    if severity:
        query = query.where(FiscalEvent.severity == severity)
    if evidence_status:
        query = query.where(FiscalEvent.evidence_status == evidence_status)
    if detected_after is not None:
        if detected_after.tzinfo is None or detected_after.utcoffset() is None:
            raise ValueError("detected_after must include a timezone.")
        query = query.where(FiscalEvent.detected_at > detected_after.astimezone(UTC))
    if date_from:
        query = query.where(
            FiscalEvent.detected_at >= datetime.combine(date_from, time.min, tzinfo=UTC)
        )
    if date_to:
        query = query.where(
            FiscalEvent.detected_at <= datetime.combine(date_to, time.max, tzinfo=UTC)
        )

    rows = session.execute(
        query.order_by(FiscalEvent.detected_at, FiscalEvent.event_id).limit(limit)
    ).all()
    data = [
        FiscalEventData(
            event_id=event.event_id,
            jurisdiction=JurisdictionIdentity(
                code=f"NG-{state.code.upper()}",
                name=state.name,
            ),
            event_type=event.event_type,
            severity=event.severity,
            effective_at=_stored_utc(event.effective_at),
            detected_at=_stored_utc(event.detected_at),
            evidence_status=event.evidence_status,
            evidence_ids=list(event.evidence_ids),
            calculation=dict(event.calculation),
            explanation=event.explanation,
            fiscal_state_id=event.fiscal_state_id,
            methodology_version=event.methodology_version,
        )
        for event, state in rows
    ]
    return FiscalEventStreamEnvelope(
        data=data,
        evidence=FiscalEventStreamEvidence(
            record_count=len(data),
            meaning=(
                "This entitled feed is a machine-readable projection of Gaia's immutable "
                "Fiscal Event ledger. It does not create new fiscal facts or infer cause."
            ),
        ),
        meta=LedgerMeta(
            schema_version=INSTITUTIONAL_SCHEMA_VERSION,
            methodology_version=INSTITUTIONAL_METHODOLOGY_VERSION,
        ),
    )
