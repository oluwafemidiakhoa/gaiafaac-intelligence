from pathlib import Path

import pytest
from sqlalchemy import select

from gaiafaac_api.database.enums import ProcessingStatus, SourceStatus
from gaiafaac_api.database.models import SourceDocument
from gaiafaac_api.pipeline.nbs_igr.archive import (
    NbsIgrDownload,
    archive_nbs_igr_publication,
)
from gaiafaac_api.pipeline.nbs_igr.discovery import NbsIgrPublicationCandidate


def _candidate() -> NbsIgrPublicationCandidate:
    return NbsIgrPublicationCandidate(
        title="Internally Generated Revenue At State Level (2023)",
        report_url="https://www.nigerianstat.gov.ng/elibrary/read/1241579",
        report_id="1241579",
        fiscal_year=2023,
    )


def _pdf_download() -> NbsIgrDownload:
    return NbsIgrDownload(
        body=b"%PDF-1.7\nfixture",
        content_type="application/pdf",
        final_url="https://www.nigerianstat.gov.ng/download/1241579",
    )


def test_archive_nbs_igr_publication_registers_immutable_source(session, tmp_path: Path):
    result = archive_nbs_igr_publication(
        session,
        _candidate(),
        archive_root=tmp_path,
        fetch=lambda _url: _pdf_download(),
    )
    source = session.get(SourceDocument, result.source_document_id)

    assert source is not None
    assert source.source_organization == "National Bureau of Statistics (NBS)"
    assert source.source_url == "https://www.nigerianstat.gov.ng/elibrary/read/1241579"
    assert source.document_version == "igr-2023-report-1241579"
    assert source.processing_status is ProcessingStatus.REGISTERED
    assert source.source_status is SourceStatus.REGISTERED
    assert result.artifact_url == "https://www.nigerianstat.gov.ng/download/1241579"
    assert Path(result.storage_path).read_bytes() == b"%PDF-1.7\nfixture"
    assert Path(result.storage_path).name == f"{result.sha256}.pdf"
    assert result.duplicate is False


def test_archive_nbs_igr_publication_is_idempotent_by_sha256(session, tmp_path: Path):
    first = archive_nbs_igr_publication(
        session,
        _candidate(),
        archive_root=tmp_path,
        fetch=lambda _url: _pdf_download(),
    )
    second = archive_nbs_igr_publication(
        session,
        _candidate(),
        archive_root=tmp_path,
        fetch=lambda _url: _pdf_download(),
    )

    assert second.source_document_id == first.source_document_id
    assert second.sha256 == first.sha256
    assert second.duplicate is True
    assert len(list(session.scalars(select(SourceDocument)))) == 1


def test_archive_nbs_igr_publication_rejects_non_pdf(session, tmp_path: Path):
    download = NbsIgrDownload(
        body=b"<html>not a pdf</html>",
        content_type="text/html",
        final_url="https://www.nigerianstat.gov.ng/download/1241579",
    )

    with pytest.raises(ValueError, match="not a PDF"):
        archive_nbs_igr_publication(
            session,
            _candidate(),
            archive_root=tmp_path,
            fetch=lambda _url: download,
        )


def test_archive_nbs_igr_publication_rejects_off_host_redirect(session, tmp_path: Path):
    download = NbsIgrDownload(
        body=b"%PDF-1.7\nfixture",
        content_type="application/pdf",
        final_url="https://evil.example/download/1241579",
    )

    with pytest.raises(ValueError, match="redirected outside"):
        archive_nbs_igr_publication(
            session,
            _candidate(),
            archive_root=tmp_path,
            fetch=lambda _url: download,
        )


def test_archive_nbs_igr_publication_rejects_report_id_mismatch(session, tmp_path: Path):
    candidate = NbsIgrPublicationCandidate(
        title="Internally Generated Revenue At State Level (2023)",
        report_url="https://www.nigerianstat.gov.ng/elibrary/read/1241579",
        report_id="9999999",
        fiscal_year=2023,
    )

    with pytest.raises(ValueError, match="does not match"):
        archive_nbs_igr_publication(
            session,
            candidate,
            archive_root=tmp_path,
            fetch=lambda _url: _pdf_download(),
        )
