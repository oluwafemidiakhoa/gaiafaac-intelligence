from __future__ import annotations

import hashlib
import html
import re
import tempfile
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import Decimal
from html.parser import HTMLParser
from pathlib import Path
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.models import (
    ExtractionRun,
    NationalDistribution,
    ReportingPeriod,
    SourceDocument,
    StateAllocation,
)
from gaiafaac_api.database.national_evidence_models import (
    NationalEvidenceCandidate,
    NationalEvidenceSyncRun,
)
from gaiafaac_api.pipeline.national_distribution import (
    NationalDistributionImportRequest,
    import_national_distribution,
)

USER_AGENT = "GaiaFAAC-national-evidence-collector/1.0 (public-finance research)"
MAX_HTML_BYTES = 4 * 1024 * 1024
MAX_SEARCH_PAGES = 6

STATUS_DISCOVERED = "discovered"
STATUS_ARCHIVED = "archived"
STATUS_PARSED = "parsed"
STATUS_DEFERRED = "deferred"
STATUS_QUARANTINED = "quarantined"
STATUS_IMPORTED = "imported"
STATUS_DUPLICATE = "duplicate"

MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}
MONTH_PATTERN = "|".join(month.title() for month in MONTHS)
MONEY_PATTERN = r"(?:₦|N|NGN)\s*([0-9][0-9,]*(?:\.[0-9]+)?)\s*(trillion|billion|million)"


class NationalEvidenceError(RuntimeError):
    """An official national source could not be processed safely."""


@dataclass(frozen=True)
class OfficialSource:
    organization: str
    host: str
    search_url: str


OFFICIAL_SOURCES = (
    OfficialSource(
        organization="Federal Ministry of Information and National Orientation",
        host="fmino.gov.ng",
        search_url="https://fmino.gov.ng/?s=FAAC",
    ),
    OfficialSource(
        organization="Federal Ministry of Finance",
        host="finance.gov.ng",
        search_url="https://finance.gov.ng/?s=FAAC",
    ),
)


@dataclass(frozen=True)
class FetchResponse:
    body: bytes
    content_type: str
    final_url: str


class Fetcher(Protocol):
    def __call__(self, url: str, *, allowed_host: str) -> FetchResponse: ...


@dataclass(frozen=True)
class DiscoveredPage:
    organization: str
    host: str
    title: str
    url: str


@dataclass(frozen=True)
class MoneyClaim:
    original: str
    normalized_billion: str


@dataclass(frozen=True)
class ExtractedNationalClaims:
    net_distributable_amount: MoneyClaim
    federal_amount: MoneyClaim
    states_amount: MoneyClaim
    local_governments_amount: MoneyClaim
    derivation_amount: MoneyClaim
    allocation_period_month: date
    disbursement_month: date

    def as_dict(self) -> dict[str, object]:
        return {
            "reported_unit": "billion_naira",
            "net_distributable_amount": self.net_distributable_amount.__dict__,
            "federal_amount": self.federal_amount.__dict__,
            "states_amount": self.states_amount.__dict__,
            "local_governments_amount": self.local_governments_amount.__dict__,
            "derivation_amount": self.derivation_amount.__dict__,
            "allocation_period_month": self.allocation_period_month.isoformat(),
            "disbursement_month": self.disbursement_month.isoformat(),
            "derivation_treatment": "separate",
        }


@dataclass(frozen=True)
class QueuedNationalEvidence:
    candidate_id: str
    run_id: str
    distribution_id: str
    reporting_period_id: str
    reporting_label: str
    finding_count: int
    blocking_finding_count: int


@dataclass
class NationalCollectionSummary:
    checked_urls: list[str] = field(default_factory=list)
    queued: list[QueuedNationalEvidence] = field(default_factory=list)
    deferred: list[dict[str, str]] = field(default_factory=list)
    quarantined: list[dict[str, str]] = field(default_factory=list)
    duplicates: list[str] = field(default_factory=list)
    errors: list[dict[str, str]] = field(default_factory=list)


class _LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, str]] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        self._href = dict(attrs).get("href")
        self._text = []

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._href is not None:
            self.links.append((self._href, " ".join(self._text).strip()))
            self._href = None
            self._text = []


class _TextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._ignored_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript", "svg"}:
            self._ignored_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript", "svg"} and self._ignored_depth:
            self._ignored_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self._ignored_depth:
            self.parts.append(data)


def _official_url(url: str, allowed_host: str) -> str:
    parsed = urllib.parse.urlparse(url)
    hostname = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or hostname != allowed_host:
        raise NationalEvidenceError(f"Refusing non-official URL: {url}")
    return urllib.parse.urlunparse(parsed._replace(fragment=""))


def http_fetch(url: str, *, allowed_host: str) -> FetchResponse:
    safe_url = _official_url(url, allowed_host)
    request = urllib.request.Request(safe_url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310 - URL is allowlisted
        final_url = _official_url(response.geturl(), allowed_host)
        content_type = response.headers.get_content_type()
        body = response.read(MAX_HTML_BYTES + 1)
    if len(body) > MAX_HTML_BYTES:
        raise NationalEvidenceError(f"Official HTML exceeds {MAX_HTML_BYTES} bytes: {safe_url}")
    if content_type not in {"text/html", "application/xhtml+xml"}:
        raise NationalEvidenceError(f"Expected HTML from official source, got {content_type}")
    return FetchResponse(body=body, content_type=content_type, final_url=final_url)


def _decode_html(response: FetchResponse) -> str:
    return response.body.decode("utf-8", errors="replace")


def _article_text(document: str) -> str:
    parser = _TextParser()
    parser.feed(document)
    return re.sub(r"\s+", " ", html.unescape(" ".join(parser.parts))).strip()


def _article_title(document: str, fallback: str) -> str:
    match = re.search(r"<title[^>]*>(.*?)</title>", document, flags=re.I | re.S)
    if match is None:
        return fallback
    title = re.sub(r"<[^>]+>", " ", match.group(1))
    title = re.sub(r"\s+", " ", html.unescape(title)).strip()
    return title[:500] or fallback


def _publication_date(document: str) -> date | None:
    matches = re.findall(
        r"<time\b[^>]*datetime=[\"'](\d{4}-\d{2}-\d{2})(?:T[^\"']*)?[\"']",
        document,
        flags=re.I,
    )
    if not matches:
        return None
    try:
        return date.fromisoformat(matches[0])
    except ValueError:
        return None


def _looks_like_faac_release(url: str, label: str) -> bool:
    value = f"{url} {label}".casefold()
    return "faac" in value and any(
        token in value
        for token in (
            "share",
            "shared",
            "revenue",
            "federation-account",
            "federation account",
            "states",
            "lgcs",
            "local-governments",
        )
    )


def discover_official_pages(
    *,
    fetcher: Fetcher = http_fetch,
    max_pages: int = MAX_SEARCH_PAGES,
) -> tuple[DiscoveredPage, ...]:
    discovered: dict[str, DiscoveredPage] = {}
    for source in OFFICIAL_SOURCES:
        for page_number in range(1, max_pages + 1):
            search_url = source.search_url
            if page_number > 1:
                separator = "&" if "?" in search_url else "?"
                search_url = f"{search_url}{separator}paged={page_number}"
            try:
                response = fetcher(search_url, allowed_host=source.host)
            except Exception:
                if page_number == 1:
                    raise
                break
            parser = _LinkParser()
            parser.feed(_decode_html(response))
            accepted = 0
            for href, label in parser.links:
                absolute = urllib.parse.urljoin(response.final_url, href)
                try:
                    absolute = _official_url(absolute, source.host)
                except NationalEvidenceError:
                    continue
                parsed = urllib.parse.urlparse(absolute)
                if parsed.path in {"", "/"} or not _looks_like_faac_release(absolute, label):
                    continue
                if "/category/" in parsed.path or "/tag/" in parsed.path or "/page/" in parsed.path:
                    continue
                discovered[absolute] = DiscoveredPage(
                    organization=source.organization,
                    host=source.host,
                    title=(label.strip() or parsed.path.strip("/").replace("-", " "))[:500],
                    url=absolute,
                )
                accepted += 1
            if accepted == 0 and page_number > 1:
                break
    return tuple(discovered[url] for url in sorted(discovered))


def _month(value: str, year: str) -> date:
    return date(int(year), MONTHS[value.casefold()], 1)


def _unique_month(matches: list[tuple[str, str]], *, field_name: str) -> date:
    values = {_month(month, year) for month, year in matches}
    if len(values) != 1:
        raise NationalEvidenceError(
            f"{field_name} is {'missing' if not values else 'ambiguous'} in the official source"
        )
    return next(iter(values))


def _extract_months(text: str) -> tuple[date, date]:
    allocation_matches = re.findall(
        rf"(?:for|from)\s+(?:the\s+)?(?:month\s+of\s+)?({MONTH_PATTERN})[,]?\s+(20\d{{2}})\s+revenue",
        text,
        flags=re.I,
    )
    if not allocation_matches:
        allocation_matches = re.findall(
            rf"revenue\s+(?:for|from)\s+(?:the\s+)?(?:month\s+of\s+)?({MONTH_PATTERN})[,]?\s+(20\d{{2}})",
            text,
            flags=re.I,
        )
    if not allocation_matches:
        allocation_matches = re.findall(
            rf"for\s+the\s+month\s+of\s+({MONTH_PATTERN})[,]?\s+(20\d{{2}})",
            text,
            flags=re.I,
        )
    meeting_matches = re.findall(
        rf"(?:at|during)\s+(?:the\s+)?({MONTH_PATTERN})\s+(20\d{{2}})\s+"
        rf"(?:Federation\s+Account\s+Allocation\s+Committee|FAAC)(?:\s+meeting)?",
        text,
        flags=re.I,
    )
    if not meeting_matches:
        meeting_matches = re.findall(
            rf"(?:at|during)\s+(?:its\s+|the\s+)?({MONTH_PATTERN})\s+(20\d{{2}})\s+meeting",
            text,
            flags=re.I,
        )
    allocation = _unique_month(allocation_matches, field_name="allocation period")
    disbursement = _unique_month(meeting_matches, field_name="disbursement/meeting month")
    return allocation, disbursement


def _normalize_billion(number: str, unit: str) -> str:
    raw = number.replace(",", "")
    amount = Decimal(raw)
    factor = {
        "trillion": Decimal("1000"),
        "billion": Decimal("1"),
        "million": Decimal("0.001"),
    }[unit.casefold()]
    value = amount * factor
    if value == value.to_integral():
        return format(value.quantize(Decimal("1")), "f")
    return format(value.normalize(), "f")


def _money_from_match(match: re.Match[str]) -> MoneyClaim:
    return MoneyClaim(
        original=match.group(0).strip(),
        normalized_billion=_normalize_billion(match.group(1), match.group(2)),
    )


def _claim_after(text: str, subject: str, *, window: int = 180) -> MoneyClaim:
    for subject_match in re.finditer(subject, text, flags=re.I):
        segment = text[subject_match.end() : subject_match.end() + window]
        money = re.search(MONEY_PATTERN, segment, flags=re.I)
        if money is not None:
            return _money_from_match(money)
    raise NationalEvidenceError(f"Required national claim is missing for {subject}")


def _total_claim(text: str) -> MoneyClaim:
    patterns = (
        rf"(?:shared|share|distributed|distributable)\b.{{0,100}}?{MONEY_PATTERN}",
        rf"(?:total\s+sum\s+of|total\s+of)\s*{MONEY_PATTERN}",
    )
    candidates: list[re.Match[str]] = []
    for pattern in patterns:
        for match in re.finditer(pattern, text, flags=re.I):
            context = match.group(0).casefold()
            if "gross" not in context:
                candidates.append(match)
    if not candidates:
        raise NationalEvidenceError("Required distributable-total claim is missing")
    match = candidates[0]
    # The amount groups are the final two capture groups in each pattern.
    amount = match.group(match.lastindex - 1 if match.lastindex else 1)
    unit = match.group(match.lastindex or 2)
    original_match = re.search(
        rf"(?:₦|N|NGN)\s*{re.escape(amount)}\s*{re.escape(unit)}",
        match.group(0),
        flags=re.I,
    )
    if original_match is None:
        raise NationalEvidenceError("Distributable-total amount could not be normalized")
    raw_match = re.search(MONEY_PATTERN, original_match.group(0), flags=re.I)
    if raw_match is None:
        raise NationalEvidenceError("Distributable-total amount could not be parsed")
    return _money_from_match(raw_match)


def extract_national_claims(document: str) -> ExtractedNationalClaims:
    text = _article_text(document)
    allocation_month, disbursement_month = _extract_months(text)
    federal = _claim_after(text, r"Federal\s+Government")
    states = _claim_after(text, r"(?:State\s+Governments?|States)")
    lgas = _claim_after(text, r"(?:Local\s+Government\s+Councils?|LGCs?)")

    derivation_match = None
    for match in re.finditer(MONEY_PATTERN, text, flags=re.I):
        context = text[max(0, match.start() - 120) : match.end() + 120].casefold()
        if "derivation" in context:
            derivation_match = match
            break
    if derivation_match is None:
        raise NationalEvidenceError("Required 13% derivation claim is missing")

    return ExtractedNationalClaims(
        net_distributable_amount=_total_claim(text),
        federal_amount=federal,
        states_amount=states,
        local_governments_amount=lgas,
        derivation_amount=_money_from_match(derivation_match),
        allocation_period_month=allocation_month,
        disbursement_month=disbursement_month,
    )


def _threshold_month(months_back: int) -> date:
    if months_back < 1:
        raise ValueError("months_back must be at least 1")
    today = date.today().replace(day=1)
    index = today.year * 12 + today.month - 1 - months_back
    return date(index // 12, index % 12 + 1, 1)


def _find_period(
    session: Session, claims: ExtractedNationalClaims
) -> tuple[ReportingPeriod | None, str | None]:
    periods = list(
        session.scalars(
            select(ReportingPeriod).where(
                ReportingPeriod.revenue_month == claims.disbursement_month,
                ReportingPeriod.is_demo.is_(False),
            )
        )
    )
    exact = [
        period
        for period in periods
        if period.disbursement_month in (None, claims.disbursement_month)
        and period.allocation_period_month in (None, claims.allocation_period_month)
    ]
    if not exact:
        return None, "NO_REPORTING_PERIOD"
    if len(exact) != 1:
        return None, "AMBIGUOUS_REPORTING_PERIOD"
    period = exact[0]
    if not period.is_published:
        return period, "JURISDICTION_PERIOD_NOT_PUBLISHED"
    return period, None


def _harden_period_semantics(period: ReportingPeriod, claims: ExtractedNationalClaims) -> None:
    if period.revenue_month != claims.disbursement_month:
        raise NationalEvidenceError("Legacy reporting-period key does not match explicit meeting month")
    if period.disbursement_month not in (None, claims.disbursement_month):
        raise NationalEvidenceError("Existing disbursement month conflicts with official source")
    if period.allocation_period_month not in (None, claims.allocation_period_month):
        raise NationalEvidenceError("Existing allocation period conflicts with official source")
    if period.disbursement_month is None:
        period.disbursement_month = claims.disbursement_month
    if period.allocation_period_month is None:
        period.allocation_period_month = claims.allocation_period_month


def _existing_source(session: Session, checksum: str) -> SourceDocument | None:
    return session.scalar(select(SourceDocument).where(SourceDocument.sha256 == checksum))


def _source_used_by_states(session: Session, source_id: uuid.UUID) -> bool:
    return (
        session.scalar(
            select(StateAllocation.id)
            .where(StateAllocation.source_document_id == source_id)
            .limit(1)
        )
        is not None
    )


def _source_used_nationally(session: Session, source_id: uuid.UUID) -> NationalDistribution | None:
    return session.scalar(
        select(NationalDistribution)
        .where(NationalDistribution.source_document_id == source_id)
        .limit(1)
    )


def _mark(
    candidate: NationalEvidenceCandidate,
    *,
    status: str,
    reason_code: str | None = None,
    details: dict[str, object] | None = None,
) -> None:
    candidate.status = status
    candidate.reason_code = reason_code
    candidate.details = details or {}


def _process_candidate(
    session: Session,
    candidate: NationalEvidenceCandidate,
    claims: ExtractedNationalClaims,
) -> QueuedNationalEvidence | None:
    candidate.extracted_claims = claims.as_dict()
    candidate.disbursement_month = claims.disbursement_month
    candidate.allocation_period_month = claims.allocation_period_month
    _mark(candidate, status=STATUS_PARSED)

    period, reason = _find_period(session, claims)
    if reason is not None:
        candidate.reporting_period_id = period.id if period is not None else None
        _mark(candidate, status=STATUS_DEFERRED, reason_code=reason)
        session.commit()
        return None
    assert period is not None
    candidate.reporting_period_id = period.id
    _harden_period_semantics(period, claims)

    existing_source = _existing_source(session, candidate.sha256)
    if existing_source is not None:
        candidate.source_document_id = existing_source.id
        if _source_used_by_states(session, existing_source.id):
            _mark(
                candidate,
                status=STATUS_QUARANTINED,
                reason_code="SOURCE_REUSED_BY_STATE_ALLOCATION",
            )
            session.commit()
            return None
        distribution = _source_used_nationally(session, existing_source.id)
        if distribution is not None:
            run = session.scalar(
                select(ExtractionRun)
                .where(ExtractionRun.source_document_id == existing_source.id)
                .order_by(ExtractionRun.created_at.desc())
                .limit(1)
            )
            candidate.extraction_run_id = run.id if run is not None else None
            _mark(candidate, status=STATUS_DUPLICATE, reason_code="NATIONAL_SOURCE_ALREADY_IMPORTED")
            session.commit()
            return None

    suffix = ".html"
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as handle:
            handle.write(candidate.content)
            temporary_path = Path(handle.name)
        result = import_national_distribution(
            session,
            NationalDistributionImportRequest(
                path=temporary_path,
                reporting_period_id=period.id,
                source_organization=candidate.source_organization,
                reported_unit="billion_naira",
                net_distributable_amount=claims.net_distributable_amount.normalized_billion,
                federal_amount=claims.federal_amount.normalized_billion,
                states_amount=claims.states_amount.normalized_billion,
                local_governments_amount=claims.local_governments_amount.normalized_billion,
                derivation_amount=claims.derivation_amount.normalized_billion,
                derivation_treatment="separate",
                publication_date=candidate.publication_date,
                source_url=candidate.source_url,
                source_type=candidate.source_type,
                source_authority=candidate.source_authority,
                canonical_source_status=candidate.canonical_source_status,
            ),
        )
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)

    run = session.get(ExtractionRun, uuid.UUID(result.run_id))
    if run is None:
        raise NationalEvidenceError("Imported extraction run could not be reloaded")
    source = session.get(SourceDocument, run.source_document_id)
    if source is None:
        raise NationalEvidenceError("Imported source document could not be reloaded")
    if source.sha256 != candidate.sha256:
        raise NationalEvidenceError("Archived candidate fingerprint differs from imported source")

    source.storage_path = f"db://national-evidence-candidates/{candidate.id}"
    candidate.source_document_id = source.id
    candidate.extraction_run_id = run.id
    _mark(candidate, status=STATUS_IMPORTED)
    session.commit()
    return QueuedNationalEvidence(
        candidate_id=str(candidate.id),
        run_id=result.run_id,
        distribution_id=result.distribution_id,
        reporting_period_id=result.reporting_period_id,
        reporting_label=period.reporting_label,
        finding_count=result.finding_count,
        blocking_finding_count=result.blocking_finding_count,
    )


def run_national_evidence_collection(
    session: Session,
    *,
    months_back: int = 24,
    fetcher: Fetcher = http_fetch,
    max_pages: int = MAX_SEARCH_PAGES,
) -> NationalCollectionSummary:
    threshold = _threshold_month(months_back)
    started = datetime.now(UTC)
    sync_run = NationalEvidenceSyncRun(
        started_at=started,
        status="running",
        options={"months_back": months_back, "max_pages": max_pages},
        errors=[],
    )
    session.add(sync_run)
    session.commit()

    summary = NationalCollectionSummary()
    try:
        pages = discover_official_pages(fetcher=fetcher, max_pages=max_pages)
        sync_run.candidates_discovered = len(pages)
        session.commit()

        for page in pages:
            summary.checked_urls.append(page.url)
            try:
                response = fetcher(page.url, allowed_host=page.host)
                checksum = hashlib.sha256(response.body).hexdigest()
                existing_candidate = session.scalar(
                    select(NationalEvidenceCandidate).where(
                        NationalEvidenceCandidate.sha256 == checksum
                    )
                )
                document = _decode_html(response)
                title = _article_title(document, page.title)
                publication_date = _publication_date(document)
                claims = extract_national_claims(document)

                if claims.disbursement_month < threshold:
                    continue

                if existing_candidate is None:
                    candidate = NationalEvidenceCandidate(
                        first_seen_run_id=sync_run.id,
                        last_seen_run_id=sync_run.id,
                        source_organization=page.organization,
                        source_url=response.final_url,
                        title=title,
                        publication_date=publication_date,
                        content_type=response.content_type,
                        byte_length=len(response.body),
                        sha256=checksum,
                        content=response.body,
                        status=STATUS_ARCHIVED,
                        details={},
                    )
                    session.add(candidate)
                    session.commit()
                    sync_run.candidates_archived += 1
                else:
                    candidate = existing_candidate
                    candidate.last_seen_run_id = sync_run.id
                    if candidate.status in {
                        STATUS_IMPORTED,
                        STATUS_DUPLICATE,
                        STATUS_QUARANTINED,
                    }:
                        summary.duplicates.append(page.url)
                        sync_run.duplicates += 1
                        session.commit()
                        continue

                queued = _process_candidate(session, candidate, claims)
                if queued is not None:
                    summary.queued.append(queued)
                    sync_run.imported += 1
                elif candidate.status == STATUS_DEFERRED:
                    summary.deferred.append(
                        {"url": page.url, "reason": candidate.reason_code or "DEFERRED"}
                    )
                    sync_run.deferred += 1
                elif candidate.status == STATUS_QUARANTINED:
                    summary.quarantined.append(
                        {"url": page.url, "reason": candidate.reason_code or "QUARANTINED"}
                    )
                    sync_run.quarantined += 1
                elif candidate.status == STATUS_DUPLICATE:
                    summary.duplicates.append(page.url)
                    sync_run.duplicates += 1
                session.commit()
            except NationalEvidenceError as error:
                session.rollback()
                summary.quarantined.append({"url": page.url, "reason": str(error)})
                sync_run = session.get(NationalEvidenceSyncRun, sync_run.id)
                assert sync_run is not None
                sync_run.quarantined += 1
                session.commit()
            except Exception as error:  # noqa: BLE001 - one official page must not stop the pass
                session.rollback()
                summary.errors.append({"url": page.url, "error": str(error)})
                sync_run = session.get(NationalEvidenceSyncRun, sync_run.id)
                assert sync_run is not None
                sync_run.errors = [*sync_run.errors, {"url": page.url, "error": str(error)}]
                session.commit()

        sync_run = session.get(NationalEvidenceSyncRun, sync_run.id)
        assert sync_run is not None
        sync_run.status = "completed" if not summary.errors else "completed_with_errors"
        sync_run.completed_at = datetime.now(UTC)
        session.commit()
        return summary
    except Exception as error:
        session.rollback()
        sync_run = session.get(NationalEvidenceSyncRun, sync_run.id)
        if sync_run is not None:
            sync_run.status = "failed"
            sync_run.completed_at = datetime.now(UTC)
            sync_run.errors = [*sync_run.errors, {"stage": "discovery", "error": str(error)}]
            session.commit()
        raise
