from datetime import date

import pytest
from sqlalchemy import select

from gaiafaac_api.database.models import SourceDocument
from gaiafaac_api.pipeline.dmo.archive import (
    DmoDownload,
    archive_dmo_publication,
    resolve_dmo_download_url,
)
from gaiafaac_api.pipeline.dmo.discovery import DmoPublicationCandidate

_LANDING_PAGE_URL = (
    "https://www.dmo.gov.ng/debt-profile/sub-national-debts/"
    "6001-states-and-fct-domestic-debt-stock-as-at-march-31-2026"
)


def _landing_page_html(href: str) -> str:
    return f"""
    <html><body>
      <div class="docman_download docman_download--right">
        <a class="btn btn-large btn-primary btn-block docman_download__button docman_track_download"
           href="{href}"
           data-mimetype="application/pdf">
          <span class="docman_download_label">Download</span>
        </a>
      </div>
    </body></html>
    """


def test_resolve_dmo_download_url_finds_the_real_download_button():
    html = _landing_page_html(f"{_LANDING_PAGE_URL}/file")

    resolved = resolve_dmo_download_url(html, listing_url=_LANDING_PAGE_URL)

    assert resolved == f"{_LANDING_PAGE_URL}/file"


def test_resolve_dmo_download_url_resolves_relative_hrefs():
    html = _landing_page_html("6001-states-and-fct-domestic-debt-stock-as-at-march-31-2026/file")

    resolved = resolve_dmo_download_url(html, listing_url=_LANDING_PAGE_URL)

    assert resolved == f"{_LANDING_PAGE_URL}/file"


def test_resolve_dmo_download_url_rejects_off_host_links():
    html = _landing_page_html("https://evil.example/file")

    with pytest.raises(ValueError, match="outside the approved official"):
        resolve_dmo_download_url(html, listing_url=_LANDING_PAGE_URL)


def test_resolve_dmo_download_url_requires_a_recognized_button():
    with pytest.raises(ValueError, match="does not contain a recognized download link"):
        resolve_dmo_download_url(
            "<html><body>no button here</body></html>", listing_url=_LANDING_PAGE_URL
        )


def _candidate() -> DmoPublicationCandidate:
    return DmoPublicationCandidate(
        title="States and FCT Domestic Debt Stock as at March 31, 2026",
        document_url=(
            "https://www.dmo.gov.ng/debt-profile/sub-national-debts/"
            "6001-states-and-fct-domestic-debt-stock-as-at-march-31-2026"
        ),
        debt_kind="domestic",
        as_of_date=date(2026, 3, 31),
    )


def _fake_put_object():
    stored: dict[str, bytes] = {}

    def put_object(key: str, body: bytes, content_type: str) -> str:
        stored[key] = body
        return f"s3://test-bucket/{key}"

    put_object.stored = stored  # type: ignore[attr-defined]
    return put_object


def test_archive_registers_immutable_pdf_source(session):
    body = b"%PDF-1.7\nfixture debt table\n%%EOF"
    put_object = _fake_put_object()

    result = archive_dmo_publication(
        session,
        _candidate(),
        put_object=put_object,
        fetch=lambda _url: DmoDownload(
            body=body,
            content_type="application/pdf",
            final_url=_candidate().document_url,
        ),
    )
    session.commit()

    source = session.get(SourceDocument, result.source_document_id)
    assert source is not None
    assert source.source_organization == "Debt Management Office (DMO)"
    assert source.source_url == _candidate().document_url
    assert source.sha256 == result.sha256
    assert source.document_version == "domestic-2026-03-31"
    assert result.storage_path == f"s3://test-bucket/dmo/domestic/2026-03-31/{result.sha256}.pdf"
    assert put_object.stored[f"dmo/domestic/2026-03-31/{result.sha256}.pdf"] == body  # type: ignore[attr-defined]


def test_archive_is_idempotent_by_sha256(session):
    body = b"%PDF-1.7\nsame bytes\n%%EOF"
    fetch = lambda _url: DmoDownload(  # noqa: E731 - compact deterministic test fixture
        body=body,
        content_type="application/pdf",
        final_url=_candidate().document_url,
    )
    put_object = _fake_put_object()

    first = archive_dmo_publication(session, _candidate(), put_object=put_object, fetch=fetch)
    session.commit()
    second = archive_dmo_publication(session, _candidate(), put_object=put_object, fetch=fetch)

    assert first.duplicate is False
    assert second.duplicate is True
    assert first.source_document_id == second.source_document_id
    assert len(session.scalars(select(SourceDocument)).all()) == 1
    assert len(put_object.stored) == 1  # type: ignore[attr-defined]


def test_archive_rejects_non_pdf_signature(session):
    with pytest.raises(ValueError, match="not a PDF"):
        archive_dmo_publication(
            session,
            _candidate(),
            put_object=_fake_put_object(),
            fetch=lambda _url: DmoDownload(
                body=b"<html>not pdf</html>",
                content_type="application/pdf",
                final_url=_candidate().document_url,
            ),
        )


def test_archive_rejects_off_host_redirect(session):
    with pytest.raises(ValueError, match="redirected outside"):
        archive_dmo_publication(
            session,
            _candidate(),
            put_object=_fake_put_object(),
            fetch=lambda _url: DmoDownload(
                body=b"%PDF-1.7\nfixture\n%%EOF",
                content_type="application/pdf",
                final_url="https://example.com/debt.pdf",
            ),
        )
