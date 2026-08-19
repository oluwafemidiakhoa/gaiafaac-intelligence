from __future__ import annotations

import hashlib
import json
import re
import tempfile
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.enums import (
    ExtractionStatus,
    ProcessingStatus,
    ReportedUnit,
    SourceStatus,
    VerificationStatus,
)
from gaiafaac_api.database.models import (
    AuditLog,
    ExtractionRun,
    NationalDistribution,
    ReportingPeriod,
    SourceDocument,
)
from gaiafaac_api.database.national_evidence_models import (
    NationalEvidenceCandidate,
    NationalEvidenceSyncRun,
)
from gaiafaac_api.pipeline import national_evidence as legacy
from gaiafaac_api.pipeline.monetary import parse_money
from gaiafaac_api.pipeline.national_distribution import (
    NationalDistributionImportRequest,
    import_national_distribution,
    validate_national_distribution,
)

PARSER_VERSION = "3"
TERMINAL_CANDIDATE_STATUSES = {
    legacy.STATUS_IMPORTED,
    legacy.STATUS_DUPLICATE,
    legacy.STATUS_QUARANTINED,
}


class NationalEvidenceError(legacy.NationalEvidenceError):
    """A structured fail-closed error raised by the hardened national parser."""

    def __init__(
        self,
        reason_code: str,
        message: str,
        *,
        details: dict[str, object] | None = None,
    ) -> None:
        super().__init__(message)
        self.reason_code = reason_code
        self.details = details or {}


@dataclass
class NationalRepairSummary:
    repaired: list[str] = field(default_factory=list)
    quarantined: list[dict[str, str]] = field(default_factory=list)
    duplicates: list[dict[str, str]] = field(default_factory=list)
    skipped: list[dict[str, str]] = field(default_factory=list)


def _money_from_match(match: re.Match[str]) -> legacy.MoneyClaim:
    return legacy.MoneyClaim(
        original=match.group(0).strip(),
        normalized_billion=legacy._normalize_billion(match.group(1), match.group(2)),
    )


def _money_value(claim: legacy.MoneyClaim) -> Decimal:
    return Decimal(claim.normalized_billion)


def _claim_quantum_billion(claim: legacy.MoneyClaim) -> Decimal:
    match = re.search(legacy.MONEY_PATTERN, claim.original, flags=re.I)
    if match is None:
        return Decimal("0.001")
    number = match.group(1).replace(",", "")
    decimals = len(number.partition(".")[2]) if "." in number else 0
    unit_factor = {
        "trillion": Decimal("1000"),
        "billion": Decimal("1"),
        "million": Decimal("0.001"),
    }[match.group(2).casefold()]
    return unit_factor / (Decimal(10) ** decimals)


def _claims_materially_differ(
    left: legacy.MoneyClaim,
    right: legacy.MoneyClaim,
) -> bool:
    tolerance = max(_claim_quantum_billion(left), _claim_quantum_billion(right)) / Decimal(2)
    return abs(_money_value(left) - _money_value(right)) > tolerance


def _sentences(text: str) -> list[str]:
    return [item.strip() for item in re.split(r"(?<=[.!?])\s+", text) if item.strip()]


def _recipient_claim(text: str, subject: str, *, label: str) -> legacy.MoneyClaim:
    verbs = (
        r"(?:received|got|gets|was\s+allocated|were\s+allocated|"
        r"was\s+given|were\s+given)"
    )
    for sentence in _sentences(text):
        if re.search(subject, sentence, flags=re.I) is None:
            continue
        forward = re.search(
            rf"{subject}.{{0,50}}?\b{verbs}\b.{{0,35}}?{legacy.MONEY_PATTERN}",
            sentence,
            flags=re.I,
        )
        if forward is not None:
            return _money_from_match(forward)
        reverse = re.search(
            rf"{legacy.MONEY_PATTERN}.{{0,50}}?\b(?:allocated|given|shared)\b"
            rf".{{0,25}}?\b(?:to|for)\b.{{0,25}}?{subject}",
            sentence,
            flags=re.I,
        )
        if reverse is not None:
            return _money_from_match(reverse)
    raise NationalEvidenceError(
        "NATIONAL_RECIPIENT_CLAIM_MISSING",
        f"Required national recipient claim is missing for {label}",
        details={"recipient": label},
    )


def _body_total_claims(text: str) -> list[legacy.MoneyClaim]:
    patterns = (
        rf"\bshared\s+(?:a\s+)?(?:total\s+)?(?:sum\s+of\s+)?{legacy.MONEY_PATTERN}",
        rf"\bdistributed\s+(?:a\s+)?(?:total\s+)?(?:sum\s+of\s+)?{legacy.MONEY_PATTERN}",
        rf"\bbringing\s+the\s+total\s+distributable\s+amount"
        rf"(?:\s+for\s+the\s+month)?\s+to\s+{legacy.MONEY_PATTERN}",
    )
    claims: list[legacy.MoneyClaim] = []
    for pattern in patterns:
        claims.extend(_money_from_match(match) for match in re.finditer(pattern, text, flags=re.I))
    return claims


def _select_body_total(text: str) -> legacy.MoneyClaim:
    claims = _body_total_claims(text)
    if not claims:
        raise NationalEvidenceError(
            "NATIONAL_DISTRIBUTABLE_TOTAL_MISSING",
            "Required distributable-total claim is missing from the official article body",
        )
    anchor = claims[0]
    conflicts = [claim for claim in claims[1:] if _claims_materially_differ(anchor, claim)]
    if conflicts:
        values = [anchor.original, *(claim.original for claim in conflicts)]
        raise NationalEvidenceError(
            "SOURCE_DISTRIBUTABLE_TOTAL_CONFLICT",
            "The official article body reports materially different distributable totals.",
            details={"reported_totals": values},
        )
    return min(claims, key=_claim_quantum_billion)


def _title_total(document: str) -> legacy.MoneyClaim | None:
    title = legacy._article_title(document, "")
    if not title or "faac" not in title.casefold():
        return None
    match = re.search(
        rf"\b(?:share|shared|distributed)\b.{{0,45}}?{legacy.MONEY_PATTERN}",
        title,
        flags=re.I,
    )
    return _money_from_match(match) if match is not None else None


def _derivation_claim(text: str) -> legacy.MoneyClaim:
    for sentence in _sentences(text):
        derivation_at = sentence.casefold().find("derivation")
        if derivation_at < 0:
            continue
        money_matches = list(re.finditer(legacy.MONEY_PATTERN, sentence, flags=re.I))
        if not money_matches:
            continue
        match = min(money_matches, key=lambda item: abs(item.start() - derivation_at))
        return _money_from_match(match)
    raise NationalEvidenceError(
        "NATIONAL_DERIVATION_CLAIM_MISSING",
        "Required 13% derivation claim is missing",
    )


def _validate_magnitude(
    total: legacy.MoneyClaim,
    federal: legacy.MoneyClaim,
    states: legacy.MoneyClaim,
    lgas: legacy.MoneyClaim,
    derivation: legacy.MoneyClaim,
) -> None:
    total_value = _money_value(total)
    components = sum(
        (_money_value(item) for item in (federal, states, lgas, derivation)),
        Decimal(0),
    )
    if total_value <= 0 or components <= 0:
        return
    ratio = max(total_value / components, components / total_value)
    if ratio >= Decimal("100"):
        raise NationalEvidenceError(
            "SOURCE_MONETARY_UNIT_CONFLICT",
            "The official distributable total is orders of magnitude away from the recipient "
            "components; the source monetary unit is internally inconsistent.",
            details={
                "total_billion_naira": str(total_value),
                "component_total_billion_naira": str(components),
                "magnitude_ratio": str(ratio),
            },
        )


def extract_national_claims(document: str) -> legacy.ExtractedNationalClaims:
    """Extract national claims while rejecting headline poisoning and source contradictions."""
    text = legacy._article_text(document)
    allocation_month, disbursement_month = legacy._extract_months(text)
    total = _select_body_total(text)
    title_total = _title_total(document)
    if title_total is not None and _claims_materially_differ(title_total, total):
        raise NationalEvidenceError(
            "SOURCE_DISTRIBUTABLE_TOTAL_CONFLICT",
            "The official page title and article body report materially different "
            "distributable totals.",
            details={
                "title_total": title_total.original,
                "body_total": total.original,
            },
        )

    federal = _recipient_claim(text, r"(?:the\s+)?Federal\s+Government", label="federal")
    states = _recipient_claim(
        text,
        r"(?:the\s+)?(?:State\s+Governments?|States)",
        label="states",
    )
    lgas = _recipient_claim(
        text,
        r"(?:the\s+)?(?:Local\s+Government\s+Councils?|LGCs?)",
        label="local_governments",
    )
    derivation = _derivation_claim(text)
    _validate_magnitude(total, federal, states, lgas, derivation)

    return legacy.ExtractedNationalClaims(
        net_distributable_amount=total,
        federal_amount=federal,
        states_amount=states,
        local_governments_amount=lgas,
        derivation_amount=derivation,
        allocation_period_month=allocation_month,
        disbursement_month=disbursement_month,
    )


def _claim_fingerprint(claims: legacy.ExtractedNationalClaims) -> str:
    payload = {
        "net": claims.net_distributable_amount.normalized_billion,
        "federal": claims.federal_amount.normalized_billion,
        "states": claims.states_amount.normalized_billion,
        "lgas": claims.local_governments_amount.normalized_billion,
        "derivation": claims.derivation_amount.normalized_billion,
        "allocation_period_month": claims.allocation_period_month.isoformat(),
        "disbursement_month": claims.disbursement_month.isoformat(),
        "derivation_treatment": "separate",
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _fingerprint_from_candidate(candidate: NationalEvidenceCandidate) -> str | None:
    details = candidate.details or {}
    fingerprint = details.get("claim_fingerprint")
    if isinstance(fingerprint, str) and len(fingerprint) == 64:
        return fingerprint
    raw = candidate.extracted_claims
    if not isinstance(raw, dict):
        return None
    try:
        payload = {
            "net": raw["net_distributable_amount"]["normalized_billion"],
            "federal": raw["federal_amount"]["normalized_billion"],
            "states": raw["states_amount"]["normalized_billion"],
            "lgas": raw["local_governments_amount"]["normalized_billion"],
            "derivation": raw["derivation_amount"]["normalized_billion"],
            "allocation_period_month": raw["allocation_period_month"],
            "disbursement_month": raw["disbursement_month"],
            "derivation_treatment": raw.get("derivation_treatment", "separate"),
        }
    except (KeyError, TypeError):
        return None
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _candidate_details(
    candidate: NationalEvidenceCandidate,
    claims: legacy.ExtractedNationalClaims,
    **extra: object,
) -> dict[str, object]:
    return {
        **(candidate.details or {}),
        "parser_version": PARSER_VERSION,
        "claim_fingerprint": _claim_fingerprint(claims),
        **extra,
    }


def _equivalent_candidate(
    session: Session,
    *,
    candidate: NationalEvidenceCandidate,
    reporting_period_id: uuid.UUID,
    claims: legacy.ExtractedNationalClaims,
) -> NationalEvidenceCandidate | None:
    fingerprint = _claim_fingerprint(claims)
    others = session.scalars(
        select(NationalEvidenceCandidate).where(
            NationalEvidenceCandidate.id != candidate.id,
            NationalEvidenceCandidate.reporting_period_id == reporting_period_id,
            NationalEvidenceCandidate.status.in_(
                [legacy.STATUS_IMPORTED, legacy.STATUS_DUPLICATE]
            ),
        )
    ).all()
    for other in others:
        if _fingerprint_from_candidate(other) == fingerprint:
            return other
    return None


def _same_url_candidate(
    session: Session,
    *,
    candidate: NationalEvidenceCandidate,
    claims: legacy.ExtractedNationalClaims,
) -> NationalEvidenceCandidate | None:
    others = session.scalars(
        select(NationalEvidenceCandidate).where(
            NationalEvidenceCandidate.id != candidate.id,
            NationalEvidenceCandidate.source_url == candidate.source_url,
            NationalEvidenceCandidate.disbursement_month == claims.disbursement_month,
            NationalEvidenceCandidate.allocation_period_month == claims.allocation_period_month,
        )
    ).all()
    return next(iter(others), None)


def _process_candidate(
    session: Session,
    candidate: NationalEvidenceCandidate,
    claims: legacy.ExtractedNationalClaims,
) -> legacy.QueuedNationalEvidence | None:
    candidate.extracted_claims = claims.as_dict()
    candidate.disbursement_month = claims.disbursement_month
    candidate.allocation_period_month = claims.allocation_period_month
    candidate.details = _candidate_details(candidate, claims)
    legacy._mark(candidate, status=legacy.STATUS_PARSED)

    period, reason = legacy._find_period(session, claims)
    if reason is not None:
        candidate.reporting_period_id = period.id if period is not None else None
        legacy._mark(
            candidate,
            status=legacy.STATUS_DEFERRED,
            reason_code=reason,
            details=_candidate_details(candidate, claims),
        )
        session.commit()
        return None
    assert period is not None
    candidate.reporting_period_id = period.id
    legacy._harden_period_semantics(period, claims)

    same_url = _same_url_candidate(session, candidate=candidate, claims=claims)
    if same_url is not None:
        same_fingerprint = _fingerprint_from_candidate(same_url) == _claim_fingerprint(claims)
        if same_fingerprint:
            legacy._mark(
                candidate,
                status=legacy.STATUS_DUPLICATE,
                reason_code="NATIONAL_URL_PERIOD_ALREADY_RETAINED",
                details=_candidate_details(
                    candidate,
                    claims,
                    duplicate_of_candidate_id=str(same_url.id),
                ),
            )
        else:
            legacy._mark(
                candidate,
                status=legacy.STATUS_QUARANTINED,
                reason_code="NATIONAL_SOURCE_CLAIMS_CHANGED",
                details=_candidate_details(
                    candidate,
                    claims,
                    previous_candidate_id=str(same_url.id),
                ),
            )
        session.commit()
        return None

    equivalent = _equivalent_candidate(
        session,
        candidate=candidate,
        reporting_period_id=period.id,
        claims=claims,
    )
    if equivalent is not None:
        legacy._mark(
            candidate,
            status=legacy.STATUS_DUPLICATE,
            reason_code="NATIONAL_EQUIVALENT_OFFICIAL_MIRROR",
            details=_candidate_details(
                candidate,
                claims,
                duplicate_of_candidate_id=str(equivalent.id),
            ),
        )
        session.commit()
        return None

    existing_source = legacy._existing_source(session, candidate.sha256)
    if existing_source is not None:
        candidate.source_document_id = existing_source.id
        if legacy._source_used_by_states(session, existing_source.id):
            legacy._mark(
                candidate,
                status=legacy.STATUS_QUARANTINED,
                reason_code="SOURCE_REUSED_BY_STATE_ALLOCATION",
                details=_candidate_details(candidate, claims),
            )
            session.commit()
            return None
        distribution = legacy._source_used_nationally(session, existing_source.id)
        if distribution is not None:
            run = session.scalar(
                select(ExtractionRun)
                .where(ExtractionRun.source_document_id == existing_source.id)
                .order_by(ExtractionRun.created_at.desc())
                .limit(1)
            )
            candidate.extraction_run_id = run.id if run is not None else None
            legacy._mark(
                candidate,
                status=legacy.STATUS_DUPLICATE,
                reason_code="NATIONAL_SOURCE_ALREADY_IMPORTED",
                details=_candidate_details(candidate, claims),
            )
            session.commit()
            return None

    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as handle:
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
        raise NationalEvidenceError(
            "NATIONAL_IMPORTED_RUN_MISSING",
            "Imported extraction run could not be reloaded",
        )
    source = session.get(SourceDocument, run.source_document_id)
    if source is None:
        raise NationalEvidenceError(
            "NATIONAL_IMPORTED_SOURCE_MISSING",
            "Imported source document could not be reloaded",
        )
    if source.sha256 != candidate.sha256:
        raise NationalEvidenceError(
            "NATIONAL_SOURCE_FINGERPRINT_MISMATCH",
            "Archived candidate fingerprint differs from imported source",
        )

    source.storage_path = f"db://national-evidence-candidates/{candidate.id}"
    candidate.source_document_id = source.id
    candidate.extraction_run_id = run.id
    legacy._mark(
        candidate,
        status=legacy.STATUS_IMPORTED,
        details=_candidate_details(candidate, claims),
    )
    configuration = dict(run.configuration or {})
    configuration["parser_version"] = PARSER_VERSION
    run.configuration = configuration
    session.commit()
    return legacy.QueuedNationalEvidence(
        candidate_id=str(candidate.id),
        run_id=result.run_id,
        distribution_id=result.distribution_id,
        reporting_period_id=result.reporting_period_id,
        reporting_label=period.reporting_label,
        finding_count=result.finding_count,
        blocking_finding_count=result.blocking_finding_count,
    )


def _archive_candidate(
    session: Session,
    *,
    sync_run: NationalEvidenceSyncRun,
    page: legacy.DiscoveredPage,
    response: legacy.FetchResponse,
    checksum: str,
    title: str,
    publication_date,
) -> NationalEvidenceCandidate:
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
        status=legacy.STATUS_ARCHIVED,
        details={"parser_version": PARSER_VERSION},
    )
    session.add(candidate)
    session.commit()
    return candidate


def run_national_evidence_collection(
    session: Session,
    *,
    months_back: int = 24,
    fetcher: legacy.Fetcher = legacy.http_fetch,
    max_pages: int = legacy.MAX_SEARCH_PAGES,
) -> legacy.NationalCollectionSummary:
    """Collect official national evidence with durable quarantine before any import."""
    threshold = legacy._threshold_month(months_back)
    sync_run = NationalEvidenceSyncRun(
        started_at=datetime.now(UTC),
        status="running",
        options={
            "months_back": months_back,
            "max_pages": max_pages,
            "parser_version": PARSER_VERSION,
        },
        errors=[],
    )
    session.add(sync_run)
    session.commit()

    summary = legacy.NationalCollectionSummary()
    try:
        pages = legacy.discover_official_pages(fetcher=fetcher, max_pages=max_pages)
        sync_run.candidates_discovered = len(pages)
        session.commit()

        for page in pages:
            summary.checked_urls.append(page.url)
            candidate: NationalEvidenceCandidate | None = None
            try:
                response = fetcher(page.url, allowed_host=page.host)
                checksum = hashlib.sha256(response.body).hexdigest()
                candidate = session.scalar(
                    select(NationalEvidenceCandidate).where(
                        NationalEvidenceCandidate.sha256 == checksum
                    )
                )
                document = legacy._decode_html(response)
                title = legacy._article_title(document, page.title)
                publication_date = legacy._publication_date(document)

                if candidate is None:
                    candidate = _archive_candidate(
                        session,
                        sync_run=sync_run,
                        page=page,
                        response=response,
                        checksum=checksum,
                        title=title,
                        publication_date=publication_date,
                    )
                    sync_run = session.get(NationalEvidenceSyncRun, sync_run.id)
                    assert sync_run is not None
                    sync_run.candidates_archived += 1
                    session.commit()
                else:
                    candidate.last_seen_run_id = sync_run.id
                    if candidate.status in TERMINAL_CANDIDATE_STATUSES:
                        summary.duplicates.append(page.url)
                        sync_run.duplicates += 1
                        session.commit()
                        continue

                try:
                    claims = extract_national_claims(document)
                except NationalEvidenceError as error:
                    legacy._mark(
                        candidate,
                        status=legacy.STATUS_QUARANTINED,
                        reason_code=error.reason_code,
                        details={
                            **(candidate.details or {}),
                            "parser_version": PARSER_VERSION,
                            "message": str(error),
                            **error.details,
                        },
                    )
                    summary.quarantined.append(
                        {"url": page.url, "reason": error.reason_code}
                    )
                    sync_run.quarantined += 1
                    session.commit()
                    continue

                candidate.extracted_claims = claims.as_dict()
                candidate.disbursement_month = claims.disbursement_month
                candidate.allocation_period_month = claims.allocation_period_month
                candidate.details = _candidate_details(candidate, claims)
                session.commit()

                if claims.disbursement_month < threshold:
                    continue

                queued = _process_candidate(session, candidate, claims)
                if queued is not None:
                    summary.queued.append(queued)
                    sync_run.imported += 1
                elif candidate.status == legacy.STATUS_DEFERRED:
                    summary.deferred.append(
                        {"url": page.url, "reason": candidate.reason_code or "DEFERRED"}
                    )
                    sync_run.deferred += 1
                elif candidate.status == legacy.STATUS_QUARANTINED:
                    summary.quarantined.append(
                        {"url": page.url, "reason": candidate.reason_code or "QUARANTINED"}
                    )
                    sync_run.quarantined += 1
                elif candidate.status == legacy.STATUS_DUPLICATE:
                    summary.duplicates.append(page.url)
                    sync_run.duplicates += 1
                session.commit()
            except legacy.NationalEvidenceError as error:
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


def _distribution_for_candidate(
    session: Session,
    candidate: NationalEvidenceCandidate,
) -> tuple[ExtractionRun, NationalDistribution, SourceDocument] | None:
    if candidate.extraction_run_id is None:
        return None
    run = session.get(ExtractionRun, candidate.extraction_run_id)
    if run is None:
        return None
    raw_id = (run.configuration or {}).get("distribution_id")
    if raw_id is None:
        return None
    try:
        distribution = session.get(NationalDistribution, uuid.UUID(str(raw_id)))
    except ValueError:
        return None
    if distribution is None:
        return None
    source = session.get(SourceDocument, distribution.source_document_id)
    if source is None:
        return None
    return run, distribution, source


def _has_approval(session: Session, distribution_id: uuid.UUID) -> bool:
    return (
        session.scalar(
            select(AuditLog.id)
            .where(
                AuditLog.action == "national_distribution.approved",
                AuditLog.entity_type == "national_distribution",
                AuditLog.entity_id == distribution_id,
            )
            .limit(1)
        )
        is not None
    )


def _retire_unpublished_packet(
    candidate: NationalEvidenceCandidate,
    run: ExtractionRun,
    distribution: NationalDistribution,
    source: SourceDocument,
    *,
    status: str,
    reason_code: str,
    details: dict[str, object],
) -> None:
    legacy._mark(candidate, status=status, reason_code=reason_code, details=details)
    distribution.verification_status = VerificationStatus.SUPERSEDED
    source.source_status = SourceStatus.SUPERSEDED
    source.processing_status = ProcessingStatus.SUPERSEDED
    run.status = ExtractionStatus.FAILED
    run.completed_at = datetime.now(UTC)


def _as_naira(claim: legacy.MoneyClaim) -> Decimal:
    parsed = parse_money(claim.normalized_billion, ReportedUnit.BILLION_NAIRA)
    if parsed.value is None:
        raise RuntimeError("Hardened national parser produced an empty monetary value")
    return parsed.value


def _repair_candidate(
    session: Session,
    candidate: NationalEvidenceCandidate,
    claims: legacy.ExtractedNationalClaims,
    run: ExtractionRun,
    distribution: NationalDistribution,
) -> None:
    period = session.get(ReportingPeriod, distribution.reporting_period_id)
    if period is None:
        raise NationalEvidenceError(
            "NATIONAL_REPAIR_PERIOD_MISSING",
            "The packet reporting period no longer exists.",
        )
    if claims.disbursement_month != (period.disbursement_month or period.revenue_month):
        raise NationalEvidenceError(
            "NATIONAL_REPAIR_MONTH_CONFLICT",
            "Re-extracted disbursement month conflicts with the governed reporting period.",
        )
    if period.allocation_period_month not in (None, claims.allocation_period_month):
        raise NationalEvidenceError(
            "NATIONAL_REPAIR_MONTH_CONFLICT",
            "Re-extracted allocation period conflicts with the governed reporting period.",
        )

    distribution.net_distributable_amount = _as_naira(claims.net_distributable_amount)
    distribution.federal_amount = _as_naira(claims.federal_amount)
    distribution.states_amount = _as_naira(claims.states_amount)
    distribution.local_governments_amount = _as_naira(claims.local_governments_amount)
    distribution.derivation_amount = _as_naira(claims.derivation_amount)
    distribution.net_amount_original = claims.net_distributable_amount.original

    configuration = dict(run.configuration or {})
    originals = dict(configuration.get("original_values") or {})
    originals.update(
        {
            "net_distributable_amount": claims.net_distributable_amount.original,
            "federal_amount": claims.federal_amount.original,
            "states_amount": claims.states_amount.original,
            "local_governments_amount": claims.local_governments_amount.original,
            "derivation_amount": claims.derivation_amount.original,
        }
    )
    configuration["original_values"] = originals
    configuration["parser_version"] = PARSER_VERSION
    configuration["repaired_by"] = "national_evidence_hardened"
    run.configuration = configuration

    candidate.extracted_claims = claims.as_dict()
    candidate.disbursement_month = claims.disbursement_month
    candidate.allocation_period_month = claims.allocation_period_month
    legacy._mark(
        candidate,
        status=legacy.STATUS_IMPORTED,
        details=_candidate_details(
            candidate,
            claims,
            repaired_at=datetime.now(UTC).isoformat(),
        ),
    )
    validate_national_distribution(session, run)


def _candidate_preference(candidate: NationalEvidenceCandidate) -> tuple[object, ...]:
    source_order = {
        "Federal Ministry of Information and National Orientation": 0,
        "Federal Ministry of Finance": 1,
    }
    return (
        candidate.publication_date is None,
        source_order.get(candidate.source_organization, 99),
        candidate.created_at,
        str(candidate.id),
    )


def _collapse_equivalent_unpublished(
    session: Session,
    candidates: list[NationalEvidenceCandidate],
    summary: NationalRepairSummary,
) -> None:
    groups: dict[tuple[uuid.UUID, str], list[NationalEvidenceCandidate]] = {}
    for candidate in candidates:
        if candidate.reporting_period_id is None or candidate.status != legacy.STATUS_IMPORTED:
            continue
        fingerprint = _fingerprint_from_candidate(candidate)
        if fingerprint is None:
            continue
        packet = _distribution_for_candidate(session, candidate)
        if packet is None:
            continue
        _, distribution, _ = packet
        if distribution.is_published or _has_approval(session, distribution.id):
            continue
        groups.setdefault((candidate.reporting_period_id, fingerprint), []).append(candidate)

    for group in groups.values():
        if len(group) < 2:
            continue
        primary = min(group, key=_candidate_preference)
        for duplicate in group:
            if duplicate.id == primary.id:
                continue
            packet = _distribution_for_candidate(session, duplicate)
            if packet is None:
                continue
            run, distribution, source = packet
            _retire_unpublished_packet(
                duplicate,
                run,
                distribution,
                source,
                status=legacy.STATUS_DUPLICATE,
                reason_code="NATIONAL_EQUIVALENT_OFFICIAL_MIRROR",
                details={
                    **(duplicate.details or {}),
                    "parser_version": PARSER_VERSION,
                    "duplicate_of_candidate_id": str(primary.id),
                },
            )
            summary.duplicates.append(
                {
                    "candidate_id": str(duplicate.id),
                    "duplicate_of": str(primary.id),
                }
            )
    session.commit()


def repair_unpublished_national_evidence(
    session: Session,
    *,
    run_ids: set[uuid.UUID] | None = None,
) -> NationalRepairSummary:
    """Re-extract unapproved unpublished autopilot packets and fail closed on bad sources."""
    summary = NationalRepairSummary()
    candidates = list(
        session.scalars(
            select(NationalEvidenceCandidate)
            .where(NationalEvidenceCandidate.extraction_run_id.is_not(None))
            .order_by(NationalEvidenceCandidate.created_at)
        )
    )
    eligible: list[NationalEvidenceCandidate] = []
    for candidate in candidates:
        packet = _distribution_for_candidate(session, candidate)
        if packet is None:
            continue
        run, distribution, source = packet
        if run_ids is not None and run.id not in run_ids:
            continue
        if distribution.is_published:
            summary.skipped.append(
                {"run_id": str(run.id), "reason": "already_published"}
            )
            continue
        if _has_approval(session, distribution.id):
            summary.skipped.append(
                {"run_id": str(run.id), "reason": "already_approved"}
            )
            continue

        try:
            document = bytes(candidate.content).decode("utf-8", errors="replace")
            claims = extract_national_claims(document)
            _repair_candidate(session, candidate, claims, run, distribution)
            session.commit()
            summary.repaired.append(str(run.id))
            eligible.append(candidate)
        except NationalEvidenceError as error:
            session.rollback()
            candidate = session.get(NationalEvidenceCandidate, candidate.id)
            run = session.get(ExtractionRun, run.id)
            distribution = session.get(NationalDistribution, distribution.id)
            source = session.get(SourceDocument, source.id)
            assert candidate is not None and run is not None
            assert distribution is not None and source is not None
            _retire_unpublished_packet(
                candidate,
                run,
                distribution,
                source,
                status=legacy.STATUS_QUARANTINED,
                reason_code=error.reason_code,
                details={
                    **(candidate.details or {}),
                    "parser_version": PARSER_VERSION,
                    "message": str(error),
                    **error.details,
                },
            )
            session.commit()
            summary.quarantined.append(
                {"run_id": str(run.id), "reason": error.reason_code}
            )

    _collapse_equivalent_unpublished(session, eligible, summary)
    return summary
