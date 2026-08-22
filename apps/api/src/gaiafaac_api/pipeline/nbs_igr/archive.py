from __future__ import annotations

import hashlib
import re
import urllib.parse
import urllib.request
import uuid
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.enums import ProcessingStatus, SourceStatus
from gaiafaac_api.database.models import SourceDocument
from gaiafaac_api.pipeline.nbs_igr.discovery import NbsIgrPublicationCandidate

NBS_IGR_ORGANIZATION = "National Bureau of Statistics (NBS)"
NBS_IGR_DOWNLOAD_ROOT = "https://www.nigerianstat.gov.ng/download/"
MAX_NBS_IGR_DOCUMENT_BYTES = 100 * 1024 * 1024
_ALLOWED_HOSTS = {"nigerianstat.gov.ng", "www.nigerianstat.gov.ng"}
_REPORT_PATH_RE = re.compile(r"^/elibrary/read/(?P<report_id>\d+)$")
_DOWNLOAD_PATH_RE = re.compile(r"^/download/(?P<report_id>\d+)$")


@dataclass(frozen=True)
class NbsIgrDownload:
    body: bytes
    content_type: str
    final_url: str


@dataclass(frozen=True)
class NbsIgrArchiveResult:
    source_document_id: uuid.UUID
    report_id: str
    fiscal_year: int
    report_url: str
    artifact_url: str
    sha256: str
    storage_path: str
    duplicate: bool


FetchDocument = Callable[[str], NbsIgrDownload]


def _artifact_url(candidate: NbsIgrPublicationCandidate) -> str:
    if not candidate.report_id.isdigit():
        raise ValueError("NBS IGR report ID must be numeric.")
    report = urllib.parse.urlparse(candidate.report_url)
    if report.scheme != "https" or report.hostname not in _ALLOWED_HOSTS:
        raise ValueError("NBS IGR report URL is outside the approved official HTTPS host.")
    match = _REPORT_PATH_RE.fullmatch(report.path.rstrip("/"))
    if match is None or match.group("report_id") != candidate.report_id:
        raise ValueError("NBS IGR report URL does not match the discovered report ID.")
    return urllib.parse.urljoin(NBS_IGR_DOWNLOAD_ROOT, candidate.report_id)


def _fetch_document(url: str) -> NbsIgrDownload:
    parsed = urllib.parse.urlparse(url)
    match = _DOWNLOAD_PATH_RE.fullmatch(parsed.path.rstrip("/"))
    if parsed.scheme != "https" or parsed.hostname not in _ALLOWED_HOSTS or match is None:
        raise ValueError("NBS IGR artifact URL is outside the approved official download boundary.")
    request = urllib.request.Request(  # noqa: S310 - validated official NBS HTTPS host
        url,
        headers={"User-Agent": "GaiaFAAC-NBS-IGR-collector/1.0 (research)"},
    )
    with urllib.request.urlopen(request, timeout=90) as response:  # noqa: S310
        final_url = response.geturl()
        final = urllib.parse.urlparse(final_url)
        if final.scheme != "https" or final.hostname not in _ALLOWED_HOSTS:
            raise ValueError(
                "NBS IGR artifact redirected outside the approved official HTTPS host."
            )
        body = response.read(MAX_NBS_IGR_DOCUMENT_BYTES + 1)
        content_type = response.headers.get_content_type()
    return NbsIgrDownload(body=body, content_type=content_type, final_url=final_url)


def _validated_download(
    candidate: NbsIgrPublicationCandidate,
    download: NbsIgrDownload,
) -> bytes:
    _artifact_url(candidate)
    final = urllib.parse.urlparse(download.final_url)
    if final.scheme != "https" or final.hostname not in _ALLOWED_HOSTS:
        raise ValueError("NBS IGR artifact redirected outside the approved official HTTPS host.")
    if not download.body:
        raise ValueError("NBS IGR artifact response is empty.")
    if len(download.body) > MAX_NBS_IGR_DOCUMENT_BYTES:
        raise ValueError("NBS IGR artifact exceeds the configured size limit.")
    if not download.body.startswith(b"%PDF-"):
        raise ValueError("NBS IGR artifact is not a PDF according to its file signature.")
    media_type = download.content_type.partition(";")[0].strip().lower()
    if media_type not in {
        "application/pdf",
        "application/octet-stream",
        "application/x-pdf",
        "binary/octet-stream",
    }:
        raise ValueError(f"Unexpected NBS IGR artifact content type: {download.content_type}")
    return download.body


def archive_nbs_igr_publication(
    session: Session,
    candidate: NbsIgrPublicationCandidate,
    *,
    archive_root: Path = Path("data/raw/nbs/igr"),
    fetch: FetchDocument = _fetch_document,
) -> NbsIgrArchiveResult:
    """Archive one official NBS IGR PDF and register source metadata only.

    This operation does not extract, reconcile, verify, or publish any IGR value.
    """

    artifact_url = _artifact_url(candidate)
    download = fetch(artifact_url)
    body = _validated_download(candidate, download)
    checksum = hashlib.sha256(body).hexdigest()
    destination = (archive_root / str(candidate.fiscal_year) / f"{checksum}.pdf").expanduser()
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        existing_hash = hashlib.sha256(destination.read_bytes()).hexdigest()
        if existing_hash != checksum:
            raise ValueError("Existing NBS IGR archive path failed integrity verification.")
    else:
        destination.write_bytes(body)

    existing = session.scalar(select(SourceDocument).where(SourceDocument.sha256 == checksum))
    if existing is not None:
        return NbsIgrArchiveResult(
            source_document_id=existing.id,
            report_id=candidate.report_id,
            fiscal_year=candidate.fiscal_year,
            report_url=candidate.report_url,
            artifact_url=artifact_url,
            sha256=checksum,
            storage_path=existing.storage_path,
            duplicate=True,
        )

    document = SourceDocument(
        source_organization=NBS_IGR_ORGANIZATION,
        source_url=candidate.report_url,
        original_filename=(f"nbs-igr-{candidate.fiscal_year}-report-{candidate.report_id}.pdf"),
        storage_path=str(destination.resolve()),
        sha256=checksum,
        mime_type="application/pdf",
        publication_date=None,
        downloaded_at=datetime.now(UTC),
        processing_status=ProcessingStatus.REGISTERED,
        source_status=SourceStatus.REGISTERED,
        document_version=f"igr-{candidate.fiscal_year}-report-{candidate.report_id}",
        is_demo=False,
    )
    session.add(document)
    session.flush()
    return NbsIgrArchiveResult(
        source_document_id=document.id,
        report_id=candidate.report_id,
        fiscal_year=candidate.fiscal_year,
        report_url=candidate.report_url,
        artifact_url=artifact_url,
        sha256=checksum,
        storage_path=str(destination.resolve()),
        duplicate=False,
    )


def archive_nbs_igr_publications(
    session: Session,
    candidates: Iterable[NbsIgrPublicationCandidate],
    *,
    archive_root: Path = Path("data/raw/nbs/igr"),
    limit: int | None = None,
    fetch: FetchDocument = _fetch_document,
) -> list[NbsIgrArchiveResult]:
    results: list[NbsIgrArchiveResult] = []
    for index, candidate in enumerate(candidates):
        if limit is not None and index >= limit:
            break
        results.append(
            archive_nbs_igr_publication(
                session,
                candidate,
                archive_root=archive_root,
                fetch=fetch,
            )
        )
    return results
