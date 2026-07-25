from __future__ import annotations

import hashlib
import mimetypes
from datetime import UTC, date, datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.enums import ProcessingStatus, SourceStatus
from gaiafaac_api.database.models import SourceDocument


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def register_source_document(
    session: Session,
    *,
    path: Path,
    source_organization: str,
    publication_date: date | None = None,
    mime_type: str | None = None,
    source_url: str | None = None,
    document_version: str = "1",
    source_status: SourceStatus = SourceStatus.REGISTERED,
    processing_status: ProcessingStatus = ProcessingStatus.REGISTERED,
    is_demo: bool = False,
    commit: bool = True,
) -> SourceDocument:
    """Register file metadata and lineage without copying or interpreting its contents."""
    resolved_path = path.expanduser().resolve(strict=True)
    if not resolved_path.is_file():
        raise ValueError(f"Source path is not a regular file: {resolved_path}")
    checksum = sha256_file(resolved_path)
    existing = session.scalar(select(SourceDocument).where(SourceDocument.sha256 == checksum))
    if existing is not None:
        return existing
    detected_mime = mime_type or mimetypes.guess_type(resolved_path.name)[0]
    document = SourceDocument(
        source_organization=source_organization,
        source_url=source_url,
        original_filename=resolved_path.name,
        storage_path=str(resolved_path),
        sha256=checksum,
        mime_type=detected_mime or "application/octet-stream",
        publication_date=publication_date,
        downloaded_at=datetime.now(UTC),
        processing_status=processing_status,
        source_status=source_status,
        document_version=document_version,
        is_demo=is_demo,
    )
    session.add(document)
    if commit:
        session.commit()
        session.refresh(document)
    else:
        session.flush()
    return document
