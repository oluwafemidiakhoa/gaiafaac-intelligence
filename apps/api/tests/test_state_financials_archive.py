from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import select

from gaiafaac_api.database.enums import ProcessingStatus, SourceStatus
from gaiafaac_api.database.models import SourceDocument
from gaiafaac_api.pipeline.state_financials.archive import (
    StateFinancialDownload,
    archive_state_financial_publication,
)
from gaiafaac_api.pipeline.state_financials.discovery import (
    StateFinancialEvidenceKind,
    StateFinancialPublicationCandidate,
)


def _audited_candidate() -> StateFinancialPublicationCandidate:
    return StateFinancialPublicationCandidate(
        state_code="OY",
        state_name="Oyo",
        fiscal_year=2025,
        evidence_kind=StateFinancialEvidenceKind.AUDITED_FINANCIAL_STATEMENT,
        title="Updated Oyo State Audited Financial Reports for Year 2025",
        document_url="https://ag.oyostate.gov.ng/files/oyo-audited-2025.pdf",
        listing_url="https://ag.oyostate.gov.ng/resources/",
    )


def test_archive_state_financial_is_content_addressed(session, tmp_path: Path):
    candidate = _audited_candidate()
    body = b"%PDF-1.7\naudited financial statement"

    def fetch(_portal, url: str) -> StateFinancialDownload:
        return StateFinancialDownload(body=body, content_type="application/pdf", final_url=url)

    result = archive_state_financial_publication(
        session,
        candidate,
        archive_root=tmp_path,
        fetch=fetch,
    )
    source = session.get(SourceDocument, result.source_document_id)

    assert result.duplicate is False
    assert result.evidence_kind is StateFinancialEvidenceKind.AUDITED_FINANCIAL_STATEMENT
    assert Path(result.storage_path).read_bytes() == body
    assert source is not None
    assert source.processing_status is ProcessingStatus.REGISTERED
    assert source.source_status is SourceStatus.REGISTERED
    assert source.document_version == "state-financial-audited-financial-statement-oy-2025"
    assert source.mime_type == "application/pdf"


def test_archive_state_financial_is_idempotent_by_sha256(session, tmp_path: Path):
    candidate = _audited_candidate()
    body = b"%PDF-1.7\nsame audited statement"

    def fetch(_portal, url: str) -> StateFinancialDownload:
        return StateFinancialDownload(body=body, content_type="application/pdf", final_url=url)

    first = archive_state_financial_publication(
        session,
        candidate,
        archive_root=tmp_path,
        fetch=fetch,
    )
    session.commit()
    second = archive_state_financial_publication(
        session,
        candidate,
        archive_root=tmp_path,
        fetch=fetch,
    )

    assert second.duplicate is True
    assert second.source_document_id == first.source_document_id
    assert len(list(session.scalars(select(SourceDocument)))) == 1


def test_archive_state_financial_rejects_cross_contract_sha_collision(session, tmp_path: Path):
    candidate = _audited_candidate()
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
        document_version="approved-budget-oy-2025",
        is_demo=False,
    )
    session.add(existing)
    session.commit()

    def fetch(_portal, url: str) -> StateFinancialDownload:
        return StateFinancialDownload(body=body, content_type="application/pdf", final_url=url)

    with pytest.raises(ValueError, match="different source contract"):
        archive_state_financial_publication(
            session,
            candidate,
            archive_root=tmp_path,
            fetch=fetch,
        )


def test_archive_state_financial_resolves_one_official_detail_artifact(session, tmp_path: Path):
    candidate = StateFinancialPublicationCandidate(
        state_code="OY",
        state_name="Oyo",
        fiscal_year=2021,
        evidence_kind=StateFinancialEvidenceKind.CONTRACTOR_ARREARS_REGISTER,
        title="Oyo State Contractor Arrears Database and Other Domestic Debt 2021",
        document_url="https://finance.oyostate.gov.ng/download/contractor-arrears-2021/",
        listing_url="https://finance.oyostate.gov.ng/resources/",
    )
    artifact_url = "https://finance.oyostate.gov.ng/files/contractor-arrears-2021.xlsx"
    xlsx_body = b"PK\x03\x04state contractor arrears"

    def fetch(_portal, url: str) -> StateFinancialDownload:
        if url == candidate.document_url:
            return StateFinancialDownload(
                body=f'<a href="{artifact_url}">Download XLSX</a>'.encode(),
                content_type="text/html",
                final_url=url,
            )
        return StateFinancialDownload(
            body=xlsx_body,
            content_type=(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ),
            final_url=url,
        )

    result = archive_state_financial_publication(
        session,
        candidate,
        archive_root=tmp_path,
        fetch=fetch,
    )

    assert result.artifact_kind == "xlsx"
    assert result.artifact_url == artifact_url
    assert Path(result.storage_path).read_bytes() == xlsx_body


def test_archive_state_financial_rejects_off_host_candidate(session, tmp_path: Path):
    candidate = StateFinancialPublicationCandidate(
        state_code="ZA",
        state_name="Zamfara",
        fiscal_year=2025,
        evidence_kind=StateFinancialEvidenceKind.AUDITED_FINANCIAL_STATEMENT,
        title="Zamfara State Audited 2025 Financial Statement",
        document_url="https://example.com/zamfara-audited-2025.pdf",
        listing_url="https://zamfara.gov.ng/budget-finance/",
    )

    def fetch(_portal, url: str) -> StateFinancialDownload:
        return StateFinancialDownload(
            body=b"%PDF-1.7\ninvalid",
            content_type="application/pdf",
            final_url=url,
        )

    with pytest.raises(ValueError, match="approved official host boundary"):
        archive_state_financial_publication(
            session,
            candidate,
            archive_root=tmp_path,
            fetch=fetch,
        )
