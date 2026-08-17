from __future__ import annotations

import hashlib
import html
import http.client
import os
import re
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath

HUB_URL = "https://oagf.gov.ng/publications/"
OAGF_HOST = "oagf.gov.ng"
USER_AGENT = "GaiaFAAC-evidence-collector/1.0 (public-finance research)"
DOCUMENT_SUFFIXES = {".pdf", ".csv", ".doc", ".docx", ".xls", ".xlsx"}
MAX_HTML_BYTES = 10 * 1024 * 1024
MAX_DOCUMENT_BYTES = 550 * 1024 * 1024
CATEGORY_NAMES = {
    "agfs-speech": "AGF's Speech",
    "faac-report": "FAAC Report",
    "funds-releases-to-mdas": "Funds Releases to MDAs",
    "gifmis-reports": "GIFMIS Reports",
    "ippis-reports": "IPPIS Reports",
    "ipsas-reports": "IPSAS Reports",
    "oagf-annual-reports": "OAGF Annual Reports",
    "oagf-journals": "OAGF Journals",
    "treasury-circulars": "Treasury Circulars",
}


class DiscoveryError(RuntimeError):
    """An official OAGF resource could not be safely discovered or retrieved."""


@dataclass(frozen=True)
class FetchResponse:
    body: bytes
    content_type: str
    final_url: str


@dataclass(frozen=True)
class DownloadedDocument:
    temporary_path: Path
    content_type: str
    final_url: str
    byte_length: int
    sha256: str

    def cleanup(self) -> None:
        self.temporary_path.unlink(missing_ok=True)


@dataclass(frozen=True)
class PublicationCategory:
    name: str
    slug: str
    url: str


@dataclass(frozen=True)
class PublicationCandidate:
    category_name: str
    category_slug: str
    title: str
    publication_page_url: str | None
    document_url: str
    discovery_url: str
    source_publication_date: date | None
    displayed_year: str | None
    displayed_month: str | None
    original_filename: str


@dataclass(frozen=True)
class DiscoveryInventory:
    categories: tuple[PublicationCategory, ...]
    publications: tuple[PublicationCandidate, ...]
    pages_checked: int
    errors: tuple[dict[str, str], ...]


class _LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, str, str]] = []
        self._href: str | None = None
        self._label = ""
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        values = dict(attrs)
        self._href = values.get("href")
        self._label = values.get("aria-label") or values.get("title") or ""
        self._text = []

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._href is not None:
            self.links.append((self._href, self._label, " ".join(self._text).strip()))
            self._href = None


def _official_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or (parsed.hostname or "").lower() != OAGF_HOST:
        raise DiscoveryError(f"Refusing non-official OAGF URL: {url}")
    return urllib.parse.urlunparse(parsed._replace(fragment=""))


def _slug_from_category_url(url: str) -> str | None:
    parts = [part for part in urllib.parse.urlparse(url).path.split("/") if part]
    if len(parts) != 2 or parts[0] != "publications":
        return None
    return parts[1]


def parse_publication_hub(document: str) -> tuple[PublicationCategory, ...]:
    parser = _LinkParser()
    parser.feed(document)
    categories: dict[str, PublicationCategory] = {}
    for href, label, text in parser.links:
        absolute = urllib.parse.urljoin(HUB_URL, href)
        slug = _slug_from_category_url(absolute)
        if slug is None:
            continue
        name = CATEGORY_NAMES.get(slug, (text or label or slug.replace("-", " ").title()).strip())
        categories[slug] = PublicationCategory(name=name, slug=slug, url=_official_url(absolute))
    return tuple(categories[key] for key in sorted(categories))


def _maximum_page(document: str) -> int:
    decoded = html.unescape(document)
    configured = re.findall(r'"max_num_pages"\s*:\s*"?(\d+)', decoded)
    linked = re.findall(r"/page/(\d+)/", decoded)
    values = [1, *(int(value) for value in configured), *(int(value) for value in linked)]
    return max(values)


def _document_url(url: str) -> bool:
    suffix = PurePosixPath(urllib.parse.urlparse(url).path).suffix.lower()
    return suffix in DOCUMENT_SUFFIXES


def _card_candidate(
    card: str, category: PublicationCategory, discovery_url: str
) -> PublicationCandidate | None:
    parser = _LinkParser()
    parser.feed(card)
    page_url: str | None = None
    title = ""
    document_url: str | None = None
    for href, label, text in parser.links:
        absolute = urllib.parse.urljoin(category.url, href)
        if "/oagf_publications/" in urllib.parse.urlparse(absolute).path:
            page_url = _official_url(absolute)
            title = label or text or title
        elif _document_url(absolute):
            document_url = _official_url(absolute)
            if label and label.lower() != "link":
                title = label
            elif text and not title:
                title = text
    if document_url is None:
        return None
    date_match = re.search(r'<time[^>]+datetime="([^"T]+)', card, flags=re.IGNORECASE)
    source_date = date.fromisoformat(date_match.group(1)) if date_match else None
    time_values = [
        re.sub(r"<[^>]+>", "", value).strip()
        for value in re.findall(r"<time\b[^>]*>(.*?)</time>", card, flags=re.IGNORECASE | re.DOTALL)
    ]
    displayed_year = next((value for value in time_values if re.fullmatch(r"\d{4}", value)), None)
    displayed_month = next(
        (value for value in time_values if re.fullmatch(r"[A-Za-z]+", value)), None
    )
    filename = urllib.parse.unquote(PurePosixPath(urllib.parse.urlparse(document_url).path).name)
    if not title:
        title = PurePosixPath(filename).stem.replace("-", " ").strip()
    return PublicationCandidate(
        category_name=category.name,
        category_slug=category.slug,
        title=html.unescape(title).strip(),
        publication_page_url=page_url,
        document_url=document_url,
        discovery_url=discovery_url,
        source_publication_date=source_date,
        displayed_year=displayed_year,
        displayed_month=displayed_month,
        original_filename=filename,
    )


def parse_listing_page(
    document: str, category: PublicationCategory, discovery_url: str | None = None
) -> tuple[tuple[PublicationCandidate, ...], int]:
    cards = re.findall(r"<article\b.*?</article>", document, flags=re.IGNORECASE | re.DOTALL)
    candidates: dict[str, PublicationCandidate] = {}
    for card in cards:
        candidate = _card_candidate(card, category, discovery_url or category.url)
        if candidate is not None:
            identity = candidate.publication_page_url or (
                f"{candidate.category_slug}:{candidate.title}:{candidate.document_url}"
            )
            candidates[identity] = candidate
    return tuple(candidates.values()), _maximum_page(document)


def http_fetch(url: str, *, maximum_bytes: int, attempts: int = 3) -> FetchResponse:
    safe_url = _official_url(url)
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        request = urllib.request.Request(  # noqa: S310 - allowlisted official HTTPS host
            safe_url, headers={"User-Agent": USER_AGENT}
        )
        try:
            with urllib.request.urlopen(request, timeout=90) as response:  # noqa: S310
                final_url = _official_url(response.geturl())
                body = response.read(maximum_bytes + 1)
                if len(body) > maximum_bytes:
                    raise DiscoveryError(f"OAGF response exceeds {maximum_bytes} bytes: {safe_url}")
                content_type = response.headers.get_content_type()
                return FetchResponse(body=body, content_type=content_type, final_url=final_url)
        except urllib.error.HTTPError as error:
            last_error = error
            if error.code not in {408, 429, 500, 502, 503, 504} or attempt == attempts:
                raise DiscoveryError(f"OAGF returned HTTP {error.code}: {safe_url}") from error
        except (OSError, http.client.HTTPException, urllib.error.URLError) as error:
            last_error = error
            if attempt == attempts:
                reason = getattr(error, "reason", error)
                raise DiscoveryError(f"OAGF request failed: {safe_url}: {reason}") from error
    raise DiscoveryError(f"OAGF request failed after retries: {safe_url}: {last_error}")


def http_download_document(
    url: str, *, maximum_bytes: int = MAX_DOCUMENT_BYTES, attempts: int = 3
) -> DownloadedDocument:
    safe_url = _official_url(url)
    last_error: Exception | None = None
    descriptor, temporary_name = tempfile.mkstemp(prefix="gaiafaac-oagf-", suffix=".source")
    os.close(descriptor)
    temporary_path = Path(temporary_name)
    for attempt in range(1, attempts + 1):
        try:
            offset = temporary_path.stat().st_size
            headers = {"User-Agent": USER_AGENT}
            if offset:
                headers["Range"] = f"bytes={offset}-"
            request = urllib.request.Request(  # noqa: S310 - allowlisted official HTTPS host
                safe_url, headers=headers
            )
            with urllib.request.urlopen(request, timeout=90) as response:  # noqa: S310
                final_url = _official_url(response.geturl())
                status = getattr(response, "status", 200)
                if offset and status != 206:
                    offset = 0
                    temporary_path.write_bytes(b"")
                content_range = response.headers.get("Content-Range")
                range_match = re.search(r"/(\d+)$", content_range or "")
                declared_length = response.headers.get("Content-Length")
                expected_total = (
                    int(range_match.group(1))
                    if range_match
                    else offset + int(declared_length)
                    if declared_length
                    else None
                )
                if expected_total is not None and expected_total > maximum_bytes:
                    raise DiscoveryError(f"OAGF response exceeds {maximum_bytes} bytes: {safe_url}")
                byte_length = offset
                with temporary_path.open("ab" if offset else "wb") as destination:
                    while block := response.read(1024 * 1024):
                        byte_length += len(block)
                        if byte_length > maximum_bytes:
                            raise DiscoveryError(
                                f"OAGF response exceeds {maximum_bytes} bytes: {safe_url}"
                            )
                        destination.write(block)
                if expected_total is not None and byte_length < expected_total:
                    raise OSError(
                        "incomplete OAGF response: "
                        f"received {byte_length} of {expected_total} bytes"
                    )
                digest = hashlib.sha256()
                with temporary_path.open("rb") as source:
                    for block in iter(lambda: source.read(1024 * 1024), b""):
                        digest.update(block)
                return DownloadedDocument(
                    temporary_path=temporary_path,
                    content_type=response.headers.get_content_type(),
                    final_url=final_url,
                    byte_length=byte_length,
                    sha256=digest.hexdigest(),
                )
        except DiscoveryError:
            temporary_path.unlink(missing_ok=True)
            raise
        except urllib.error.HTTPError as error:
            last_error = error
            if error.code not in {408, 429, 500, 502, 503, 504} or attempt == attempts:
                temporary_path.unlink(missing_ok=True)
                raise DiscoveryError(f"OAGF returned HTTP {error.code}: {safe_url}") from error
        except (OSError, http.client.HTTPException, urllib.error.URLError) as error:
            last_error = error
            if attempt == attempts:
                reason = getattr(error, "reason", error)
                temporary_path.unlink(missing_ok=True)
                raise DiscoveryError(f"OAGF request failed: {safe_url}: {reason}") from error
    temporary_path.unlink(missing_ok=True)
    raise DiscoveryError(f"OAGF request failed after retries: {safe_url}: {last_error}")


class OagfDiscoveryClient:
    def __init__(self, fetcher=http_fetch, hub_url: str = HUB_URL) -> None:
        self.fetcher = fetcher
        self.hub_url = _official_url(hub_url)

    def fetch_document(self, url: str) -> FetchResponse:
        return self.fetcher(url, maximum_bytes=MAX_DOCUMENT_BYTES)

    def download_document(self, url: str) -> DownloadedDocument:
        return http_download_document(url)

    def inventory(
        self,
        *,
        category_slug: str | None = None,
        since: date | None = None,
        limit: int | None = None,
    ) -> DiscoveryInventory:
        hub = self.fetcher(self.hub_url, maximum_bytes=MAX_HTML_BYTES)
        categories = parse_publication_hub(hub.body.decode("utf-8", errors="replace"))
        if not categories:
            raise DiscoveryError("OAGF publication hub exposed no publication categories")
        if category_slug is not None:
            categories = tuple(item for item in categories if item.slug == category_slug)
            if not categories:
                raise DiscoveryError(f"OAGF category was not found on the hub: {category_slug}")

        publications: dict[str, PublicationCandidate] = {}
        errors: list[dict[str, str]] = []
        pages_checked = 0
        for category in categories:
            page = 1
            maximum_page = 1
            while page <= maximum_page:
                url = category.url if page == 1 else f"{category.url.rstrip('/')}/page/{page}/"
                try:
                    response = self.fetcher(url, maximum_bytes=MAX_HTML_BYTES)
                    found, reported_maximum = parse_listing_page(
                        response.body.decode("utf-8", errors="replace"), category, url
                    )
                except DiscoveryError as error:
                    errors.append({"category": category.slug, "url": url, "error": str(error)})
                    page += 1
                    continue
                pages_checked += 1
                maximum_page = max(maximum_page, reported_maximum)
                for item in found:
                    if since is not None and (
                        item.source_publication_date is None or item.source_publication_date < since
                    ):
                        continue
                    identity = item.publication_page_url or (
                        f"{item.category_slug}:{item.title}:{item.document_url}"
                    )
                    publications[identity] = item
                    if limit is not None and len(publications) >= limit:
                        return DiscoveryInventory(
                            categories, tuple(publications.values()), pages_checked, tuple(errors)
                        )
                page += 1
        return DiscoveryInventory(
            categories, tuple(publications.values()), pages_checked, tuple(errors)
        )
