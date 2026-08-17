from __future__ import annotations

import mimetypes
import urllib.parse
import uuid
from collections import Counter
from collections.abc import Iterator
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from dataclasses import asdict, dataclass, field
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path, PurePosixPath

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.enums import ProcessingStatus, SourceStatus
from gaiafaac_api.database.models import OagfDiscoveryRecord, OagfSyncRun, SourceDocument
from gaiafaac_api.pipeline.oagf.discovery import (
    HUB_URL,
    DiscoveryError,
    DownloadedDocument,
    FetchResponse,
    OagfDiscoveryClient,
    PublicationCandidate,
)
from gaiafaac_api.pipeline.oagf.storage import ArchiveStorage, LocalArchiveStorage

OAGF_ORGANIZATION = "Office of the Accountant-General of the Federation (OAGF)"
FAIL_SAFE_MINIMUM_BASELINE = 10
FAIL_SAFE_RATIO = Decimal("0.5")


@dataclass(frozen=True)
class SyncOptions:
    dry_run: bool = False
    category: str | None = None
    since: date | None = None
    download_only: bool = False
    extract: bool = False
    limit: int | None = None


@dataclass
class SyncSummary:
    categories: list[dict[str, str]] = field(default_factory=list)
    pages_checked: int = 0
    discovered: int = 0
    archived: int = 0
    duplicates: int = 0
    revisions: int = 0
    inaccessible: int = 0
    errors: list[dict[str, str]] = field(default_factory=list)
    publications: list[dict[str, object]] = field(default_factory=list)
    category_counts: dict[str, int] = field(default_factory=dict)
    earliest_source_publication_date: date | None = None
    latest_source_publication_date: date | None = None
    candidate_faac_publications: list[str] = field(default_factory=list)
    candidate_funds_release_documents: list[str] = field(default_factory=list)


def classify(category_slug: str) -> tuple[str, Decimal, str]:
    rules = {
        "faac-report": "faac_report",
        "treasury-circulars": "treasury_circular",
        "oagf-annual-reports": "oagf_annual_report",
        "ipsas-reports": "ipsas_report",
        "agfs-speech": "agf_speech",
        "funds-releases-to-mdas": "funds_release",
        "gifmis-reports": "gifmis_report",
        "ippis-reports": "ippis_report",
        "oagf-journals": "oagf_journal",
    }
    return rules.get(category_slug, "oagf_publication"), Decimal("1.0000"), "hub_category_v1"


def _candidate_payload(candidate: PublicationCandidate) -> dict[str, object]:
    classification, confidence, method = classify(candidate.category_slug)
    return {
        "source_organization": OAGF_ORGANIZATION,
        "category": candidate.category_name,
        "category_slug": candidate.category_slug,
        "title": candidate.title,
        "publication_identity": _publication_identity(candidate),
        "publication_page_url": candidate.publication_page_url,
        "document_url": candidate.document_url,
        "discovery_url": candidate.discovery_url,
        "source_publication_date": candidate.source_publication_date,
        "displayed_year": candidate.displayed_year,
        "displayed_month": candidate.displayed_month,
        "original_filename": candidate.original_filename,
        "classification": classification,
        "classification_confidence": str(confidence),
        "classification_method": method,
        "extraction_status": "not_requested",
    }


def _publication_identity(candidate: PublicationCandidate) -> str:
    return candidate.publication_page_url or (
        f"{candidate.category_slug}:{candidate.title}:{candidate.document_url}"
    )


def _validate_document(candidate: PublicationCandidate, body: bytes, content_type: str) -> None:
    if not body:
        raise DiscoveryError(f"Empty document response: {candidate.document_url}")
    media_type = content_type.partition(";")[0].lower()
    if media_type in {"text/html", "application/xhtml+xml"} or body.lstrip().startswith(b"<"):
        raise DiscoveryError(f"Document URL returned HTML: {candidate.document_url}")
    suffix = PurePosixPath(urllib.parse.urlparse(candidate.document_url).path).suffix.lower()
    if suffix == ".pdf" and not body.startswith(b"%PDF"):
        raise DiscoveryError(f"PDF signature is missing: {candidate.document_url}")


def _validate_downloaded_document(
    candidate: PublicationCandidate, download: DownloadedDocument
) -> None:
    if download.byte_length == 0:
        raise DiscoveryError(f"Empty document response: {candidate.document_url}")
    with download.temporary_path.open("rb") as source:
        signature = source.read(5)
    media_type = download.content_type.partition(";")[0].lower()
    if media_type in {"text/html", "application/xhtml+xml"} or signature.lstrip().startswith(b"<"):
        raise DiscoveryError(f"Document URL returned HTML: {candidate.document_url}")
    suffix = PurePosixPath(urllib.parse.urlparse(candidate.document_url).path).suffix.lower()
    if suffix == ".pdf" and signature != b"%PDF-":
        raise DiscoveryError(f"PDF signature is missing: {candidate.document_url}")


def _download_candidate(
    client: OagfDiscoveryClient, candidate: PublicationCandidate
) -> tuple[FetchResponse | DownloadedDocument | None, DiscoveryError | None]:
    response: FetchResponse | DownloadedDocument | None = None
    try:
        downloader = getattr(client, "download_document", None)
        if callable(downloader):
            response = downloader(candidate.document_url)
            _validate_downloaded_document(candidate, response)
        else:
            response = client.fetch_document(candidate.document_url)
            _validate_document(candidate, response.body, response.content_type)
    except DiscoveryError as error:
        if isinstance(response, DownloadedDocument):
            response.cleanup()
        return None, error
    return response, None


def _prefetched_documents(
    client: OagfDiscoveryClient,
    candidates: tuple[PublicationCandidate, ...],
    *,
    workers: int = 3,
) -> Iterator[
    tuple[
        PublicationCandidate,
        FetchResponse | DownloadedDocument | None,
        DiscoveryError | None,
    ]
]:
    """Download with a bounded window while yielding results in discovery order."""
    iterator = iter(candidates)
    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="oagf-download") as executor:
        pending: dict[
            Future[tuple[FetchResponse | DownloadedDocument | None, DiscoveryError | None]],
            PublicationCandidate,
        ] = {}
        for _ in range(workers):
            candidate = next(iterator, None)
            if candidate is None:
                break
            pending[executor.submit(_download_candidate, client, candidate)] = candidate
        while pending:
            completed, _ = wait(pending, return_when=FIRST_COMPLETED)
            for future in completed:
                candidate = pending.pop(future)
                response, error = future.result()
                yield candidate, response, error
                next_candidate = next(iterator, None)
                if next_candidate is not None:
                    pending[executor.submit(_download_candidate, client, next_candidate)] = (
                        next_candidate
                    )


def _latest_for_candidate(
    session: Session, candidate: PublicationCandidate
) -> OagfDiscoveryRecord | None:
    return session.scalar(
        select(OagfDiscoveryRecord)
        .where(OagfDiscoveryRecord.publication_identity == _publication_identity(candidate))
        .order_by(OagfDiscoveryRecord.version.desc())
        .limit(1)
    )


def _source_document(
    session: Session,
    *,
    candidate: PublicationCandidate,
    storage_path: str,
    checksum: str,
    content_type: str,
    retrieved_at: datetime,
    version: int,
    supersedes_id: uuid.UUID | None,
) -> tuple[SourceDocument, bool]:
    existing = session.scalar(select(SourceDocument).where(SourceDocument.sha256 == checksum))
    if existing is not None:
        return existing, True
    document = SourceDocument(
        source_organization=OAGF_ORGANIZATION,
        source_url=candidate.document_url,
        original_filename=candidate.original_filename,
        storage_path=str(Path(storage_path).resolve()),
        sha256=checksum,
        mime_type=content_type
        or mimetypes.guess_type(candidate.original_filename)[0]
        or "application/octet-stream",
        publication_date=candidate.source_publication_date,
        downloaded_at=retrieved_at,
        processing_status=ProcessingStatus.REGISTERED,
        source_status=SourceStatus.REGISTERED,
        document_version=str(version),
        supersedes_document_id=supersedes_id,
        is_demo=False,
    )
    session.add(document)
    session.flush()
    return document, False


def _manifest_payload(
    *,
    candidate: PublicationCandidate,
    record: OagfDiscoveryRecord,
    event: str,
    run_id: uuid.UUID,
) -> dict[str, object]:
    return {
        "schema_version": "oagf-source-manifest/v1",
        "event": event,
        "sync_run_id": str(run_id),
        "discovery_record_id": str(record.id),
        **_candidate_payload(candidate),
        "retrieved_at": record.retrieved_at,
        "content_type": record.content_type,
        "byte_length": record.byte_length,
        "sha256": record.sha256,
        "storage_path": record.storage_path,
        "downloaded_filename": record.downloaded_filename,
        "version": record.version,
        "previous_record_id": str(record.previous_record_id) if record.previous_record_id else None,
        "source_document_id": str(record.source_document_id) if record.source_document_id else None,
        "status": record.status,
    }


def _record_inaccessible(
    session: Session,
    run: OagfSyncRun,
    candidate: PublicationCandidate,
    now: datetime,
) -> OagfDiscoveryRecord:
    latest = _latest_for_candidate(session, candidate)
    if latest is not None and latest.sha256 is None:
        latest.last_seen_run_id = run.id
        latest.last_seen_at = now
        latest.status = "inaccessible"
        latest.title = candidate.title
        latest.document_url = candidate.document_url
        latest.discovery_url = candidate.discovery_url
        latest.source_publication_date = candidate.source_publication_date
        latest.displayed_year = candidate.displayed_year
        latest.displayed_month = candidate.displayed_month
        latest.original_filename = candidate.original_filename
        return latest
    classification, confidence, method = classify(candidate.category_slug)
    record = OagfDiscoveryRecord(
        first_seen_run_id=run.id,
        last_seen_run_id=run.id,
        previous_record_id=latest.id if latest else None,
        source_organization=OAGF_ORGANIZATION,
        category_name=candidate.category_name,
        category_slug=candidate.category_slug,
        title=candidate.title,
        publication_identity=_publication_identity(candidate),
        publication_page_url=candidate.publication_page_url,
        document_url=candidate.document_url,
        discovery_url=candidate.discovery_url,
        source_publication_date=candidate.source_publication_date,
        displayed_year=candidate.displayed_year,
        displayed_month=candidate.displayed_month,
        first_discovered_at=now,
        last_seen_at=now,
        original_filename=candidate.original_filename,
        version=(latest.version + 1) if latest else 1,
        status="inaccessible",
        classification=classification,
        classification_confidence=confidence,
        classification_method=method,
        extraction_status="not_requested",
    )
    session.add(record)
    session.flush()
    return record


def _checkpoint_run(run: OagfSyncRun, summary: SyncSummary) -> None:
    run.documents_archived = summary.archived
    run.duplicates_found = summary.duplicates
    run.revisions_found = summary.revisions
    run.inaccessible_documents = summary.inaccessible
    run.errors = list(summary.errors)


def run_oagf_sync(
    session: Session | None,
    *,
    options: SyncOptions,
    client: OagfDiscoveryClient | None = None,
    storage: ArchiveStorage | None = None,
    now: datetime | None = None,
) -> SyncSummary:
    """Discover and optionally archive OAGF sources. Never extracts or publishes fiscal data."""
    if options.extract:
        raise ValueError("--extract is intentionally unavailable in source-discovery PR1")
    if options.limit is not None and options.limit < 1:
        raise ValueError("--limit must be greater than zero")
    if options.dry_run is False and session is None:
        raise ValueError("A database session is required unless --dry-run is used")

    timestamp = now or datetime.now(UTC)
    discovery_client = client or OagfDiscoveryClient()
    archive = storage or LocalArchiveStorage()
    discovery = discovery_client.inventory(
        category_slug=options.category,
        since=options.since,
        limit=options.limit,
    )
    source_dates = [
        item.source_publication_date
        for item in discovery.publications
        if item.source_publication_date is not None
    ]
    faac_publications = [
        item.title for item in discovery.publications if item.category_slug == "faac-report"
    ]
    summary = SyncSummary(
        categories=[asdict(item) for item in discovery.categories],
        pages_checked=discovery.pages_checked,
        discovered=len(discovery.publications),
        errors=list(discovery.errors),
        publications=[_candidate_payload(item) for item in discovery.publications],
        category_counts=dict(Counter(item.category_slug for item in discovery.publications)),
        earliest_source_publication_date=min(source_dates) if source_dates else None,
        latest_source_publication_date=max(source_dates) if source_dates else None,
        candidate_faac_publications=faac_publications,
        candidate_funds_release_documents=[
            item.title
            for item in discovery.publications
            if item.category_slug == "funds-releases-to-mdas"
        ],
    )
    if discovery.errors and not options.dry_run:
        raise DiscoveryError(
            f"Fail-safe stopped OAGF sync after {len(discovery.errors)} listing-page error(s)"
        )
    is_full_inventory = options.category is None and options.since is None and options.limit is None
    baseline = 0
    if is_full_inventory and isinstance(archive, LocalArchiveStorage):
        baseline = archive.manifest_document_count()
    if is_full_inventory and session is not None:
        previous = session.scalar(
            select(OagfSyncRun)
            .where(OagfSyncRun.status.in_(["completed", "completed_with_errors"]))
            .order_by(OagfSyncRun.completed_at.desc())
            .limit(1)
        )
        if previous is not None:
            baseline = max(baseline, previous.documents_discovered)
    if (
        baseline >= FAIL_SAFE_MINIMUM_BASELINE
        and Decimal(summary.discovered) < Decimal(baseline) * FAIL_SAFE_RATIO
    ):
        raise DiscoveryError(
            "Fail-safe stopped OAGF sync: "
            f"discovered {summary.discovered} documents versus prior baseline {baseline}"
        )
    if options.dry_run:
        return summary

    assert session is not None
    run = OagfSyncRun(
        started_at=timestamp,
        status="running",
        dry_run=False,
        hub_url=HUB_URL,
        options={
            "category": options.category,
            "since": options.since.isoformat() if options.since else None,
            "download_only": options.download_only,
            "extract": False,
            "limit": options.limit,
        },
        categories_discovered=len(discovery.categories),
        pages_checked=discovery.pages_checked,
        documents_discovered=len(discovery.publications),
        errors=list(summary.errors),
    )
    session.add(run)
    session.commit()

    for candidate, response, download_error in _prefetched_documents(
        discovery_client, discovery.publications
    ):
        if download_error is not None:
            summary.inaccessible += 1
            issue = {"url": candidate.document_url, "error": str(download_error)}
            summary.errors.append(issue)
            record = _record_inaccessible(session, run, candidate, timestamp)
            _checkpoint_run(run, summary)
            session.commit()
            archive.append_manifest(
                _manifest_payload(
                    candidate=candidate,
                    record=record,
                    event="inaccessible",
                    run_id=run.id,
                )
            )
            continue
        assert response is not None

        source_date = candidate.source_publication_date or timestamp.date()
        if isinstance(response, DownloadedDocument):
            try:
                archived = archive.archive_file(
                    source_path=response.temporary_path,
                    checksum=response.sha256,
                    byte_length=response.byte_length,
                    category_slug=candidate.category_slug,
                    document_slug=PurePosixPath(candidate.original_filename).stem,
                    source_date=source_date,
                    original_filename=candidate.original_filename,
                )
            finally:
                response.cleanup()
        else:
            archived = archive.archive(
                content=response.body,
                category_slug=candidate.category_slug,
                document_slug=PurePosixPath(candidate.original_filename).stem,
                source_date=source_date,
                original_filename=candidate.original_filename,
            )
        latest = _latest_for_candidate(session, candidate)
        if (
            latest is not None
            and latest.document_url == candidate.document_url
            and latest.sha256 == archived.sha256
        ):
            latest.last_seen_run_id = run.id
            latest.last_seen_at = timestamp
            latest.retrieved_at = timestamp
            summary.duplicates += 1
            _checkpoint_run(run, summary)
            session.commit()
            archive.append_manifest(
                _manifest_payload(
                    candidate=candidate, record=latest, event="duplicate", run_id=run.id
                )
            )
            continue

        is_revision = latest is not None and latest.sha256 is not None
        version = (latest.version + 1) if latest is not None else 1
        if is_revision:
            latest.status = "superseded"
            summary.revisions += 1
        source, hash_duplicate = _source_document(
            session,
            candidate=candidate,
            storage_path=archived.storage_path,
            checksum=archived.sha256,
            content_type=response.content_type,
            retrieved_at=timestamp,
            version=version,
            supersedes_id=(latest.source_document_id if is_revision else None),
        )
        if hash_duplicate:
            summary.duplicates += 1
        classification, confidence, method = classify(candidate.category_slug)
        if latest is not None and latest.sha256 is None:
            record = latest
            record.source_document_id = source.id
            record.title = candidate.title
            record.document_url = candidate.document_url
            record.discovery_url = candidate.discovery_url
            record.source_publication_date = candidate.source_publication_date
            record.displayed_year = candidate.displayed_year
            record.displayed_month = candidate.displayed_month
            record.original_filename = candidate.original_filename
            record.retrieved_at = timestamp
            record.content_type = response.content_type
            record.byte_length = archived.byte_length
            record.sha256 = archived.sha256
            record.storage_path = archived.storage_path
            record.downloaded_filename = Path(archived.storage_path).name
            record.status = "archived"
            record.last_seen_run_id = run.id
            record.last_seen_at = timestamp
        else:
            record = OagfDiscoveryRecord(
                first_seen_run_id=run.id,
                last_seen_run_id=run.id,
                source_document_id=source.id,
                previous_record_id=latest.id if latest else None,
                source_organization=OAGF_ORGANIZATION,
                category_name=candidate.category_name,
                category_slug=candidate.category_slug,
                title=candidate.title,
                publication_identity=_publication_identity(candidate),
                publication_page_url=candidate.publication_page_url,
                document_url=candidate.document_url,
                discovery_url=candidate.discovery_url,
                source_publication_date=candidate.source_publication_date,
                displayed_year=candidate.displayed_year,
                displayed_month=candidate.displayed_month,
                first_discovered_at=timestamp,
                last_seen_at=timestamp,
                retrieved_at=timestamp,
                original_filename=candidate.original_filename,
                downloaded_filename=Path(archived.storage_path).name,
                content_type=response.content_type,
                byte_length=archived.byte_length,
                sha256=archived.sha256,
                storage_path=archived.storage_path,
                version=version,
                status="archived",
                classification=classification,
                classification_confidence=confidence,
                classification_method=method,
                extraction_status="not_requested",
            )
            session.add(record)
        session.flush()
        summary.archived += 1
        _checkpoint_run(run, summary)
        session.commit()
        archive.append_manifest(
            _manifest_payload(
                candidate=candidate,
                record=record,
                event="revision" if is_revision else "archived",
                run_id=run.id,
            )
        )

    run.completed_at = datetime.now(UTC)
    run.status = "completed_with_errors" if summary.errors else "completed"
    _checkpoint_run(run, summary)
    session.commit()
    return summary
