from __future__ import annotations

import re
import urllib.parse
import urllib.request
from dataclasses import dataclass
from html.parser import HTMLParser

MAX_LISTING_BYTES = 5 * 1024 * 1024
_APPROVED_BUDGET_RE = re.compile(
    r"(?=.*\bapproved\b)(?=.*\bbudget\b)(?=.*\b(?P<year>20\d{2})\b)", re.I
)
_EXCLUDED_RE = re.compile(
    r"\b(proposed|citizens?|performance|appropriation\s+law|finance\s+law)\b", re.I
)


@dataclass(frozen=True)
class StateBudgetPortal:
    state_code: str
    state_name: str
    listing_url: str
    allowed_hosts: frozenset[str]


@dataclass(frozen=True)
class StateBudgetPublicationCandidate:
    state_code: str
    state_name: str
    fiscal_year: int
    title: str
    document_url: str
    listing_url: str


PORTALS: tuple[StateBudgetPortal, ...] = (
    StateBudgetPortal(
        state_code="OY",
        state_name="Oyo",
        listing_url="https://budget.oyostate.gov.ng/resources/",
        allowed_hosts=frozenset(
            {"budget.oyostate.gov.ng", "oyostate.gov.ng", "www.oyostate.gov.ng"}
        ),
    ),
    StateBudgetPortal(
        state_code="ZA",
        state_name="Zamfara",
        listing_url="https://zamfara.gov.ng/budget-finance/",
        allowed_hosts=frozenset({"zamfara.gov.ng", "www.zamfara.gov.ng"}),
    ),
)


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
        title = " ".join("".join(self._text).split())
        self.links.append((self._href, title))
        self._href = None
        self._text = []


def get_budget_portal(state_code: str) -> StateBudgetPortal:
    code = state_code.strip().upper()
    for portal in PORTALS:
        if portal.state_code == code:
            return portal
    raise ValueError(f"No verified state-budget portal is registered for {code!r}.")


def registered_budget_portals() -> tuple[StateBudgetPortal, ...]:
    return PORTALS


def _candidate_from_link(
    portal: StateBudgetPortal,
    *,
    href: str,
    title: str,
) -> StateBudgetPublicationCandidate | None:
    normalized_title = " ".join(title.split())
    if _EXCLUDED_RE.search(normalized_title):
        return None
    match = _APPROVED_BUDGET_RE.search(normalized_title)
    if match is None:
        return None
    absolute_url = urllib.parse.urljoin(portal.listing_url, href)
    parsed = urllib.parse.urlparse(absolute_url)
    if parsed.scheme != "https" or parsed.hostname not in portal.allowed_hosts:
        return None
    return StateBudgetPublicationCandidate(
        state_code=portal.state_code,
        state_name=portal.state_name,
        fiscal_year=int(match.group("year")),
        title=normalized_title,
        document_url=absolute_url,
        listing_url=portal.listing_url,
    )


def parse_budget_listing(
    portal: StateBudgetPortal,
    html: str,
) -> list[StateBudgetPublicationCandidate]:
    parser = _LinkParser()
    parser.feed(html)
    candidates: dict[tuple[int, str], StateBudgetPublicationCandidate] = {}
    for href, title in parser.links:
        candidate = _candidate_from_link(portal, href=href, title=title)
        if candidate is not None:
            candidates[(candidate.fiscal_year, candidate.document_url)] = candidate
    return sorted(
        candidates.values(),
        key=lambda item: (item.fiscal_year, item.title),
        reverse=True,
    )


def fetch_budget_listing(portal: StateBudgetPortal) -> str:
    parsed = urllib.parse.urlparse(portal.listing_url)
    if parsed.scheme != "https" or parsed.hostname not in portal.allowed_hosts:
        raise ValueError("State-budget listing URL is outside its approved official host boundary.")
    request = urllib.request.Request(  # noqa: S310 - validated official HTTPS host
        portal.listing_url,
        headers={"User-Agent": "GaiaFAAC-state-budget-collector/1.0 (research)"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310
        final = urllib.parse.urlparse(response.geturl())
        if final.scheme != "https" or final.hostname not in portal.allowed_hosts:
            raise ValueError("State-budget listing redirected outside the approved official host.")
        body = response.read(MAX_LISTING_BYTES + 1)
    if len(body) > MAX_LISTING_BYTES:
        raise ValueError("State-budget listing response exceeds the configured size limit.")
    return body.decode("utf-8", errors="replace")


def discover_state_budget_publications(
    state_code: str,
) -> list[StateBudgetPublicationCandidate]:
    portal = get_budget_portal(state_code)
    return parse_budget_listing(portal, fetch_budget_listing(portal))
