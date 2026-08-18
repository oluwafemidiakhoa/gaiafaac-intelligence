from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.models import OagfDiscoveryRecord, SourceDocument
from gaiafaac_api.database.oagf_revision_models import OagfRevisionCase
from gaiafaac_api.database.session import create_database_engine, create_session_factory
from gaiafaac_api.pipeline.oagf.discovery import OagfDiscoveryClient
from gaiafaac_api.pipeline.oagf.storage import ArchiveStorage, DatabaseArchiveStorage
from gaiafaac_api.pipeline.oagf.sync import SyncOptions, run_oagf_sync


@dataclass(frozen=True)
class RevisionMonitorSummary:
    discovered: int
    archived: int
    duplicates: int
    revisions_detected: int
    revision_cases_created: int
    inaccessible: int
    errors: list[dict[str, str]]


def _add_months(anchor: date, delta: int) -> date:
    index = anchor.year * 12 + (anchor.month - 1) + delta
    return date(index // 12, index % 12 + 1, 1)


def _create_missing_revision_cases(session: Session, *, detected_at: datetime) -> int:
    records = session.scalars(
        select(OagfDiscoveryRecord)
        .where(
            OagfDiscoveryRecord.category_slug == "faac-report",
            OagfDiscoveryRecord.previous_record_id.is_not(None),
            OagfDiscoveryRecord.sha256.is_not(None),
        )
        .order_by(OagfDiscoveryRecord.created_at)
    ).all()
    created = 0
    for record in records:
        if session.scalar(
            select(OagfRevisionCase.id).where(
                OagfRevisionCase.discovery_record_id == record.id
            )
        ):
            continue
        previous = session.get(OagfDiscoveryRecord, record.previous_record_id)
        if previous is None or previous.sha256 is None or previous.sha256 == record.sha256:
            continue
        if record.source_document_id is None:
            continue
        previous_source = (
            session.get(SourceDocument, previous.source_document_id)
            if previous.source_document_id
            else None
        )
        session.add(
            OagfRevisionCase(
                discovery_record_id=record.id,
                previous_record_id=previous.id,
                source_document_id=record.source_document_id,
                previous_source_document_id=previous.source_document_id,
                reporting_period_id=(
                    previous_source.reporting_period_id if previous_source is not None else None
                ),
                status="pending_review",
                detected_at=detected_at,
            )
        )
        created += 1
    session.commit()
    return created


def run_revision_monitor(
    session: Session,
    *,
    months_back: int | None = 24,
    now: datetime | None = None,
    client: OagfDiscoveryClient | None = None,
    storage: ArchiveStorage | None = None,
) -> RevisionMonitorSummary:
    """Detect official OAGF FAAC source changes without mutating published fiscal data."""
    timestamp = now or datetime.now(UTC)
    since = None
    if months_back is not None:
        if months_back < 1:
            raise ValueError("months_back must be positive or None")
        since = _add_months(timestamp.date().replace(day=1), -months_back)

    sync = run_oagf_sync(
        session,
        options=SyncOptions(category="faac-report", since=since, download_only=True),
        client=client,
        storage=storage or DatabaseArchiveStorage(session),
        now=timestamp,
    )
    cases_created = _create_missing_revision_cases(session, detected_at=timestamp)
    return RevisionMonitorSummary(
        discovered=sync.discovered,
        archived=sync.archived,
        duplicates=sync.duplicates,
        revisions_detected=sync.revisions,
        revision_cases_created=cases_created,
        inaccessible=sync.inaccessible,
        errors=sync.errors,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Detect and retain official OAGF FAAC source revisions; never publishes."
    )
    parser.add_argument(
        "--months-back",
        type=int,
        default=24,
        help="Rolling publication window. Use --full-history for the full FAAC inventory.",
    )
    parser.add_argument("--full-history", action="store_true")
    args = parser.parse_args()

    SessionLocal = create_session_factory(create_database_engine())
    with SessionLocal() as session:
        summary = run_revision_monitor(
            session,
            months_back=None if args.full_history else args.months_back,
        )
    print(json.dumps(asdict(summary), indent=2, sort_keys=True))
    if summary.errors:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
