from __future__ import annotations

import argparse
import http.client
import json
import time
import urllib.error
import urllib.request
from dataclasses import asdict
from typing import Callable

from gaiafaac_api.database.session import create_database_engine, create_session_factory
from gaiafaac_api.pipeline.oagf.discovery import (
    MAX_HTML_BYTES,
    DiscoveryError,
    FetchResponse,
    OagfDiscoveryClient,
    USER_AGENT,
    _official_url,
)
from gaiafaac_api.pipeline.oagf.revision_monitor import run_revision_monitor

REQUEST_TIMEOUT_SECONDS = 45
RETRY_ATTEMPTS = 3
RETRY_DELAYS_SECONDS = (2.0, 5.0)
RETRYABLE_HTTP_CODES = {408, 425, 429, 500, 502, 503, 504}


def resilient_http_fetch(
    url: str,
    *,
    maximum_bytes: int = MAX_HTML_BYTES,
    attempts: int = RETRY_ATTEMPTS,
    timeout_seconds: int = REQUEST_TIMEOUT_SECONDS,
    sleeper: Callable[[float], None] = time.sleep,
) -> FetchResponse:
    """Fetch allowlisted OAGF HTML with bounded retries and deterministic backoff."""
    if attempts < 1:
        raise ValueError("attempts must be positive")
    if timeout_seconds < 1:
        raise ValueError("timeout_seconds must be positive")

    safe_url = _official_url(url)
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        request = urllib.request.Request(
            safe_url,
            headers={"User-Agent": USER_AGENT},
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310
                final_url = _official_url(response.geturl())
                body = response.read(maximum_bytes + 1)
                if len(body) > maximum_bytes:
                    raise DiscoveryError(
                        f"OAGF response exceeds {maximum_bytes} bytes: {safe_url}"
                    )
                return FetchResponse(
                    body=body,
                    content_type=response.headers.get_content_type(),
                    final_url=final_url,
                )
        except urllib.error.HTTPError as error:
            last_error = error
            if error.code not in RETRYABLE_HTTP_CODES:
                raise DiscoveryError(f"OAGF returned HTTP {error.code}: {safe_url}") from error
        except (OSError, http.client.HTTPException, urllib.error.URLError) as error:
            last_error = error

        if attempt == attempts:
            reason = getattr(last_error, "reason", last_error)
            raise DiscoveryError(
                f"OAGF request failed after {attempts} attempts: {safe_url}: {reason}"
            ) from last_error
        sleeper(RETRY_DELAYS_SECONDS[min(attempt - 1, len(RETRY_DELAYS_SECONDS) - 1)])

    raise RuntimeError("unreachable retry state")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Detect OAGF FAAC source revisions with bounded network retries; "
            "never publishes."
        )
    )
    parser.add_argument("--months-back", type=int, default=24)
    parser.add_argument("--full-history", action="store_true")
    args = parser.parse_args()

    session_factory = create_session_factory(create_database_engine())
    client = OagfDiscoveryClient(fetcher=resilient_http_fetch)
    with session_factory() as session:
        summary = run_revision_monitor(
            session,
            months_back=None if args.full_history else args.months_back,
            client=client,
        )

    print(json.dumps(asdict(summary), indent=2, sort_keys=True))
    if summary.errors:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
