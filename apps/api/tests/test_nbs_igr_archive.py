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


def _fake_put_object():
    stored: dict[str, bytes] = {}

    def put_object(key: str, body: bytes, content_type: str) -> str:
        stored[key] = body
        return f"s3://test-bucket/{key}"

    put_object.stored = stored  # type: ignore[attr-defined]
    return put_object


def test_archive_nbs_igr_publication_registers_immutable_source(session):
    put_object = _fake_put_object()
    result = archive_nbs_igr_publication(
        session,
        _candidate(),
        put_object=put_object,
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
    assert result.storage_path == f"s3://test-bucket/nbs-igr/2023/{result.sha256}.pdf"
    assert put_object.stored[f"nbs-igr/2023/{result.sha256}.pdf"] == b"%PDF-1.7\nfixture"  # type: ignore[attr-defined]
    assert result.duplicate is False


def test_archive_nbs_igr_publication_is_idempotent_by_sha256(session):
    put_object = _fake_put_object()
    first = archive_nbs_igr_publication(
        session,
        _candidate(),
        put_object=put_object,
        fetch=lambda _url: _pdf_download(),
    )
    second = archive_nbs_igr_publication(
        session,
        _candidate(),
        put_object=put_object,
        fetch=lambda _url: _pdf_download(),
    )

    assert second.source_document_id == first.source_document_id
    assert second.sha256 == first.sha256
    assert second.duplicate is True
    assert len(list(session.scalars(select(SourceDocument)))) == 1
    assert len(put_object.stored) == 1  # type: ignore[attr-defined]


def test_archive_nbs_igr_publication_rejects_non_pdf(session):
    download = NbsIgrDownload(
        body=b"<html>not a pdf</html>",
        content_type="text/html",
        final_url="https://www.nigerianstat.gov.ng/download/1241579",
    )

    with pytest.raises(ValueError, match="not a PDF"):
        archive_nbs_igr_publication(
            session,
            _candidate(),
            put_object=_fake_put_object(),
            fetch=lambda _url: download,
        )


def test_archive_nbs_igr_publication_rejects_off_host_redirect(session):
    download = NbsIgrDownload(
        body=b"%PDF-1.7\nfixture",
        content_type="application/pdf",
        final_url="https://evil.example/download/1241579",
    )

    with pytest.raises(ValueError, match="redirected outside"):
        archive_nbs_igr_publication(
            session,
            _candidate(),
            put_object=_fake_put_object(),
            fetch=lambda _url: download,
        )


def test_archive_nbs_igr_publication_rejects_report_id_mismatch(session):
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
            put_object=_fake_put_object(),
            fetch=lambda _url: _pdf_download(),
        )
