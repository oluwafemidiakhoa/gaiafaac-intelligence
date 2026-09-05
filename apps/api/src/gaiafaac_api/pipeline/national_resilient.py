from __future__ import annotations

import argparse
import time
import urllib.error
from datetime import UTC, datetime
from typing import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.config import get_settings
from gaiafaac_api.database.national_evidence_models import NationalEvidenceSyncRun
from gaiafaac_api.database.session import create_database_engine, create_session_factory
from gaiafaac_api.pipeline import national_evidence as legacy
from gaiafaac_api.pipeline.national_evidence_hardened import run_national_evidence_collection
from gaiafaac_api.pipeline.national_notify import send_national_review_alert

RETRY_ATTEMPTS = 3
RETRY_DELAYS_SECONDS = (2.0, 5.0)
RETRYABLE_HTTP_CODES = {408, 425, 429, 500, 502, 503, 504}


def retrying_fetch(
    url: str,
    *,
    allowed_host: str,
    fetcher: legacy.Fetcher = legacy.http_fetch,
    attempts: int = RETRY_ATTEMPTS,
    sleeper: Callable[[float], None] = time.sleep,
) -> legacy.FetchResponse:
    """Retry transient official-source failures without weakening URL allowlisting."""
    if attempts < 1:
        raise ValueError("attempts must be positive")

    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            return fetcher(url, allowed_host=allowed_host)
        except urllib.error.HTTPError as error:
            last_error = error
            if error.code not in RETRYABLE_HTTP_CODES:
                raise
        except (TimeoutError, urllib.error.URLError, OSError) as error:
            last_error = error

        if attempt == attempts:
            assert last_error is not None
            raise last_error
        sleeper(RETRY_DELAYS_SECONDS[min(attempt - 1, len(RETRY_DELAYS_SECONDS) - 1)])

    raise RuntimeError("unreachable retry state")


def _reachable_sources(
    *,
    fetcher: legacy.Fetcher,
    sleeper: Callable[[float], None] = time.sleep,
) -> tuple[
    tuple[legacy.OfficialSource, ...],
    dict[tuple[str, str], legacy.FetchResponse],
    list[dict[str, str]],
]:
    reachable: list[legacy.OfficialSource] = []
    cache: dict[tuple[str, str], legacy.FetchResponse] = {}
    errors: list[dict[str, str]] = []

    for source in legacy.OFFICIAL_SOURCES:
        try:
            response = retrying_fetch(
                source.search_url,
                allowed_host=source.host,
                fetcher=fetcher,
                sleeper=sleeper,
            )
        except Exception as error:  # noqa: BLE001 - outage is recorded and other sources continue
            errors.append(
                {
                    "stage": "source_preflight",
                    "source": source.organization,
                    "host": source.host,
                    "url": source.search_url,
                    "error": str(error),
                }
            )
            continue
        reachable.append(source)
        cache[(source.search_url, source.host)] = response

    if not reachable:
        raise legacy.NationalEvidenceError(
            "All configured official national FAAC sources were unreachable; "
            "the collection pass cannot be treated as complete."
        )
    return tuple(reachable), cache, errors


def run_resilient_national_collection(
    session: Session,
    *,
    months_back: int = 24,
    max_pages: int = legacy.MAX_SEARCH_PAGES,
    fetcher: legacy.Fetcher = legacy.http_fetch,
    sleeper: Callable[[float], None] = time.sleep,
) -> legacy.NationalCollectionSummary:
    """Run the governed collector while isolating transient per-source outages."""
    wrapper_started_at = datetime.now(UTC)
    reachable, cache, source_errors = _reachable_sources(fetcher=fetcher, sleeper=sleeper)
    configured_sources = legacy.OFFICIAL_SOURCES

    def resilient_fetch(url: str, *, allowed_host: str) -> legacy.FetchResponse:
        cached = cache.get((url, allowed_host))
        if cached is not None:
            return cached
        return retrying_fetch(
            url,
            allowed_host=allowed_host,
            fetcher=fetcher,
            sleeper=sleeper,
        )

    try:
        legacy.OFFICIAL_SOURCES = reachable
        summary = run_national_evidence_collection(
            session,
            months_back=months_back,
            fetcher=resilient_fetch,
            max_pages=max_pages,
        )
    finally:
        legacy.OFFICIAL_SOURCES = configured_sources

    if source_errors:
        summary.errors.extend(source_errors)
        sync_run = session.scalar(
            select(NationalEvidenceSyncRun)
            .where(NationalEvidenceSyncRun.started_at >= wrapper_started_at)
            .order_by(NationalEvidenceSyncRun.started_at.desc())
            .limit(1)
        )
        if sync_run is None:
            raise RuntimeError("National evidence sync run was not persisted")
        sync_run.errors = [*sync_run.errors, *source_errors]
        sync_run.status = "completed_with_errors"
        session.commit()

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Collect national FAAC evidence with bounded official-source retries."
    )
    parser.add_argument("--months-back", type=int, default=24)
    parser.add_argument("--max-pages", type=int, default=legacy.MAX_SEARCH_PAGES)
    args = parser.parse_args()

    session_factory = create_session_factory(create_database_engine())
    with session_factory() as session:
        summary = run_resilient_national_collection(
            session,
            months_back=args.months_back,
            max_pages=args.max_pages,
        )

        settings = get_settings()
        queue_url = "https://gaiafaac-web.up.railway.app/review/national"
        for item in summary.queued:
            send_national_review_alert(
                settings,
                reporting_label=item.reporting_label,
                run_id=item.run_id,
                finding_count=item.finding_count,
                blocking_finding_count=item.blocking_finding_count,
                queue_url=queue_url,
            )

    print(
        "National resilient collection complete: "
        f"checked={len(summary.checked_urls)}, "
        f"queued={len(summary.queued)}, "
        f"deferred={len(summary.deferred)}, "
        f"quarantined={len(summary.quarantined)}, "
        f"duplicates={len(summary.duplicates)}, "
        f"errors={len(summary.errors)}."
    )


if __name__ == "__main__":
    main()
