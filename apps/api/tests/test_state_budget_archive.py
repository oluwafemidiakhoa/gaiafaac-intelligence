from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import select

from gaiafaac_api.database.enums import ProcessingStatus, SourceStatus
from gaiafaac_api.database.models import SourceDocument
from gaiafaac_api.pipeline.state_budget.archive import (
    StateBudgetDownload,
    archive_state_budget_publication,
)
from gaiafaac_api.pipeline.state_budget.discovery import (
    StateBudgetPublicationCandidate,
)


def _candidate() -> StateBudgetPublicationCandidate:
    return StateBudgetPublicationCandidate(
        state_code="ZA",
        state_name="Zamfara",
        fiscal_year=2026,
        title="2026 Approved Budget Estimates",
        document_url="https://zamfara.gov.ng/files/2026-approved-budget.pdf",
        listing_url="https://zamfara.gov.ng/budget-finance/",
    )


def test_archive_state_budget_direct_pdf_is_content_addressed(session, tmp_path: Path):
    candidate = _candidate()
    body = b"%PDF-1.7\nstate budget"

    def fetch(_portal, url: str) -> StateBudgetDownload:
        return StateBudgetDownload(
            body=body,
            content_type="application/pdf",
            final_url=url,
        )

    result = archive_state_budget_publication(
        session,
        candidate,
        archive_root=tmp_path,
        fetch=fetch,
    )
    source = session.get(SourceDocument, result.source_document_id)

    assert result.duplicate is False
    assert result.artifact_kind == "pdf"
    assert Path(result.storage_path).read_bytes() == body
    assert source is not None
    assert source.processing_status is ProcessingStatus.REGISTERED
    assert source.source_status is SourceStatus.REGISTERED
    assert source.document_version == "approved-budget-za-2026"
    assert source.mime_type == "application/pdf"


def test_archive_state_budget_is_idempotent_by_sha256(session, tmp_path: Path):
    candidate = _candidate()
    body = b"%PDF-1.7\nsame budget"

    def fetch(_portal, url: str) -> StateBudgetDownload:
        return StateBudgetDownload(
            body=body,
            content_type="application/pdf",
            final_url=url,
        )

    first = archive_state_budget_publication(
        session,
        candidate,
        archive_root=tmp_path,
        fetch=fetch,
    )
    session.commit()
    second = archive_state_budget_publication(
        session,
        candidate,
        archive_root=tmp_path,
        fetch=fetch,
    )

    assert second.duplicate is True
    assert second.source_document_id == first.source_document_id
    assert len(list(session.scalars(select(SourceDocument)))) == 1


def test_archive_state_budget_resolves_one_official_artifact_from_detail_page(
    session,
    tmp_path: Path,
):
    candidate = StateBudgetPublicationCandidate(
        state_code="OY",
        state_name="Oyo",
        fiscal_year=2026,
        title="2026 Approved Budget",
        document_url="https://budget.oyostate.gov.ng/resources/approved-budget-2026/",
        listing_url="https://budget.oyostate.gov.ng/resources/",
    )

    def fetch(_portal, url: str) -> StateBudgetDownload:
        if url == candidate.document_url:
            return StateBudgetDownload(
                body=(
                    b'<html><body><a href="https://budget.oyostate.gov.ng/files/'
                    b'2026-approved-budget.pdf">Download</a></body></html>'
                ),
                content_type="text/html",
                final_url=url,
            )
        return StateBudgetDownload(
            body=b"%PDF-1.7\noyo budget",
            content_type="application/pdf",
            final_url=url,
        )

    result = archive_state_budget_publication(
        session,
        candidate,
        archive_root=tmp_path,
        fetch=fetch,
    )

    assert result.artifact_url.endswith("2026-approved-budget.pdf")
    assert result.artifact_kind == "pdf"


def test_archive_state_budget_rejects_ambiguous_detail_page(session, tmp_path: Path):
    candidate = StateBudgetPublicationCandidate(
        state_code="OY",
        state_name="Oyo",
        fiscal_year=2026,
        title="2026 Approved Budget",
        document_url="https://budget.oyostate.gov.ng/resources/approved-budget-2026/",
        listing_url="https://budget.oyostate.gov.ng/resources/",
    )

    def fetch(_portal, url: str) -> StateBudgetDownload:
        return StateBudgetDownload(
            body=(
                b'<a href="https://budget.oyostate.gov.ng/files/a.pdf">A</a>'
                b'<a href="https://budget.oyostate.gov.ng/files/b.pdf">B</a>'
            ),
            content_type="text/html",
            final_url=url,
        )

    with pytest.raises(ValueError, match="exactly one official PDF or XLSX"):
        archive_state_budget_publication(
            session,
            candidate,
            archive_root=tmp_path,
            fetch=fetch,
        )


def test_archive_state_budget_rejects_off_host_candidate(session, tmp_path: Path):
    candidate = StateBudgetPublicationCandidate(
        state_code="ZA",
        state_name="Zamfara",
        fiscal_year=2026,
        title="2026 Approved Budget",
        document_url="https://example.com/2026-approved-budget.pdf",
        listing_url="https://zamfara.gov.ng/budget-finance/",
    )

    def fetch(_portal, url: str) -> StateBudgetDownload:
        return StateBudgetDownload(
            body=b"%PDF-1.7\ninvalid",
            content_type="application/pdf",
            final_url=url,
        )

    with pytest.raises(ValueError, match="approved official host boundary"):
        archive_state_budget_publication(
            session,
            candidate,
            archive_root=tmp_path,
            fetch=fetch,
        )
