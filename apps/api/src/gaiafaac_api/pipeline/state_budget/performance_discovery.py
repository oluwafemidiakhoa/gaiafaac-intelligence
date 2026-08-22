from __future__ import annotations

import re
import urllib.parse
from dataclasses import dataclass

from gaiafaac_api.pipeline.state_budget.discovery import (
    StateBudgetPortal,
    fetch_budget_listing,
    get_budget_portal,
)

_PERFORMANCE_RE = re.compile(
    r"(?=.*\bbudget\b)(?=.*\bperformance\b)(?=.*\breport\b)(?=.*\b(?P<year>20\d{2})\b)",
    re.IGNORECASE,
)
_APPROVED_BUDGET_RE = re.compile(r"\bapproved\b.*\bbudget\b|\bbudget\b.*\bapproved\b", re.IGNORECASE)
_QUARTER_PATTERNS: tuple[tuple[int, re.Pattern[str]], ...] = (
    (1, re.compile(r"\bQ\s*1\b|\bfirst\s+quarter\b|\b1st\s+quarter\b", re.IGNORECASE)),
    (2, re.compile(r"\bQ\s*2\b|\bsecond\s+quarter\b|\b2nd\s+quarter\b", re.IGNORECASE)),
    (3, re.compile(r"\bQ\s*3\b|\bthird\s+quarter\b|\b3rd\s+quarter\b", re.IGNORECASE)),
    (4, re.compile(r"\bQ\s*4\b|\bfourth\s+quarter\b|\b4th\s+quarter\b", re.IGNORECASE)),
)


@dataclass(frozen=True)
class BudgetPerformancePublicationCandidate:
    state_code: str
    state_name: str
    fiscal_year: int
    quarter: int
    title: str
    document_url: str
    listing_url: str


def _quarter(title: str) -> int | None:
    matches = [quarter for quarter, pattern in _QUARTER_PATTERNS if pattern.search(title)]
    if len(matches) != 1:
        return None
    return matches[0]


def _candidate_from_link(
    portal: StateBudgetPortal,
    *,
    href: str,
    title: str,
) -> BudgetPerformancePublicationCandidate | None:
    normalized_title = " ".join(title.split())
    if _APPROVED_BUDGET_RE.search(normalized_title):
        return None
    match = _PERFORMANCE_RE.search(normalized_title)
    if match is None:
        return None
    quarter = _quarter(normalized_title)
    if quarter is None:
        return None
    absolute_url = urllib.parse.urljoin(portal.listing_url, href)
    parsed = urllib.parse.urlparse(absolute_url)
    if parsed.scheme != "https" or parsed.hostname not in portal.allowed_hosts:
        return None
    return BudgetPerformancePublicationCandidate(
        state_code=portal.state_code,
        state_name=portal.state_name,
        fiscal_year=int(match.group("year")),
        quarter=quarter,
        title=normalized_title,
        document_url=absolute_url,
        listing_url=portal.listing_url,
    )


def parse_budget_performance_listing(
    portal: StateBudgetPortal,
    html: str,
) -> list[BudgetPerformancePublicationCandidate]:
    from gaiafaac_api.pipeline.state_budget.discovery import _LinkParser

    parser = _LinkParser()
    parser.feed(html)
    candidates: dict[tuple[int, int, str], BudgetPerformancePublicationCandidate] = {}
    for href, title in parser.links:
        candidate = _candidate_from_link(portal, href=href, title=title)
        if candidate is not None:
            candidates[(candidate.fiscal_year, candidate.quarter, candidate.document_url)] = candidate
    return sorted(
        candidates.values(),
        key=lambda item: (item.fiscal_year, item.quarter, item.title),
        reverse=True,
    )


def discover_budget_performance_publications(
    state_code: str,
) -> list[BudgetPerformancePublicationCandidate]:
    portal = get_budget_portal(state_code)
    return parse_budget_performance_listing(portal, fetch_budget_listing(portal))
