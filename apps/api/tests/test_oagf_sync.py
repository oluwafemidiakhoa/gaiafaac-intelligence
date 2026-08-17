from __future__ import annotations

import json
from datetime import UTC, date, datetime

import pytest
from sqlalchemy import func, select

from gaiafaac_api.database.models import OagfDiscoveryRecord, OagfSyncRun, SourceDocument
from gaiafaac_api.pipeline.oagf.discovery import (
    DiscoveryError,
    DiscoveryInventory,
    FetchResponse,
    PublicationCandidate,
    PublicationCategory,
)
from gaiafaac_api.pipeline.oagf.storage import LocalArchiveStorage
from gaiafaac_api.pipeline.oagf.sync import SyncOptions, run_oagf_sync

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
    def __init__(self, body: bytes = b"%PDF source-v1", inaccessible: bool = False) -> None:
        self.body = body
        self.inaccessible = inaccessible
        self.document_fetches = 0

    def inventory(self, **kwargs) -> DiscoveryInventory:
        return DiscoveryInventory((CATEGORY,), (CANDIDATE,), 1, ())

    def fetch_document(self, url: str) -> FetchResponse:
        self.document_fetches += 1
        if self.inaccessible:
            raise DiscoveryError("HTTP 503")
        return FetchResponse(self.body, "application/pdf", url)


def _storage(tmp_path) -> LocalArchiveStorage:
    return LocalArchiveStorage(tmp_path / "archive", tmp_path / "manifest.jsonl")


def test_dry_run_does_not_download_write_or_create_database_rows(session, tmp_path) -> None:
    client = FakeClient()
    summary = run_oagf_sync(
        session,
        options=SyncOptions(dry_run=True),
        client=client,
        storage=_storage(tmp_path),
    )

    assert summary.discovered == 1
    assert client.document_fetches == 0
    assert not (tmp_path / "archive").exists()
    assert session.scalar(select(func.count()).select_from(OagfSyncRun)) == 0


def test_sync_archives_then_deduplicates_an_unchanged_url(session, tmp_path) -> None:
    client = FakeClient()
    storage = _storage(tmp_path)
    first = run_oagf_sync(session, options=SyncOptions(), client=client, storage=storage)
    second = run_oagf_sync(session, options=SyncOptions(), client=client, storage=storage)

    assert first.archived == 1
    assert second.archived == 0
    assert second.duplicates == 1
    assert session.scalar(select(func.count()).select_from(SourceDocument)) == 1
    assert session.scalar(select(func.count()).select_from(OagfDiscoveryRecord)) == 1
    events = [
        json.loads(line)["event"] for line in (tmp_path / "manifest.jsonl").read_text().splitlines()
    ]
    assert events == ["archived", "duplicate"]


def test_same_url_with_changed_bytes_creates_linked_revision(session, tmp_path) -> None:
    storage = _storage(tmp_path)
    run_oagf_sync(session, options=SyncOptions(), client=FakeClient(), storage=storage)
    summary = run_oagf_sync(
        session,
        options=SyncOptions(),
        client=FakeClient(b"%PDF source-v2"),
        storage=storage,
        now=datetime(2026, 8, 17, tzinfo=UTC),
    )

    records = session.scalars(
        select(OagfDiscoveryRecord).order_by(OagfDiscoveryRecord.version)
    ).all()
    sources = session.scalars(
        select(SourceDocument).order_by(SourceDocument.document_version)
    ).all()
    assert summary.revisions == 1
    assert [record.status for record in records] == ["superseded", "archived"]
    assert records[1].previous_record_id == records[0].id
    assert sources[1].supersedes_document_id == sources[0].id


def test_inaccessible_document_is_recorded_without_source_document(session, tmp_path) -> None:
    summary = run_oagf_sync(
        session,
        options=SyncOptions(),
        client=FakeClient(inaccessible=True),
        storage=_storage(tmp_path),
    )

    record = session.scalar(select(OagfDiscoveryRecord))
    assert summary.inaccessible == 1
    assert record.status == "inaccessible"
    assert record.sha256 is None
    assert session.scalar(select(func.count()).select_from(SourceDocument)) == 0
    run = session.scalar(select(OagfSyncRun))
    assert len(run.errors) == 1


def test_invalid_pdf_is_recorded_as_inaccessible(session, tmp_path) -> None:
    summary = run_oagf_sync(
        session,
        options=SyncOptions(),
        client=FakeClient(b"<html>upstream error</html>"),
        storage=_storage(tmp_path),
    )

    assert summary.inaccessible == 1
    assert "returned HTML" in summary.errors[0]["error"]


def test_full_sync_fails_safe_after_dramatic_discovery_drop(session, tmp_path) -> None:
    previous = OagfSyncRun(
        started_at=datetime(2026, 8, 15, tzinfo=UTC),
        completed_at=datetime(2026, 8, 15, tzinfo=UTC),
        status="completed",
        dry_run=False,
        hub_url="https://oagf.gov.ng/publications/",
        options={},
        categories_discovered=9,
        pages_checked=11,
        documents_discovered=113,
        errors=[],
    )
    session.add(previous)
    session.commit()

    with pytest.raises(DiscoveryError, match="Fail-safe stopped"):
        run_oagf_sync(
            session,
            options=SyncOptions(),
            client=FakeClient(),
            storage=_storage(tmp_path),
        )
