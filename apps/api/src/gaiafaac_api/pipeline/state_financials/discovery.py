from __future__ import annotations

import re
import urllib.parse
import urllib.request
from dataclasses import dataclass
from enum import StrEnum
from html.parser import HTMLParser

MAX_LISTING_BYTES = 5 * 1024 * 1024
_YEAR_RE = re.compile(r"\b(?P<year>20\d{2})\b")
_AUDITED_RE = re.compile(
    r"(?=.*\baudited\b)(?=.*\bfinancial\b)(?=.*\b(?:report|reports|statement|statements)\b)",
    re.I,
)
_CONTRACTOR_ARREARS_RE = re.compile(r"(?=.*\bcontractor\b)(?=.*\barrears\b)", re.I)
_EXCLUDED_AUDITED_RE = re.compile(
    r"\b(local\s+government|local\s+governments|citizens?['’]?\s+accountability|audit\s+certificate)\b",
    re.I,
)


class StateFinancialEvidenceKind(StrEnum):
    AUDITED_FINANCIAL_STATEMENT = "audited_financial_statement"
    CONTRACTOR_ARREARS_REGISTER = "contractor_arrears_register"


@dataclass(frozen=True)
class StateFinancialPortal:
    state_code: str
    state_name: str
    listing_url: str
    allowed_hosts: frozenset[str]
    evidence_kinds: frozenset[StateFinancialEvidenceKind]


@dataclass(frozen=True)
class StateFinancialPublicationCandidate:
    state_code: str
    state_name: str
    fiscal_year: int
    evidence_kind: StateFinancialEvidenceKind
    title: str
    document_url: str
    listing_url: str


PORTALS: tuple[StateFinancialPortal, ...] = (
    StateFinancialPortal(
        state_code="OY",
        state_name="Oyo",
        listing_url="https://ag.oyostate.gov.ng/resources/",
        allowed_hosts=frozenset({"ag.oyostate.gov.ng", "oyostate.gov.ng", "www.oyostate.gov.ng"}),
        evidence_kinds=frozenset({StateFinancialEvidenceKind.AUDITED_FINANCIAL_STATEMENT}),
    ),
    StateFinancialPortal(
        state_code="OY",
        state_name="Oyo",
        listing_url="https://finance.oyostate.gov.ng/resources/",
        allowed_hosts=frozenset(
            {"finance.oyostate.gov.ng", "oyostate.gov.ng", "www.oyostate.gov.ng"}
        ),
        evidence_kinds=frozenset({StateFinancialEvidenceKind.CONTRACTOR_ARREARS_REGISTER}),
    ),
    StateFinancialPortal(
        state_code="ZA",
        state_name="Zamfara",
        listing_url="https://zamfara.gov.ng/budget-finance/",
        allowed_hosts=frozenset({"zamfara.gov.ng", "www.zamfara.gov.ng"}),
        evidence_kinds=frozenset({StateFinancialEvidenceKind.AUDITED_FINANCIAL_STATEMENT}),
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


def registered_state_financial_portals() -> tuple[StateFinancialPortal, ...]:
    return PORTALS


def get_state_financial_portals(state_code: str) -> tuple[StateFinancialPortal, ...]:
    code = state_code.strip().upper()
    portals = tuple(portal for portal in PORTALS if portal.state_code == code)
    if not portals:
        raise ValueError(f"No verified state-financial portal is registered for {code!r}.")
    return portals


def _classify_title(
    portal: StateFinancialPortal,
    title: str,
) -> tuple[StateFinancialEvidenceKind, int] | None:
    normalized_title = " ".join(title.split())
    year_match = _YEAR_RE.search(normalized_title)
    if year_match is None:
        return None
    year = int(year_match.group("year"))

    if (
        StateFinancialEvidenceKind.CONTRACTOR_ARREARS_REGISTER in portal.evidence_kinds
        and _CONTRACTOR_ARREARS_RE.search(normalized_title)
    ):
        return StateFinancialEvidenceKind.CONTRACTOR_ARREARS_REGISTER, year

    if (
        StateFinancialEvidenceKind.AUDITED_FINANCIAL_STATEMENT in portal.evidence_kinds
        and _AUDITED_RE.search(normalized_title)
        and not _EXCLUDED_AUDITED_RE.search(normalized_title)
    ):
        return StateFinancialEvidenceKind.AUDITED_FINANCIAL_STATEMENT, year

    return None


def _candidate_from_link(
    portal: StateFinancialPortal,
    *,
    href: str,
    title: str,
) -> StateFinancialPublicationCandidate | None:
    classification = _classify_title(portal, title)
    if classification is None:
        return None
    evidence_kind, fiscal_year = classification
    absolute_url = urllib.parse.urljoin(portal.listing_url, href)
    parsed = urllib.parse.urlparse(absolute_url)
    if parsed.scheme != "https" or parsed.hostname not in portal.allowed_hosts:
        return None
    return StateFinancialPublicationCandidate(
        state_code=portal.state_code,
        state_name=portal.state_name,
        fiscal_year=fiscal_year,
        evidence_kind=evidence_kind,
        title=" ".join(title.split()),
        document_url=absolute_url,
        listing_url=portal.listing_url,
    )


def parse_state_financial_listing(
    portal: StateFinancialPortal,
    html: str,
) -> list[StateFinancialPublicationCandidate]:
    parser = _LinkParser()
    parser.feed(html)
    candidates: dict[
        tuple[StateFinancialEvidenceKind, int, str], StateFinancialPublicationCandidate
    ] = {}
    for href, title in parser.links:
        candidate = _candidate_from_link(portal, href=href, title=title)
        if candidate is not None:
            key = (candidate.evidence_kind, candidate.fiscal_year, candidate.document_url)
            candidates[key] = candidate
    return sorted(
        candidates.values(),
        key=lambda item: (item.fiscal_year, item.evidence_kind.value, item.title),
        reverse=True,
    )


def fetch_state_financial_listing(portal: StateFinancialPortal) -> str:
    parsed = urllib.parse.urlparse(portal.listing_url)
    if parsed.scheme != "https" or parsed.hostname not in portal.allowed_hosts:
        raise ValueError(
            "State-financial listing URL is outside its approved official host boundary."
        )
    request = urllib.request.Request(  # noqa: S310 - validated official HTTPS host
        portal.listing_url,
        headers={"User-Agent": "Gaia-Fiscal-state-financials-collector/1.0 (research)"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310
        final = urllib.parse.urlparse(response.geturl())
        if final.scheme != "https" or final.hostname not in portal.allowed_hosts:
            raise ValueError(
                "State-financial listing redirected outside the approved official host."
            )
        body = response.read(MAX_LISTING_BYTES + 1)
    if len(body) > MAX_LISTING_BYTES:
        raise ValueError("State-financial listing response exceeds the configured size limit.")
    return body.decode("utf-8", errors="replace")


def discover_state_financial_publications(
    state_code: str,
) -> list[StateFinancialPublicationCandidate]:
    publications: dict[
        tuple[StateFinancialEvidenceKind, int, str], StateFinancialPublicationCandidate
    ] = {}
    for portal in get_state_financial_portals(state_code):
        for candidate in parse_state_financial_listing(
            portal,
            fetch_state_financial_listing(portal),
        ):
            key = (candidate.evidence_kind, candidate.fiscal_year, candidate.document_url)
            publications[key] = candidate
    return sorted(
        publications.values(),
        key=lambda item: (item.fiscal_year, item.evidence_kind.value, item.title),
        reverse=True,
    )
