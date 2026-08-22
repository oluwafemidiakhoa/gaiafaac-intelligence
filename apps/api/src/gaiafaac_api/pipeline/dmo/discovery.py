from __future__ import annotations

import re
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime
from html.parser import HTMLParser

DMO_SUBNATIONAL_URL = "https://www.dmo.gov.ng/debt-profile/sub-national-debts"
_ALLOWED_HOSTS = {"dmo.gov.ng", "www.dmo.gov.ng"}
_TITLE_RE = re.compile(
    r"States(?:, FCT and Federal Government's| and FCT) "
    r"(?P<kind>Domestic|External) Debt Stock as at "
    r"(?P<as_of>[A-Za-z]+ \d{1,2}, \d{4})",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class DmoPublicationCandidate:
    title: str
    document_url: str
    debt_kind: str
    as_of_date: date


class _LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._href: str | None = None
        self._text: list[str] = []
        self.links: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        self._href = dict(attrs).get("href")
        self._text = []

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() != "a" or self._href is None:
            return
        text = " ".join("".join(self._text).split())
        self.links.append((self._href, text))
        self._href = None
        self._text = []


def _candidate_from_link(
    href: str,
    title: str,
    *,
    listing_url: str,
) -> DmoPublicationCandidate | None:
    match = _TITLE_RE.search(title)
    if match is None:
        return None
    absolute_url = urllib.parse.urljoin(listing_url, href)
    parsed = urllib.parse.urlparse(absolute_url)
    if parsed.scheme != "https" or parsed.hostname not in _ALLOWED_HOSTS:
        return None
    return DmoPublicationCandidate(
        title=title,
        document_url=absolute_url,
        debt_kind=match.group("kind").lower(),
        as_of_date=datetime.strptime(match.group("as_of"), "%B %d, %Y").date(),
    )


def parse_dmo_subnational_listing(
    html: str,
    *,
    listing_url: str = DMO_SUBNATIONAL_URL,
) -> list[DmoPublicationCandidate]:
    parser = _LinkParser()
    parser.feed(html)
    candidates: dict[tuple[str, date], DmoPublicationCandidate] = {}
    for href, title in parser.links:
        candidate = _candidate_from_link(href, title, listing_url=listing_url)
        if candidate is None:
            continue
        candidates[(candidate.debt_kind, candidate.as_of_date)] = candidate
    return sorted(
        candidates.values(),
        key=lambda item: (item.as_of_date, item.debt_kind),
        reverse=True,
    )


def fetch_dmo_subnational_listing(url: str = DMO_SUBNATIONAL_URL) -> str:
    request = urllib.request.Request(  # noqa: S310 - fixed official DMO https host
        url,
        headers={"User-Agent": "GaiaFAAC-DMO-collector/1.0 (research)"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310
        final_url = urllib.parse.urlparse(response.geturl())
        if final_url.scheme != "https" or final_url.hostname not in _ALLOWED_HOSTS:
            raise ValueError("DMO listing redirected outside the approved official host.")
        body = response.read(5 * 1024 * 1024 + 1)
    if len(body) > 5 * 1024 * 1024:
        raise ValueError("DMO listing response exceeds the configured size limit.")
    return body.decode("utf-8", errors="replace")


def discover_dmo_subnational_publications(
    url: str = DMO_SUBNATIONAL_URL,
) -> list[DmoPublicationCandidate]:
    return parse_dmo_subnational_listing(fetch_dmo_subnational_listing(url), listing_url=url)
