from __future__ import annotations

import hashlib
import urllib.parse
import urllib.request
import uuid
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.enums import ProcessingStatus, SourceStatus
from gaiafaac_api.database.models import SourceDocument
from gaiafaac_api.pipeline.state_budget.discovery import (
    StateBudgetPortal,
    StateBudgetPublicationCandidate,
    get_budget_portal,
)

MAX_ARTIFACT_BYTES = 100 * 1024 * 1024
_PDF_MIME = "application/pdf"
_XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
_ARTIFACT_SUFFIXES = {".pdf", ".xlsx"}


@dataclass(frozen=True)
class StateBudgetDownload:
    body: bytes
    content_type: str
    final_url: str


@dataclass(frozen=True)
class StateBudgetArchiveResult:
    source_document_id: uuid.UUID
    state_code: str
    fiscal_year: int
    document_url: str
    artifact_url: str
    artifact_kind: str
    sha256: str
    storage_path: str
    duplicate: bool


FetchUrl = Callable[[StateBudgetPortal, str], StateBudgetDownload]


class _ArtifactLinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        href = dict(attrs).get("href")
        if href:
            self.hrefs.append(href)


def _validate_url(portal: StateBudgetPortal, url: str) -> None:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in portal.allowed_hosts:
        raise ValueError("State-budget URL is outside the approved official host boundary.")


def _fetch_url(portal: StateBudgetPortal, url: str) -> StateBudgetDownload:
    _validate_url(portal, url)
    request = urllib.request.Request(  # noqa: S310 - validated official HTTPS host
        url,
        headers={"User-Agent": "GaiaFAAC-state-budget-collector/1.0 (research)"},
    )
    with urllib.request.urlopen(request, timeout=90) as response:  # noqa: S310
        final_url = response.geturl()
        _validate_url(portal, final_url)
        body = response.read(MAX_ARTIFACT_BYTES + 1)
        content_type = response.headers.get_content_type()
    if len(body) > MAX_ARTIFACT_BYTES:
        raise ValueError("State-budget response exceeds the configured size limit.")
    return StateBudgetDownload(
        body=body,
        content_type=content_type,
        final_url=final_url,
    )


def _artifact_type(download: StateBudgetDownload) -> tuple[str, str] | None:
    media_type = download.content_type.partition(";")[0].strip().lower()
    suffix = PurePosixPath(urllib.parse.urlparse(download.final_url).path).suffix.lower()
    if download.body.startswith(b"%PDF-"):
        return "pdf", _PDF_MIME
    if download.body.startswith(b"PK\x03\x04") and (suffix == ".xlsx" or media_type == _XLSX_MIME):
        return "xlsx", _XLSX_MIME
    return None


def _artifact_links(
    portal: StateBudgetPortal,
    *,
    base_url: str,
    html: str,
) -> list[str]:
    parser = _ArtifactLinkParser()
    parser.feed(html)
    links: set[str] = set()
    for href in parser.hrefs:
        absolute = urllib.parse.urljoin(base_url, href)
        parsed = urllib.parse.urlparse(absolute)
        suffix = PurePosixPath(parsed.path).suffix.lower()
        if (
            parsed.scheme == "https"
            and parsed.hostname in portal.allowed_hosts
            and suffix in _ARTIFACT_SUFFIXES
        ):
            links.add(absolute)
    return sorted(links)


def _resolve_artifact(
    portal: StateBudgetPortal,
    candidate: StateBudgetPublicationCandidate,
    *,
    fetch: FetchUrl,
) -> tuple[StateBudgetDownload, str, str]:
    initial = fetch(portal, candidate.document_url)
    artifact = _artifact_type(initial)
    if artifact is not None:
        kind, mime_type = artifact
        return initial, kind, mime_type

    media_type = initial.content_type.partition(";")[0].strip().lower()
    if media_type != "text/html":
        raise ValueError("State-budget document is not a supported PDF or XLSX artifact.")
    links = _artifact_links(
        portal,
        base_url=initial.final_url,
        html=initial.body.decode("utf-8", errors="replace"),
    )
    if len(links) != 1:
        raise ValueError(
            "State-budget detail page must resolve to exactly one official PDF or XLSX artifact."
        )
    resolved = fetch(portal, links[0])
    artifact = _artifact_type(resolved)
    if artifact is None:
        raise ValueError("Resolved state-budget artifact failed file-signature validation.")
    kind, mime_type = artifact
    return resolved, kind, mime_type


def _validate_candidate(
    portal: StateBudgetPortal,
    candidate: StateBudgetPublicationCandidate,
) -> None:
    if candidate.state_code != portal.state_code:
        raise ValueError("State-budget candidate does not match the registered portal state.")
    if candidate.listing_url != portal.listing_url:
        raise ValueError("State-budget candidate listing URL does not match the registry.")
    _validate_url(portal, candidate.document_url)


def archive_state_budget_publication(
    session: Session,
    candidate: StateBudgetPublicationCandidate,
    *,
    archive_root: Path = Path("data/raw/state-budget"),
    fetch: FetchUrl = _fetch_url,
) -> StateBudgetArchiveResult:
    """Archive one approved state-budget artifact without extracting fiscal values."""

    portal = get_budget_portal(candidate.state_code)
    _validate_candidate(portal, candidate)
    download, artifact_kind, mime_type = _resolve_artifact(
        portal,
        candidate,
        fetch=fetch,
    )
    checksum = hashlib.sha256(download.body).hexdigest()
    destination = (
        archive_root
        / candidate.state_code.lower()
        / str(candidate.fiscal_year)
        / f"{checksum}.{artifact_kind}"
    ).expanduser()
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        existing_hash = hashlib.sha256(destination.read_bytes()).hexdigest()
        if existing_hash != checksum:
            raise ValueError("Existing state-budget archive path failed integrity verification.")
    else:
        destination.write_bytes(download.body)

    existing = session.scalar(select(SourceDocument).where(SourceDocument.sha256 == checksum))
    if existing is not None:
        return StateBudgetArchiveResult(
            source_document_id=existing.id,
            state_code=candidate.state_code,
            fiscal_year=candidate.fiscal_year,
            document_url=candidate.document_url,
            artifact_url=download.final_url,
            artifact_kind=artifact_kind,
            sha256=checksum,
            storage_path=existing.storage_path,
            duplicate=True,
        )

    artifact_name = PurePosixPath(urllib.parse.urlparse(download.final_url).path).name
    original_filename = artifact_name or (
        f"{candidate.state_code.lower()}-{candidate.fiscal_year}-approved-budget.{artifact_kind}"
    )
    document = SourceDocument(
        source_organization=f"{candidate.state_name} State Government",
        source_url=download.final_url,
        original_filename=original_filename,
        storage_path=str(destination.resolve()),
        sha256=checksum,
        mime_type=mime_type,
        publication_date=None,
        downloaded_at=datetime.now(UTC),
        processing_status=ProcessingStatus.REGISTERED,
        source_status=SourceStatus.REGISTERED,
        document_version=(
            f"approved-budget-{candidate.state_code.lower()}-{candidate.fiscal_year}"
        ),
        is_demo=False,
    )
    session.add(document)
    session.flush()
    return StateBudgetArchiveResult(
        source_document_id=document.id,
        state_code=candidate.state_code,
        fiscal_year=candidate.fiscal_year,
        document_url=candidate.document_url,
        artifact_url=download.final_url,
        artifact_kind=artifact_kind,
        sha256=checksum,
        storage_path=str(destination.resolve()),
        duplicate=False,
    )


def archive_state_budget_publications(
    session: Session,
    candidates: Iterable[StateBudgetPublicationCandidate],
    *,
    archive_root: Path = Path("data/raw/state-budget"),
    limit: int | None = None,
    fetch: FetchUrl = _fetch_url,
) -> list[StateBudgetArchiveResult]:
    results: list[StateBudgetArchiveResult] = []
    for index, candidate in enumerate(candidates):
        if limit is not None and index >= limit:
            break
        results.append(
            archive_state_budget_publication(
                session,
                candidate,
                archive_root=archive_root,
                fetch=fetch,
            )
        )
    return results
