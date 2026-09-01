from __future__ import annotations

import re
import urllib.parse
import urllib.request
from dataclasses import dataclass
from html.parser import HTMLParser

NBS_IGR_LIBRARY_URL = (
    "https://www.nigerianstat.gov.ng/elibrary?queries%5Bsearch%5D=Internally%20Generated%20Revenue"
)
_ALLOWED_HOSTS = {"nigerianstat.gov.ng", "www.nigerianstat.gov.ng"}
_TITLE_RE = re.compile(r"Internally Generated Revenue At State Level \((?P<year>20\d{2})\)", re.I)
_REPORT_PATH_RE = re.compile(r"^/elibrary/read/(?P<report_id>\d+)$")


@dataclass(frozen=True)
class NbsIgrPublicationCandidate:
    title: str
    report_url: str
    report_id: str
    fiscal_year: int


class _RowParser(HTMLParser):
    """Groups link hrefs with nearby text by table row. The NBS eLibrary lists each
    report's title in a plain `<td>` and its download link in a separate `<td>` whose
    visible text is just an icon, so a report's title and href never share one `<a>`."""

    def __init__(self) -> None:
        super().__init__()
        self._in_row = False
        self._row_text: list[str] = []
        self._row_hrefs: list[str] = []
        self.rows: list[tuple[str, list[str]]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag == "tr":
            self._in_row = True
            self._row_text = []
            self._row_hrefs = []
        elif tag == "a" and self._in_row:
            href = dict(attrs).get("href")
            if href:
                self._row_hrefs.append(href)

    def handle_data(self, data: str) -> None:
        if self._in_row:
            self._row_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() != "tr" or not self._in_row:
            return
        text = " ".join("".join(self._row_text).split())
        self.rows.append((text, list(self._row_hrefs)))
        self._in_row = False


def _candidate_from_row(
    text: str,
    hrefs: list[str],
    *,
    listing_url: str,
) -> NbsIgrPublicationCandidate | None:
    title_match = _TITLE_RE.search(text)
    if title_match is None:
        return None
    for href in hrefs:
        absolute_url = urllib.parse.urljoin(listing_url, href)
        parsed = urllib.parse.urlparse(absolute_url)
        if parsed.scheme != "https" or parsed.hostname not in _ALLOWED_HOSTS:
            continue
        path_match = _REPORT_PATH_RE.fullmatch(parsed.path.rstrip("/"))
        if path_match is None:
            continue
        return NbsIgrPublicationCandidate(
            title=title_match.group(0),
            report_url=absolute_url,
            report_id=path_match.group("report_id"),
            fiscal_year=int(title_match.group("year")),
        )
    return None


def parse_nbs_igr_listing(
    html: str,
    *,
    listing_url: str = NBS_IGR_LIBRARY_URL,
) -> list[NbsIgrPublicationCandidate]:
    parser = _RowParser()
    parser.feed(html)
    candidates: dict[int, NbsIgrPublicationCandidate] = {}
    for text, hrefs in parser.rows:
        candidate = _candidate_from_row(text, hrefs, listing_url=listing_url)
        if candidate is not None:
            candidates[candidate.fiscal_year] = candidate
    return sorted(candidates.values(), key=lambda item: item.fiscal_year, reverse=True)


def fetch_nbs_igr_listing(url: str = NBS_IGR_LIBRARY_URL) -> str:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in _ALLOWED_HOSTS:
        raise ValueError("NBS IGR listing URL is outside the approved official HTTPS host.")
    request = urllib.request.Request(  # noqa: S310 - validated official NBS HTTPS host
        url,
        headers={"User-Agent": "GaiaFAAC-NBS-IGR-collector/1.0 (research)"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310
        final_url = urllib.parse.urlparse(response.geturl())
        if final_url.scheme != "https" or final_url.hostname not in _ALLOWED_HOSTS:
            raise ValueError("NBS IGR listing redirected outside the approved official host.")
        body = response.read(5 * 1024 * 1024 + 1)
    if len(body) > 5 * 1024 * 1024:
        raise ValueError("NBS IGR listing response exceeds the configured size limit.")
    return body.decode("utf-8", errors="replace")


def discover_nbs_igr_publications(
    url: str = NBS_IGR_LIBRARY_URL,
) -> list[NbsIgrPublicationCandidate]:
    return parse_nbs_igr_listing(fetch_nbs_igr_listing(url), listing_url=url)
