from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import select

from gaiafaac_api.database.enums import ProcessingStatus, SourceStatus
from gaiafaac_api.database.models import SourceDocument
from gaiafaac_api.pipeline.state_budget.archive import StateBudgetDownload
from gaiafaac_api.pipeline.state_budget.performance_archive import (
    archive_budget_performance_publication,
)
from gaiafaac_api.pipeline.state_budget.performance_discovery import (
    BudgetPerformancePublicationCandidate,
)


def _candidate() -> BudgetPerformancePublicationCandidate:
    return BudgetPerformancePublicationCandidate(
        state_code="OY",
        state_name="Oyo",
        fiscal_year=2026,
        quarter=2,
        title="Oyo State Budget Performance Report for Year 2026 Second Quarter",
        document_url="https://budget.oyostate.gov.ng/files/2026-q2-bpr.pdf",
        listing_url="https://budget.oyostate.gov.ng/resources/",
    )


def test_archive_budget_performance_is_content_addressed(session, tmp_path: Path):
    candidate = _candidate()
    body = b"%PDF-1.7\nbudget performance"

    def fetch(_portal, url: str) -> StateBudgetDownload:
        return StateBudgetDownload(body=body, content_type="application/pdf", final_url=url)

    result = archive_budget_performance_publication(
        session,
        candidate,
        archive_root=tmp_path,
        fetch=fetch,
    )
    source = session.get(SourceDocument, result.source_document_id)

    assert result.duplicate is False
    assert result.quarter == 2
    assert Path(result.storage_path).read_bytes() == body
    assert source is not None
    assert source.processing_status is ProcessingStatus.REGISTERED
    assert source.source_status is SourceStatus.REGISTERED
    assert source.document_version == "budget-performance-oy-2026-q2"
    assert source.mime_type == "application/pdf"


def test_archive_budget_performance_is_idempotent_by_sha256(session, tmp_path: Path):
    candidate = _candidate()
    body = b"%PDF-1.7\nsame performance report"

    def fetch(_portal, url: str) -> StateBudgetDownload:
        return StateBudgetDownload(body=body, content_type="application/pdf", final_url=url)

    first = archive_budget_performance_publication(
        session,
        candidate,
        archive_root=tmp_path,
        fetch=fetch,
    )
    session.commit()
    second = archive_budget_performance_publication(
        session,
        candidate,
        archive_root=tmp_path,
        fetch=fetch,
    )

    assert second.duplicate is True
    assert second.source_document_id == first.source_document_id
    assert len(list(session.scalars(select(SourceDocument)))) == 1


def test_archive_budget_performance_rejects_cross_contract_sha_collision(
    session,
    tmp_path: Path,
):
    candidate = _candidate()
    body = b"%PDF-1.7\nshared bytes"
    existing = SourceDocument(
        source_organization="Oyo State Government",
        source_url="https://budget.oyostate.gov.ng/files/approved-budget.pdf",
        original_filename="approved-budget.pdf",
        storage_path=str((tmp_path / "approved-budget.pdf").resolve()),
        sha256=__import__("hashlib").sha256(body).hexdigest(),
        mime_type="application/pdf",
        processing_status=ProcessingStatus.REGISTERED,
        source_status=SourceStatus.REGISTERED,
        document_version="approved-budget-oy-2026",
        is_demo=False,
    )
    session.add(existing)
    session.commit()

    def fetch(_portal, url: str) -> StateBudgetDownload:
        return StateBudgetDownload(body=body, content_type="application/pdf", final_url=url)

    with pytest.raises(ValueError, match="different source contract"):
        archive_budget_performance_publication(
            session,
            candidate,
            archive_root=tmp_path,
            fetch=fetch,
        )


def test_archive_budget_performance_rejects_off_host_candidate(session, tmp_path: Path):
    candidate = BudgetPerformancePublicationCandidate(
        state_code="OY",
        state_name="Oyo",
        fiscal_year=2026,
        quarter=2,
        title="Oyo State Budget Performance Report 2026 Q2",
        document_url="https://example.com/oyo-q2.pdf",
        listing_url="https://budget.oyostate.gov.ng/resources/",
    )

    def fetch(_portal, url: str) -> StateBudgetDownload:
        return StateBudgetDownload(
            body=b"%PDF-1.7\ninvalid",
            content_type="application/pdf",
            final_url=url,
        )

    with pytest.raises(ValueError, match="approved official host boundary"):
        archive_budget_performance_publication(
            session,
            candidate,
            archive_root=tmp_path,
            fetch=fetch,
        )
