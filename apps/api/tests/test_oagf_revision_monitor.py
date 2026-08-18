from __future__ import annotations

from datetime import UTC, date, datetime

from sqlalchemy import func, select

from gaiafaac_api.database.models import OagfDiscoveryRecord, ReportingPeriod, SourceDocument
from gaiafaac_api.database.oagf_revision_models import OagfArchiveObject, OagfRevisionCase
from gaiafaac_api.pipeline.oagf.discovery import (
    DiscoveryInventory,
    FetchResponse,
    PublicationCandidate,
    PublicationCategory,
)
from gaiafaac_api.pipeline.oagf.revision_monitor import run_revision_monitor
from gaiafaac_api.pipeline.oagf.storage import DatabaseArchiveStorage

CATEGORY = PublicationCategory(
    name="FAAC Report",
    slug="faac-report",
    url="https://oagf.gov.ng/publications/faac-report/",
)
CANDIDATE = PublicationCandidate(
    category_name=CATEGORY.name,
    category_slug=CATEGORY.slug,
    title="Disbursement June, 2026",
    publication_page_url="https://oagf.gov.ng/oagf_publications/disbursement-june-2026/",
    document_url="https://oagf.gov.ng/wp-content/uploads/2026/08/Disbursement-June-2026.pdf",
    discovery_url="https://oagf.gov.ng/publications/faac-report/",
    source_publication_date=date(2026, 6, 1),
    displayed_year="2026",
    displayed_month="June",
    original_filename="Disbursement-June-2026.pdf",
)


class FakeClient:
    def __init__(self, body: bytes) -> None:
        self.body = body

    def inventory(self, **kwargs) -> DiscoveryInventory:
        return DiscoveryInventory((CATEGORY,), (CANDIDATE,), 1, ())

    def fetch_document(self, url: str) -> FetchResponse:
        return FetchResponse(self.body, "application/pdf", url)


def test_database_archive_is_content_addressed_and_durable(session) -> None:
    storage = DatabaseArchiveStorage(session)
    first = storage.archive(
        content=b"%PDF retained",
        category_slug="faac-report",
        document_slug="June 2026",
        source_date=date(2026, 6, 1),
        original_filename="june.pdf",
    )
    second = storage.archive(
        content=b"%PDF retained",
        category_slug="faac-report",
        document_slug="renamed",
        source_date=date(2026, 6, 1),
        original_filename="renamed.pdf",
    )
    session.commit()

    assert first.created is True
    assert second.created is False
    assert first.storage_path == second.storage_path
    assert session.scalar(select(func.count()).select_from(OagfArchiveObject)) == 1
    archived = session.scalar(select(OagfArchiveObject))
    assert bytes(archived.content) == b"%PDF retained"


def test_changed_official_faac_bytes_create_revision_case_without_mutating_period(session) -> None:
    timestamp = datetime(2026, 8, 18, tzinfo=UTC)
    first = run_revision_monitor(
        session,
        months_back=24,
        now=timestamp,
        client=FakeClient(b"%PDF source-v1"),
    )
    assert first.revisions_detected == 0
    assert first.revision_cases_created == 0

    original_record = session.scalar(select(OagfDiscoveryRecord))
    original_source = session.get(SourceDocument, original_record.source_document_id)
    period = ReportingPeriod(
        revenue_month=date(2026, 6, 1),
        disbursement_month=date(2026, 6, 1),
        allocation_period_month=date(2026, 5, 1),
        reporting_label="OAGF FAAC Disbursement - June 2026",
        is_demo=False,
        is_published=True,
    )
    session.add(period)
    session.flush()
    original_source.reporting_period_id = period.id
    session.commit()

    second = run_revision_monitor(
        session,
        months_back=24,
        now=datetime(2026, 8, 19, tzinfo=UTC),
        client=FakeClient(b"%PDF source-v2"),
    )

    assert second.revisions_detected == 1
    assert second.revision_cases_created == 1
    case = session.scalar(select(OagfRevisionCase))
    assert case.status == "pending_review"
    assert case.reporting_period_id == period.id
    assert case.previous_source_document_id == original_source.id
    assert session.get(ReportingPeriod, period.id).is_published is True
    assert session.scalar(select(func.count()).select_from(OagfArchiveObject)) == 2


def test_unchanged_rescan_is_idempotent(session) -> None:
    run_revision_monitor(session, client=FakeClient(b"%PDF same"))
    second = run_revision_monitor(session, client=FakeClient(b"%PDF same"))

    assert second.revisions_detected == 0
    assert second.revision_cases_created == 0
    assert session.scalar(select(func.count()).select_from(OagfRevisionCase)) == 0
    assert session.scalar(select(func.count()).select_from(OagfArchiveObject)) == 1
