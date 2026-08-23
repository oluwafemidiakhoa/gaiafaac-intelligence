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
from gaiafaac_api.pipeline.state_financials.discovery import (
    StateFinancialEvidenceKind,
    StateFinancialPortal,
    StateFinancialPublicationCandidate,
    get_state_financial_portals,
)

MAX_ARTIFACT_BYTES = 100 * 1024 * 1024
_PDF_MIME = "application/pdf"
_XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
_ARTIFACT_SUFFIXES = {".pdf", ".xlsx"}


@dataclass(frozen=True)
class StateFinancialDownload:
    body: bytes
    content_type: str
    final_url: str


@dataclass(frozen=True)
class StateFinancialArchiveResult:
    source_document_id: uuid.UUID
    state_code: str
    fiscal_year: int
    evidence_kind: StateFinancialEvidenceKind
    document_url: str
    artifact_url: str
    artifact_kind: str
    sha256: str
    storage_path: str
    duplicate: bool


FetchUrl = Callable[[StateFinancialPortal, str], StateFinancialDownload]


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


def _validate_url(portal: StateFinancialPortal, url: str) -> None:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in portal.allowed_hosts:
        raise ValueError("State-financial URL is outside the approved official host boundary.")


def _fetch_url(portal: StateFinancialPortal, url: str) -> StateFinancialDownload:
    _validate_url(portal, url)
    request = urllib.request.Request(  # noqa: S310 - validated official HTTPS host
        url,
        headers={"User-Agent": "Gaia-Fiscal-state-financials-collector/1.0 (research)"},
    )
    with urllib.request.urlopen(request, timeout=90) as response:  # noqa: S310
        final_url = response.geturl()
        _validate_url(portal, final_url)
        body = response.read(MAX_ARTIFACT_BYTES + 1)
        content_type = response.headers.get_content_type()
    if len(body) > MAX_ARTIFACT_BYTES:
        raise ValueError("State-financial response exceeds the configured size limit.")
    return StateFinancialDownload(
        body=body,
        content_type=content_type,
        final_url=final_url,
    )


def _artifact_type(download: StateFinancialDownload) -> tuple[str, str] | None:
    media_type = download.content_type.partition(";")[0].strip().lower()
    suffix = PurePosixPath(urllib.parse.urlparse(download.final_url).path).suffix.lower()
    if download.body.startswith(b"%PDF-"):
        return "pdf", _PDF_MIME
    if download.body.startswith(b"PK\x03\x04") and (suffix == ".xlsx" or media_type == _XLSX_MIME):
        return "xlsx", _XLSX_MIME
    return None


def _artifact_links(
    portal: StateFinancialPortal,
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
    portal: StateFinancialPortal,
    candidate: StateFinancialPublicationCandidate,
    *,
    fetch: FetchUrl,
) -> tuple[StateFinancialDownload, str, str]:
    initial = fetch(portal, candidate.document_url)
    artifact = _artifact_type(initial)
    if artifact is not None:
        artifact_kind, mime_type = artifact
        return initial, artifact_kind, mime_type

    media_type = initial.content_type.partition(";")[0].strip().lower()
    if media_type != "text/html":
        raise ValueError("State-financial document is not a supported PDF or XLSX artifact.")
    links = _artifact_links(
        portal,
        base_url=initial.final_url,
        html=initial.body.decode("utf-8", errors="replace"),
    )
    if len(links) != 1:
        raise ValueError(
            "State-financial detail page must resolve to exactly one official PDF or XLSX artifact."
        )
    resolved = fetch(portal, links[0])
    artifact = _artifact_type(resolved)
    if artifact is None:
        raise ValueError("Resolved state-financial artifact failed file-signature validation.")
    artifact_kind, mime_type = artifact
    return resolved, artifact_kind, mime_type


def _portal_for_candidate(candidate: StateFinancialPublicationCandidate) -> StateFinancialPortal:
    for portal in get_state_financial_portals(candidate.state_code):
        if (
            portal.listing_url == candidate.listing_url
            and candidate.evidence_kind in portal.evidence_kinds
        ):
            return portal
    raise ValueError("State-financial candidate does not match a registered source contract.")


def _expected_version(candidate: StateFinancialPublicationCandidate) -> str:
    evidence_kind = candidate.evidence_kind.value.replace("_", "-")
    return f"state-financial-{evidence_kind}-{candidate.state_code.lower()}-{candidate.fiscal_year}"


def _validate_candidate(
    portal: StateFinancialPortal,
    candidate: StateFinancialPublicationCandidate,
) -> None:
    if candidate.state_code != portal.state_code or candidate.state_name != portal.state_name:
        raise ValueError("State-financial candidate does not match the registered portal state.")
    if candidate.listing_url != portal.listing_url:
        raise ValueError("State-financial candidate listing URL does not match the registry.")
    if candidate.evidence_kind not in portal.evidence_kinds:
        raise ValueError("State-financial evidence kind is not allowed for this registered portal.")
    if candidate.fiscal_year < 2000:
        raise ValueError("State-financial fiscal year is outside the governed range.")
    _validate_url(portal, candidate.document_url)


def archive_state_financial_publication(
    session: Session,
    candidate: StateFinancialPublicationCandidate,
    *,
    archive_root: Path = Path("data/raw/state-financials"),
    fetch: FetchUrl = _fetch_url,
) -> StateFinancialArchiveResult:
    """Archive one official state-financial artifact without extracting fiscal values."""

    portal = _portal_for_candidate(candidate)
    _validate_candidate(portal, candidate)
    download, artifact_kind, mime_type = _resolve_artifact(portal, candidate, fetch=fetch)
    checksum = hashlib.sha256(download.body).hexdigest()
    version = _expected_version(candidate)
    destination = (
        archive_root
        / candidate.state_code.lower()
        / str(candidate.fiscal_year)
        / candidate.evidence_kind.value
        / f"{checksum}.{artifact_kind}"
    ).expanduser()
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        existing_hash = hashlib.sha256(destination.read_bytes()).hexdigest()
        if existing_hash != checksum:
            raise ValueError("Existing state-financial archive failed integrity verification.")
    else:
        destination.write_bytes(download.body)

    source_organization = f"{candidate.state_name} State Government"
    existing = session.scalar(select(SourceDocument).where(SourceDocument.sha256 == checksum))
    if existing is not None:
        if (
            existing.document_version != version
            or existing.source_organization != source_organization
        ):
            raise ValueError(
                "State-financial SHA-256 is already registered under a different source contract."
            )
        return StateFinancialArchiveResult(
            source_document_id=existing.id,
            state_code=candidate.state_code,
            fiscal_year=candidate.fiscal_year,
            evidence_kind=candidate.evidence_kind,
            document_url=candidate.document_url,
            artifact_url=download.final_url,
            artifact_kind=artifact_kind,
            sha256=checksum,
            storage_path=existing.storage_path,
            duplicate=True,
        )

    artifact_name = PurePosixPath(urllib.parse.urlparse(download.final_url).path).name
    fallback_name = (
        f"{candidate.state_code.lower()}-{candidate.fiscal_year}-"
        f"{candidate.evidence_kind.value}.{artifact_kind}"
    )
    document = SourceDocument(
        source_organization=source_organization,
        source_url=download.final_url,
        original_filename=artifact_name or fallback_name,
        storage_path=str(destination.resolve()),
        sha256=checksum,
        mime_type=mime_type,
        publication_date=None,
        downloaded_at=datetime.now(UTC),
        processing_status=ProcessingStatus.REGISTERED,
        source_status=SourceStatus.REGISTERED,
        document_version=version,
        is_demo=False,
    )
    session.add(document)
    session.flush()
    return StateFinancialArchiveResult(
        source_document_id=document.id,
        state_code=candidate.state_code,
        fiscal_year=candidate.fiscal_year,
        evidence_kind=candidate.evidence_kind,
        document_url=candidate.document_url,
        artifact_url=download.final_url,
        artifact_kind=artifact_kind,
        sha256=checksum,
        storage_path=str(destination.resolve()),
        duplicate=False,
    )


def archive_state_financial_publications(
    session: Session,
    candidates: Iterable[StateFinancialPublicationCandidate],
    *,
    archive_root: Path = Path("data/raw/state-financials"),
    limit: int | None = None,
    fetch: FetchUrl = _fetch_url,
) -> list[StateFinancialArchiveResult]:
    results: list[StateFinancialArchiveResult] = []
    for index, candidate in enumerate(candidates):
        if limit is not None and index >= limit:
            break
        results.append(
            archive_state_financial_publication(
                session,
                candidate,
                archive_root=archive_root,
                fetch=fetch,
            )
        )
    return results
