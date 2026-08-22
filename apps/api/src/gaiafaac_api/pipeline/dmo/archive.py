from __future__ import annotations

import hashlib
import urllib.parse
import urllib.request
import uuid
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.enums import ProcessingStatus, SourceStatus
from gaiafaac_api.database.models import SourceDocument
from gaiafaac_api.pipeline.dmo.discovery import DmoPublicationCandidate

DMO_ORGANIZATION = "Debt Management Office (DMO)"
MAX_DMO_DOCUMENT_BYTES = 50 * 1024 * 1024
_ALLOWED_HOSTS = {"dmo.gov.ng", "www.dmo.gov.ng"}


@dataclass(frozen=True)
class DmoDownload:
    body: bytes
    content_type: str
    final_url: str


@dataclass(frozen=True)
class DmoArchiveResult:
    source_document_id: uuid.UUID
    debt_kind: str
    as_of_date: str
    source_url: str
    sha256: str
    storage_path: str
    duplicate: bool


FetchDocument = Callable[[str], DmoDownload]


def _fetch_document(url: str) -> DmoDownload:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in _ALLOWED_HOSTS:
        raise ValueError("DMO document URL is outside the approved official HTTPS host.")
    request = urllib.request.Request(  # noqa: S310 - validated official DMO HTTPS host
        url,
        headers={"User-Agent": "GaiaFAAC-DMO-collector/1.0 (research)"},
    )
    with urllib.request.urlopen(request, timeout=90) as response:  # noqa: S310
        final_url = response.geturl()
        final = urllib.parse.urlparse(final_url)
        if final.scheme != "https" or final.hostname not in _ALLOWED_HOSTS:
            raise ValueError("DMO document redirected outside the approved official HTTPS host.")
        body = response.read(MAX_DMO_DOCUMENT_BYTES + 1)
        content_type = response.headers.get_content_type()
    return DmoDownload(body=body, content_type=content_type, final_url=final_url)


def _validated_download(candidate: DmoPublicationCandidate, download: DmoDownload) -> bytes:
    final = urllib.parse.urlparse(download.final_url)
    if final.scheme != "https" or final.hostname not in _ALLOWED_HOSTS:
        raise ValueError("DMO document redirected outside the approved official HTTPS host.")
    if not download.body:
        raise ValueError("DMO document response is empty.")
    if len(download.body) > MAX_DMO_DOCUMENT_BYTES:
        raise ValueError("DMO document exceeds the configured size limit.")
    if not download.body.startswith(b"%PDF-"):
        raise ValueError("DMO document is not a PDF according to its file signature.")
    media_type = download.content_type.partition(";")[0].strip().lower()
    if media_type not in {"application/pdf", "application/octet-stream"}:
        raise ValueError(f"Unexpected DMO document content type: {download.content_type}")
    source = urllib.parse.urlparse(candidate.document_url)
    if source.scheme != "https" or source.hostname not in _ALLOWED_HOSTS:
        raise ValueError("DMO candidate URL is outside the approved official HTTPS host.")
    return download.body


def _original_filename(candidate: DmoPublicationCandidate) -> str:
    name = PurePosixPath(urllib.parse.urlparse(candidate.document_url).path).name
    return name or f"dmo-{candidate.debt_kind}-{candidate.as_of_date.isoformat()}.pdf"


def archive_dmo_publication(
    session: Session,
    candidate: DmoPublicationCandidate,
    *,
    archive_root: Path = Path("data/raw/dmo"),
    fetch: FetchDocument = _fetch_document,
) -> DmoArchiveResult:
    """Archive one official DMO PDF immutably and register source metadata only.

    This operation does not extract, verify, reconcile, or publish any fiscal value.
    """

    download = fetch(candidate.document_url)
    body = _validated_download(candidate, download)
    checksum = hashlib.sha256(body).hexdigest()
    destination = (
        archive_root / candidate.debt_kind / candidate.as_of_date.isoformat() / f"{checksum}.pdf"
    ).expanduser()
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        existing_hash = hashlib.sha256(destination.read_bytes()).hexdigest()
        if existing_hash != checksum:
            raise ValueError("Existing DMO archive path failed integrity verification.")
    else:
        destination.write_bytes(body)

    existing = session.scalar(select(SourceDocument).where(SourceDocument.sha256 == checksum))
    if existing is not None:
        return DmoArchiveResult(
            source_document_id=existing.id,
            debt_kind=candidate.debt_kind,
            as_of_date=candidate.as_of_date.isoformat(),
            source_url=candidate.document_url,
            sha256=checksum,
            storage_path=existing.storage_path,
            duplicate=True,
        )

    document = SourceDocument(
        source_organization=DMO_ORGANIZATION,
        source_url=candidate.document_url,
        original_filename=_original_filename(candidate),
        storage_path=str(destination.resolve()),
        sha256=checksum,
        mime_type="application/pdf",
        publication_date=None,
        downloaded_at=datetime.now(UTC),
        processing_status=ProcessingStatus.REGISTERED,
        source_status=SourceStatus.REGISTERED,
        document_version=f"{candidate.debt_kind}-{candidate.as_of_date.isoformat()}",
        is_demo=False,
    )
    session.add(document)
    session.flush()
    return DmoArchiveResult(
        source_document_id=document.id,
        debt_kind=candidate.debt_kind,
        as_of_date=candidate.as_of_date.isoformat(),
        source_url=candidate.document_url,
        sha256=checksum,
        storage_path=str(destination.resolve()),
        duplicate=False,
    )


def archive_dmo_publications(
    session: Session,
    candidates: Iterable[DmoPublicationCandidate],
    *,
    archive_root: Path = Path("data/raw/dmo"),
    limit: int | None = None,
    fetch: FetchDocument = _fetch_document,
) -> list[DmoArchiveResult]:
    results: list[DmoArchiveResult] = []
    for index, candidate in enumerate(candidates):
        if limit is not None and index >= limit:
            break
        results.append(
            archive_dmo_publication(
                session,
                candidate,
                archive_root=archive_root,
                fetch=fetch,
            )
        )
    return results
