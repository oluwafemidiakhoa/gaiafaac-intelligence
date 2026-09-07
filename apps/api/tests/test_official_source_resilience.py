from __future__ import annotations

import urllib.error
from io import BytesIO

import pytest

from gaiafaac_api.pipeline import national_evidence as legacy
from gaiafaac_api.pipeline.national_resilient import _reachable_sources, retrying_fetch
from gaiafaac_api.pipeline.oagf.discovery import HUB_URL, DiscoveryError
from gaiafaac_api.pipeline.oagf.resilient_revision_monitor import resilient_http_fetch


def test_national_retrying_fetch_recovers_from_transient_timeouts() -> None:
    calls = 0
    sleeps: list[float] = []
    expected = legacy.FetchResponse(
        body=b"<html>ok</html>",
        content_type="text/html",
        final_url="https://fmino.gov.ng/?s=FAAC",
    )

    def fetcher(url: str, *, allowed_host: str) -> legacy.FetchResponse:
        nonlocal calls
        calls += 1
        assert allowed_host == "fmino.gov.ng"
        if calls < 3:
            raise urllib.error.URLError(TimeoutError("timed out"))
        return expected

    result = retrying_fetch(
        "https://fmino.gov.ng/?s=FAAC",
        allowed_host="fmino.gov.ng",
        fetcher=fetcher,
        sleeper=sleeps.append,
    )

    assert result == expected
    assert calls == 3
    assert sleeps == [2.0, 5.0]


def test_national_preflight_keeps_reachable_source_and_records_outage() -> None:
    def fetcher(url: str, *, allowed_host: str) -> legacy.FetchResponse:
        if allowed_host == "fmino.gov.ng":
            raise urllib.error.URLError(TimeoutError("timed out"))
        return legacy.FetchResponse(
            body=b"<html>finance</html>",
            content_type="text/html",
            final_url=url,
        )

    reachable, cache, errors = _reachable_sources(fetcher=fetcher, sleeper=lambda _delay: None)

    assert [source.host for source in reachable] == ["finance.gov.ng"]
    assert ("https://finance.gov.ng/?s=FAAC", "finance.gov.ng") in cache
    assert len(errors) == 1
    assert errors[0]["host"] == "fmino.gov.ng"
    assert errors[0]["stage"] == "source_preflight"


def test_national_preflight_fails_closed_when_all_sources_are_unreachable() -> None:
    def fetcher(url: str, *, allowed_host: str) -> legacy.FetchResponse:
        raise urllib.error.URLError(TimeoutError(f"{allowed_host} timed out"))

    with pytest.raises(legacy.NationalEvidenceError, match="All configured official"):
        _reachable_sources(fetcher=fetcher, sleeper=lambda _delay: None)


def test_oagf_resilient_fetch_retries_then_succeeds(monkeypatch) -> None:
    calls = 0
    sleeps: list[float] = []

    class Headers:
        def get_content_type(self) -> str:
            return "text/html"

    class Response(BytesIO):
        headers = Headers()

        def geturl(self) -> str:
            return HUB_URL

        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.close()

    def urlopen(request, timeout):
        nonlocal calls
        calls += 1
        assert timeout == 45
        if calls < 3:
            raise urllib.error.URLError(TimeoutError("timed out"))
        return Response(b"<html>ok</html>")

    monkeypatch.setattr(
        "gaiafaac_api.pipeline.oagf.resilient_revision_monitor.urllib.request.urlopen",
        urlopen,
    )

    result = resilient_http_fetch(HUB_URL, sleeper=sleeps.append)

    assert result.body == b"<html>ok</html>"
    assert calls == 3
    assert sleeps == [2.0, 5.0]


def test_oagf_resilient_fetch_remains_fail_closed_after_retries(monkeypatch) -> None:
    calls = 0

    def urlopen(request, timeout):
        nonlocal calls
        calls += 1
        raise urllib.error.URLError(TimeoutError("timed out"))

    monkeypatch.setattr(
        "gaiafaac_api.pipeline.oagf.resilient_revision_monitor.urllib.request.urlopen",
        urlopen,
    )

    with pytest.raises(DiscoveryError, match="failed after 3 attempts"):
        resilient_http_fetch(HUB_URL, sleeper=lambda _delay: None)

    assert calls == 3
