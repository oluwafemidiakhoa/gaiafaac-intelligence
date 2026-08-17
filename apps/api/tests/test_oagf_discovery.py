from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pytest

from gaiafaac_api.pipeline.oagf.discovery import (
    HUB_URL,
    DiscoveryError,
    FetchResponse,
    OagfDiscoveryClient,
    http_download_document,
    parse_publication_hub,
)

FIXTURES = Path(__file__).parent / "fixtures" / "oagf"


def _response(name: str, url: str) -> FetchResponse:
    return FetchResponse(
        body=(FIXTURES / name).read_bytes(), content_type="text/html", final_url=url
    )


def test_inventory_discovers_categories_and_traverses_pagination() -> None:
    responses = {
        HUB_URL: _response("publications.html", HUB_URL),
        "https://oagf.gov.ng/publications/faac-report/": _response(
            "faac-page-1.html", "https://oagf.gov.ng/publications/faac-report/"
        ),
        "https://oagf.gov.ng/publications/faac-report/page/2/": _response(
            "faac-page-2.html", "https://oagf.gov.ng/publications/faac-report/page/2/"
        ),
        "https://oagf.gov.ng/publications/treasury-circulars/": _response(
            "treasury-circulars.html",
            "https://oagf.gov.ng/publications/treasury-circulars/",
        ),
    }

    def fetch(url: str, *, maximum_bytes: int) -> FetchResponse:
        assert maximum_bytes > 0
        return responses[url]

    inventory = OagfDiscoveryClient(fetcher=fetch).inventory()

    assert [item.slug for item in inventory.categories] == [
        "faac-report",
        "treasury-circulars",
    ]
    assert inventory.pages_checked == 3
    assert [item.title for item in inventory.publications] == [
        "Disbursement June, 2026",
        "Disbursement May, 2026",
    ]
    assert inventory.publications[0].source_publication_date.isoformat() == "2026-06-01"
    assert inventory.publications[0].displayed_year == "2026"
    assert inventory.publications[0].displayed_month == "June"
    assert inventory.publications[1].publication_page_url == (
        "https://oagf.gov.ng/oagf_publications/disbursement-may-2026/"
    )


def test_inventory_limit_and_since_are_applied_without_document_downloads() -> None:
    calls: list[str] = []

    def fetch(url: str, *, maximum_bytes: int) -> FetchResponse:
        calls.append(url)
        if url == HUB_URL:
            return _response("publications.html", url)
        return _response("faac-page-1.html", url)

    inventory = OagfDiscoveryClient(fetcher=fetch).inventory(
        category_slug="faac-report", since=None, limit=1
    )

    assert len(inventory.publications) == 1
    assert calls == [HUB_URL, "https://oagf.gov.ng/publications/faac-report/"]


def test_inventory_records_a_category_page_failure_and_continues() -> None:
    def fetch(url: str, *, maximum_bytes: int) -> FetchResponse:
        if url == HUB_URL:
            return _response("publications.html", url)
        if "faac-report" in url:
            raise DiscoveryError("temporary failure")
        return _response("treasury-circulars.html", url)

    inventory = OagfDiscoveryClient(fetcher=fetch).inventory()

    assert inventory.pages_checked == 1
    assert inventory.errors[0]["category"] == "faac-report"
    assert inventory.publications == ()


def test_hub_rejects_external_category_links() -> None:
    document = '<a href="https://example.com/publications/faac-report/">FAAC</a>'
    with pytest.raises(DiscoveryError, match="non-official"):
        parse_publication_hub(document)


def test_inventory_fails_closed_on_malformed_hub() -> None:
    def fetch(url: str, *, maximum_bytes: int) -> FetchResponse:
        return FetchResponse(b"<html>changed layout</html>", "text/html", url)

    with pytest.raises(DiscoveryError, match="no publication categories"):
        OagfDiscoveryClient(fetcher=fetch).inventory()


def test_distinct_publications_are_preserved_when_they_share_a_document_url() -> None:
    shared = "https://oagf.gov.ng/wp-content/uploads/shared.pdf"
    page = f"""
    <article><a href="/oagf_publications/first/" aria-label="First"></a>
      <a href="{shared}">Download</a></article>
    <article><a href="/oagf_publications/second/" aria-label="Second"></a>
      <a href="{shared}">Download</a></article>
    """
    hub = '<a href="/publications/faac-report/">FAAC Report</a>'

    def fetch(url: str, *, maximum_bytes: int) -> FetchResponse:
        body = hub if url == HUB_URL else page
        return FetchResponse(body.encode(), "text/html", url)

    inventory = OagfDiscoveryClient(fetcher=fetch).inventory()

    assert [item.title for item in inventory.publications] == ["First", "Second"]


def test_document_download_streams_to_a_hashed_temporary_file(monkeypatch) -> None:
    class Headers:
        def get(self, name: str):
            return str(len(b"%PDF-streamed")) if name == "Content-Length" else None

        def get_content_type(self) -> str:
            return "application/pdf"

    class Response(BytesIO):
        headers = Headers()

        def geturl(self) -> str:
            return "https://oagf.gov.ng/source.pdf"

        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.close()

    monkeypatch.setattr(
        "gaiafaac_api.pipeline.oagf.discovery.urllib.request.urlopen",
        lambda request, timeout: Response(b"%PDF-streamed"),
    )

    downloaded = http_download_document(
        "https://oagf.gov.ng/source.pdf", maximum_bytes=100, attempts=1
    )
    try:
        assert downloaded.temporary_path.read_bytes() == b"%PDF-streamed"
        assert downloaded.byte_length == len(b"%PDF-streamed")
        assert len(downloaded.sha256) == 64
    finally:
        downloaded.cleanup()

    assert downloaded.temporary_path.exists() is False


def test_document_download_resumes_with_http_range_after_disconnect(monkeypatch) -> None:
    content = b"%PDF-resumable"
    calls: list[str | None] = []

    class Headers:
        def __init__(self, *, length: int, content_range: str | None = None) -> None:
            self.length = length
            self.content_range = content_range

        def get(self, name: str):
            if name == "Content-Length":
                return str(self.length)
            if name == "Content-Range":
                return self.content_range
            return None

        def get_content_type(self) -> str:
            return "application/pdf"

    class Response(BytesIO):
        def __init__(self, body: bytes, *, headers: Headers, status: int) -> None:
            super().__init__(body)
            self.headers = headers
            self.status = status

        def geturl(self) -> str:
            return "https://oagf.gov.ng/source.pdf"

        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.close()

    class DisconnectingResponse(Response):
        def __init__(self) -> None:
            super().__init__(content[:5], headers=Headers(length=len(content)), status=200)
            self.reads = 0

        def read(self, size: int = -1) -> bytes:
            self.reads += 1
            if self.reads == 1:
                return super().read(size)
            raise OSError("connection closed")

    def urlopen(request, timeout):
        range_header = request.get_header("Range")
        calls.append(range_header)
        if len(calls) == 1:
            return DisconnectingResponse()
        return Response(
            content[5:],
            headers=Headers(
                length=len(content) - 5,
                content_range=f"bytes 5-{len(content) - 1}/{len(content)}",
            ),
            status=206,
        )

    monkeypatch.setattr("gaiafaac_api.pipeline.oagf.discovery.urllib.request.urlopen", urlopen)

    downloaded = http_download_document(
        "https://oagf.gov.ng/source.pdf", maximum_bytes=100, attempts=2
    )
    try:
        assert downloaded.temporary_path.read_bytes() == content
        assert calls == [None, "bytes=5-"]
    finally:
        downloaded.cleanup()
