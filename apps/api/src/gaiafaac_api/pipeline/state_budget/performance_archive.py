from __future__ import annotations

import hashlib
import urllib.parse
import uuid
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.enums import ProcessingStatus, SourceStatus
from gaiafaac_api.database.models import SourceDocument
from gaiafaac_api.pipeline.state_budget.archive import (
    FetchUrl,
    _fetch_url,
    _resolve_artifact,
    _validate_url,
)
from gaiafaac_api.pipeline.state_budget.discovery import get_budget_portal
from gaiafaac_api.pipeline.state_budget.performance_discovery import (
    BudgetPerformancePublicationCandidate,
)


@dataclass(frozen=True)
class BudgetPerformanceArchiveResult:
    source_document_id: uuid.UUID
    state_code: str
    fiscal_year: int
    quarter: int
    document_url: str
    artifact_url: str
    artifact_kind: str
    sha256: str
    storage_path: str
    duplicate: bool


def _expected_version(candidate: BudgetPerformancePublicationCandidate) -> str:
    return (
        f"budget-performance-{candidate.state_code.lower()}-"
        f"{candidate.fiscal_year}-q{candidate.quarter}"
    )


def _validate_candidate(candidate: BudgetPerformancePublicationCandidate) -> None:
    portal = get_budget_portal(candidate.state_code)
    if candidate.state_code != portal.state_code:
        raise ValueError("Budget-performance candidate does not match the registered portal state.")
    if candidate.listing_url != portal.listing_url:
        raise ValueError("Budget-performance candidate listing URL does not match the registry.")
    if candidate.quarter not in {1, 2, 3, 4}:
        raise ValueError("Budget-performance candidate quarter must be between 1 and 4.")
    _validate_url(portal, candidate.document_url)


def archive_budget_performance_publication(
    session: Session,
    candidate: BudgetPerformancePublicationCandidate,
    *,
    archive_root: Path = Path("data/raw/state-budget-performance"),
    fetch: FetchUrl = _fetch_url,
) -> BudgetPerformanceArchiveResult:
    """Archive one quarterly budget-performance artifact without extracting fiscal values."""

    _validate_candidate(candidate)
    portal = get_budget_portal(candidate.state_code)
    download, artifact_kind, mime_type = _resolve_artifact(
        portal,
        candidate,
        fetch=fetch,
    )
    checksum = hashlib.sha256(download.body).hexdigest()
    version = _expected_version(candidate)
    destination = (
        archive_root
        / candidate.state_code.lower()
        / str(candidate.fiscal_year)
        / f"q{candidate.quarter}"
        / f"{checksum}.{artifact_kind}"
    ).expanduser()
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        existing_hash = hashlib.sha256(destination.read_bytes()).hexdigest()
        if existing_hash != checksum:
            raise ValueError("Existing budget-performance archive failed integrity verification.")
    else:
        destination.write_bytes(download.body)

    existing = session.scalar(select(SourceDocument).where(SourceDocument.sha256 == checksum))
    if existing is not None:
        if (
            existing.document_version != version
            or existing.source_organization != f"{candidate.state_name} State Government"
        ):
            raise ValueError(
                "Budget-performance SHA-256 is already registered under a different source contract."
            )
        return BudgetPerformanceArchiveResult(
            source_document_id=existing.id,
            state_code=candidate.state_code,
            fiscal_year=candidate.fiscal_year,
            quarter=candidate.quarter,
            document_url=candidate.document_url,
            artifact_url=download.final_url,
            artifact_kind=artifact_kind,
            sha256=checksum,
            storage_path=existing.storage_path,
            duplicate=True,
        )

    artifact_name = PurePosixPath(urllib.parse.urlparse(download.final_url).path).name
    original_filename = artifact_name or (
        f"{candidate.state_code.lower()}-{candidate.fiscal_year}-"
        f"q{candidate.quarter}-budget-performance.{artifact_kind}"
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
        document_version=version,
        is_demo=False,
    )
    session.add(document)
    session.flush()
    return BudgetPerformanceArchiveResult(
        source_document_id=document.id,
        state_code=candidate.state_code,
        fiscal_year=candidate.fiscal_year,
        quarter=candidate.quarter,
        document_url=candidate.document_url,
        artifact_url=download.final_url,
        artifact_kind=artifact_kind,
        sha256=checksum,
        storage_path=str(destination.resolve()),
        duplicate=False,
    )


def archive_budget_performance_publications(
    session: Session,
    candidates: Iterable[BudgetPerformancePublicationCandidate],
    *,
    archive_root: Path = Path("data/raw/state-budget-performance"),
    limit: int | None = None,
    fetch: FetchUrl = _fetch_url,
) -> list[BudgetPerformanceArchiveResult]:
    results: list[BudgetPerformanceArchiveResult] = []
    for index, candidate in enumerate(candidates):
        if limit is not None and index >= limit:
            break
        results.append(
            archive_budget_performance_publication(
                session,
                candidate,
                archive_root=archive_root,
                fetch=fetch,
            )
        )
    return results
