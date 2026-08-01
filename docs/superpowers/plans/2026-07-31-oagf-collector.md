# OAGF Automated Collector Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a daily, idempotent, fail-closed collector that fetches new OAGF FAAC PDFs, runs the existing import + validation, queues them for human review, and emails an alert — never publishing.

**Architecture:** A new `gaiafaac_api.pipeline.collection` package (URL builder, HTTP downloader, runner, Zoho notifier), a `collect-oagf` CLI command, a read-only `/api/v1/review/pending` endpoint + web page, and a Railway cron service. The runner reuses `import_file` and structurally omits any publish function.

**Tech Stack:** Python 3.12, SQLAlchemy 2, FastAPI, Pydantic v2, argparse, stdlib `urllib`/`smtplib`/`email` (no new runtime dependencies); Next.js 16 + Zod on the web; Railway cron for scheduling.

## Global Constraints

- Python **3.12+**; **no new runtime dependencies** — use stdlib `urllib.request`, `smtplib`, `email.message`.
- The `collection` package **must never import** `approve_import` or `publish_import`. A test asserts their absence.
- Money stays `Decimal`; the collector touches no monetary parsing (delegated to `import_file`).
- New Python files live under `apps/api/src/gaiafaac_api/pipeline/collection/`; tests under `apps/api/tests/`.
- Tests run on the SQLite in-memory `session` fixture (`apps/api/tests/conftest.py`); any test that imports data must call `seed_states(session)` first.
- Lint: `ruff format` + `ruff check` (rules E,F,I,UP,B,SIM), `--max-warnings=0` equivalents must pass.
- OAGF constant org string, used verbatim everywhere: `Office of the Accountant-General of the Federation (OAGF)`.
- Default reported unit for OAGF PDFs: `naira`.
- Public review-queue URL (for email + nav): `https://gaiafaac-api-production.up.railway.app/review/pending` (web page served by the site; the API endpoint is `/api/v1/review/pending`).

---

### Task 1: OAGF URL builder

**Files:**

- Create: `apps/api/src/gaiafaac_api/pipeline/collection/__init__.py` (empty)
- Create: `apps/api/src/gaiafaac_api/pipeline/collection/oagf_urls.py`
- Test: `apps/api/tests/test_collection_urls.py`

**Interfaces:**

- Produces: `candidate_urls(revenue_year: int, revenue_month: int) -> list[str]` — OAGF PDF URLs to try, most-likely first.

- [ ] **Step 1: Write the failing test**

```python
# apps/api/tests/test_collection_urls.py
from gaiafaac_api.pipeline.collection.oagf_urls import candidate_urls


def test_january_2024_matches_verified_real_url():
    urls = candidate_urls(2024, 1)
    assert urls[0] == (
        "https://oagf.gov.ng/wp-content/uploads/2024/02/Disbursement-January-2024.pdf"
    )
    # fallback tries the following publication month too
    assert urls[1] == (
        "https://oagf.gov.ng/wp-content/uploads/2024/03/Disbursement-January-2024.pdf"
    )


def test_december_rolls_publication_year_forward():
    urls = candidate_urls(2024, 12)
    assert urls[0] == (
        "https://oagf.gov.ng/wp-content/uploads/2025/01/Disbursement-December-2024.pdf"
    )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest apps/api/tests/test_collection_urls.py -v`
Expected: FAIL with `ModuleNotFoundError` / `candidate_urls` not defined.

- [ ] **Step 3: Write minimal implementation**

```python
# apps/api/src/gaiafaac_api/pipeline/collection/oagf_urls.py
from __future__ import annotations

import calendar

_BASE = "https://oagf.gov.ng/wp-content/uploads"


def _add_months(year: int, month: int, delta: int) -> tuple[int, int]:
    index = (year * 12 + (month - 1)) + delta
    return index // 12, index % 12 + 1


def candidate_urls(revenue_year: int, revenue_month: int) -> list[str]:
    """OAGF PDF URLs for a revenue month, most-likely publication folder first.

    The filename carries the revenue month name + revenue year; the upload folder
    is the publication month (revenue month + 1, with +2 as a slippage fallback).
    """
    month_name = calendar.month_name[revenue_month]
    filename = f"Disbursement-{month_name}-{revenue_year}.pdf"
    urls: list[str] = []
    for slip in (1, 2):
        pub_year, pub_month = _add_months(revenue_year, revenue_month, slip)
        urls.append(f"{_BASE}/{pub_year}/{pub_month:02d}/{filename}")
    return urls
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest apps/api/tests/test_collection_urls.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add apps/api/src/gaiafaac_api/pipeline/collection/__init__.py \
        apps/api/src/gaiafaac_api/pipeline/collection/oagf_urls.py \
        apps/api/tests/test_collection_urls.py
git commit -m "feat(collection): OAGF revenue-month -> candidate PDF URLs"
```

---

### Task 2: HTTP downloader

**Files:**

- Create: `apps/api/src/gaiafaac_api/pipeline/collection/downloader.py`
- Test: `apps/api/tests/test_collection_downloader.py`

**Interfaces:**

- Produces:
  - `Fetch = Callable[[str], bytes | None]` (returns raw bytes, or `None` on HTTP 404).
  - `http_download(url: str, *, dest_dir: Path = Path("data/raw"), fetch: Fetch = _urlopen_bytes) -> Path | None` — saves a real PDF, returns its path; returns `None` for 404 or non-PDF content.

- [ ] **Step 1: Write the failing test**

```python
# apps/api/tests/test_collection_downloader.py
from pathlib import Path

from gaiafaac_api.pipeline.collection.downloader import http_download

URL = "https://oagf.gov.ng/wp-content/uploads/2024/02/Disbursement-January-2024.pdf"


def test_saves_pdf_bytes(tmp_path: Path):
    path = http_download(URL, dest_dir=tmp_path, fetch=lambda _u: b"%PDF-1.7 fake body")
    assert path is not None
    assert path.exists()
    assert path.read_bytes().startswith(b"%PDF")
    assert path.name == "Disbursement-January-2024.pdf"


def test_returns_none_on_404(tmp_path: Path):
    assert http_download(URL, dest_dir=tmp_path, fetch=lambda _u: None) is None


def test_rejects_non_pdf(tmp_path: Path):
    assert http_download(URL, dest_dir=tmp_path, fetch=lambda _u: b"<html>nope</html>") is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest apps/api/tests/test_collection_downloader.py -v`
Expected: FAIL (module/function not defined).

- [ ] **Step 3: Write minimal implementation**

```python
# apps/api/src/gaiafaac_api/pipeline/collection/downloader.py
from __future__ import annotations

import logging
import urllib.error
import urllib.request
from collections.abc import Callable
from pathlib import Path

logger = logging.getLogger(__name__)
MAX_DOWNLOAD_BYTES = 30 * 1024 * 1024
Fetch = Callable[[str], bytes | None]


def _urlopen_bytes(url: str) -> bytes | None:
    request = urllib.request.Request(  # noqa: S310 - fixed https OAGF host
        url, headers={"User-Agent": "GaiaFAAC-collector/1.0 (research)"}
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as response:  # noqa: S310
            return response.read(MAX_DOWNLOAD_BYTES + 1)
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return None
        raise


def http_download(
    url: str, *, dest_dir: Path = Path("data/raw"), fetch: Fetch = _urlopen_bytes
) -> Path | None:
    """Download a URL to dest_dir if it is a real (non-empty, in-limit) PDF."""
    data = fetch(url)
    if data is None:
        logger.info("Not published yet (404): %s", url)
        return None
    if not data.startswith(b"%PDF"):
        logger.warning("Ignoring non-PDF response from %s", url)
        return None
    if len(data) > MAX_DOWNLOAD_BYTES:
        logger.warning("Ignoring oversized response from %s", url)
        return None
    dest_dir.mkdir(parents=True, exist_ok=True)
    destination = dest_dir / url.rsplit("/", 1)[-1]
    destination.write_bytes(data)
    return destination
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest apps/api/tests/test_collection_downloader.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add apps/api/src/gaiafaac_api/pipeline/collection/downloader.py \
        apps/api/tests/test_collection_downloader.py
git commit -m "feat(collection): PDF-validating HTTP downloader with 404 handling"
```

---

### Task 3: Collector runner

**Files:**

- Create: `apps/api/src/gaiafaac_api/pipeline/collection/collector.py`
- Test: `apps/api/tests/test_collector.py`

**Interfaces:**

- Consumes: `candidate_urls` (Task 1); `import_file` + `ImportRequest`/`ImportResult` from existing pipeline.
- Produces:
  - `QueuedMonth` (frozen dataclass): `run_id: str`, `revenue_month: date`, `reporting_label: str`, `records_extracted: int`, `blocking_finding_count: int`.
  - `CollectionSummary` (frozen dataclass): `checked: list[date]`, `queued: list[QueuedMonth]`, `skipped: list[date]`, `errors: list[tuple[date, str]]`.
  - `run_collection(session, *, months_back: int = 3, downloader: Callable[[str], Path | None], importer=import_file, now: date | None = None) -> CollectionSummary`.

- [ ] **Step 1: Write the failing test**

```python
# apps/api/tests/test_collector.py
from datetime import date
from pathlib import Path

from sqlalchemy import select

from gaiafaac_api.database.models import ReportingPeriod
from gaiafaac_api.database.seeds import seed_states
from gaiafaac_api.pipeline.collection import collector as collector_module
from gaiafaac_api.pipeline.collection.collector import QueuedMonth, run_collection
from gaiafaac_api.pipeline.importer import ImportResult


def _fake_importer_factory(session):
    """Importer stub that records a real (non-demo) requires_review period."""

    def _fake_importer(sess, request):
        period = ReportingPeriod(
            revenue_month=request.revenue_month,
            reporting_label=request.reporting_label,
            is_demo=False,
            is_published=False,
        )
        sess.add(period)
        sess.flush()
        return ImportResult(
            run_id=str(period.id),
            reporting_period_id=str(period.id),
            source_document_id=str(period.id),
            records_extracted=36,
            finding_count=2,
            blocking_finding_count=2,
        )

    return _fake_importer


def test_collects_available_month_and_never_publishes(session, tmp_path):
    seed_states(session)
    pdf = tmp_path / "x.pdf"
    pdf.write_bytes(b"%PDF-1.7 x")

    summary = run_collection(
        session,
        months_back=1,
        downloader=lambda _url: pdf,
        importer=_fake_importer_factory(session),
        now=date(2024, 2, 15),
    )

    assert summary.queued == [
        QueuedMonth(
            run_id=summary.queued[0].run_id,
            revenue_month=date(2024, 1, 1),
            reporting_label=summary.queued[0].reporting_label,
            records_extracted=36,
            blocking_finding_count=2,
        )
    ]
    # nothing is ever published
    assert session.scalars(
        select(ReportingPeriod).where(ReportingPeriod.is_published.is_(True))
    ).all() == []


def test_is_idempotent(session, tmp_path):
    seed_states(session)
    pdf = tmp_path / "x.pdf"
    pdf.write_bytes(b"%PDF-1.7 x")
    kwargs = dict(
        months_back=1,
        downloader=lambda _url: pdf,
        importer=_fake_importer_factory(session),
        now=date(2024, 2, 15),
    )
    run_collection(session, **kwargs)
    second = run_collection(session, **kwargs)
    assert second.queued == []
    assert second.skipped == [date(2024, 1, 1)]


def test_missing_month_is_skipped(session, tmp_path):
    seed_states(session)
    summary = run_collection(
        session,
        months_back=1,
        downloader=lambda _url: None,  # 404 everywhere
        importer=_fake_importer_factory(session),
        now=date(2024, 2, 15),
    )
    assert summary.queued == []
    assert summary.skipped == [date(2024, 1, 1)]


def test_collector_cannot_publish():
    source = Path(collector_module.__file__).read_text(encoding="utf-8")
    assert "publish_import" not in source
    assert "approve_import" not in source
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest apps/api/tests/test_collector.py -v`
Expected: FAIL (module/symbols not defined).

- [ ] **Step 3: Write minimal implementation**

```python
# apps/api/src/gaiafaac_api/pipeline/collection/collector.py
from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from gaiafaac_api.database.models import ReportingPeriod
from gaiafaac_api.pipeline.collection.oagf_urls import candidate_urls
from gaiafaac_api.pipeline.extraction.file_import import import_file
from gaiafaac_api.pipeline.importer import ImportRequest, ImportResult

logger = logging.getLogger(__name__)

OAGF_ORG = "Office of the Accountant-General of the Federation (OAGF)"
Downloader = Callable[[str], Path | None]
Importer = Callable[[Session, ImportRequest], ImportResult]


@dataclass(frozen=True)
class QueuedMonth:
    run_id: str
    revenue_month: date
    reporting_label: str
    records_extracted: int
    blocking_finding_count: int


@dataclass(frozen=True)
class CollectionSummary:
    checked: list[date]
    queued: list[QueuedMonth]
    skipped: list[date]
    errors: list[tuple[date, str]]


def _reporting_label(revenue: date) -> str:
    return (
        f"OAGF FAAC Disbursement — {revenue.strftime('%B %Y')} "
        "(Table III: state distribution)"
    )


def _add_months(anchor: date, delta: int) -> date:
    index = (anchor.year * 12 + (anchor.month - 1)) + delta
    return date(index // 12, index % 12 + 1, 1)


def _already_ingested(session: Session, revenue: date) -> bool:
    return session.scalar(
        select(ReportingPeriod).where(
            ReportingPeriod.revenue_month == revenue,
            ReportingPeriod.is_demo.is_(False),
        )
    ) is not None


def run_collection(
    session: Session,
    *,
    months_back: int = 3,
    downloader: Downloader,
    importer: Importer = import_file,
    now: date | None = None,
) -> CollectionSummary:
    """Fetch, import, and queue any newly published OAGF months. Never publishes."""
    anchor = now or date.today()
    checked: list[date] = []
    queued: list[QueuedMonth] = []
    skipped: list[date] = []
    errors: list[tuple[date, str]] = []

    for step in range(1, months_back + 1):
        revenue = _add_months(anchor.replace(day=1), -step)
        checked.append(revenue)
        if _already_ingested(session, revenue):
            skipped.append(revenue)
            continue

        path: Path | None = None
        source_url: str | None = None
        failed = False
        for url in candidate_urls(revenue.year, revenue.month):
            try:
                path = downloader(url)
            except Exception as error:  # noqa: BLE001 - one bad month must not abort the run
                errors.append((revenue, f"download failed: {error}"))
                failed = True
                break
            if path is not None:
                source_url = url
                break
        if failed:
            continue
        if path is None:
            skipped.append(revenue)
            continue

        try:
            result = importer(
                session,
                ImportRequest(
                    path=path,
                    source_organization=OAGF_ORG,
                    revenue_month=revenue,
                    reporting_label=_reporting_label(revenue),
                    source_url=source_url,
                    reported_unit="naira",
                ),
            )
        except Exception as error:  # noqa: BLE001 - surface, don't abort the whole run
            errors.append((revenue, f"import failed: {error}"))
            continue

        queued.append(
            QueuedMonth(
                run_id=result.run_id,
                revenue_month=revenue,
                reporting_label=_reporting_label(revenue),
                records_extracted=result.records_extracted,
                blocking_finding_count=result.blocking_finding_count,
            )
        )
        logger.info("Queued %s (run=%s) for review", _reporting_label(revenue), result.run_id)

    return CollectionSummary(checked, queued, skipped, errors)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest apps/api/tests/test_collector.py -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add apps/api/src/gaiafaac_api/pipeline/collection/collector.py \
        apps/api/tests/test_collector.py
git commit -m "feat(collection): idempotent, never-publishing OAGF collector runner"
```

---

### Task 4: Config settings + Zoho email notifier

**Files:**

- Modify: `apps/api/src/gaiafaac_api/config.py` (add SMTP settings)
- Create: `apps/api/src/gaiafaac_api/pipeline/collection/notify.py`
- Test: `apps/api/tests/test_collection_notify.py`

**Interfaces:**

- Consumes: `Settings` fields `smtp_host, smtp_port, smtp_username, smtp_password, alert_from, alert_to`.
- Produces: `send_review_alert(settings, *, reporting_label: str, records_extracted: int, blocking_finding_count: int, queue_url: str) -> bool` — sends via Zoho SMTP; returns `False` (never raises) if unconfigured or on any SMTP error.

- [ ] **Step 1: Write the failing test**

```python
# apps/api/tests/test_collection_notify.py
import smtplib

import pytest

from gaiafaac_api.config import Settings
from gaiafaac_api.pipeline.collection.notify import send_review_alert


def _settings(**over):
    base = dict(
        smtp_host="smtp.zoho.com",
        smtp_port=465,
        smtp_username="alerts@example.com",
        smtp_password="app-pw",
        alert_from="alerts@example.com",
        alert_to="me@example.com",
    )
    base.update(over)
    return Settings(**base)


class _FakeSMTP:
    sent = []

    def __init__(self, host, port):
        self.host = host

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def login(self, user, password):
        pass

    def send_message(self, message):
        _FakeSMTP.sent.append(message)


def test_sends_when_configured(monkeypatch):
    _FakeSMTP.sent = []
    monkeypatch.setattr(smtplib, "SMTP_SSL", _FakeSMTP)
    ok = send_review_alert(
        _settings(),
        reporting_label="OAGF Jan 2024",
        records_extracted=36,
        blocking_finding_count=2,
        queue_url="https://x/review/pending",
    )
    assert ok is True
    assert "OAGF Jan 2024" in _FakeSMTP.sent[0]["Subject"]


def test_skips_when_unconfigured(monkeypatch):
    def _boom(*a, **k):
        raise AssertionError("must not connect")

    monkeypatch.setattr(smtplib, "SMTP_SSL", _boom)
    assert (
        send_review_alert(
            _settings(smtp_password=""),
            reporting_label="X",
            records_extracted=1,
            blocking_finding_count=0,
            queue_url="https://x",
        )
        is False
    )


def test_swallows_smtp_errors(monkeypatch):
    class _Broken(_FakeSMTP):
        def login(self, user, password):
            raise smtplib.SMTPAuthenticationError(535, b"bad")

    monkeypatch.setattr(smtplib, "SMTP_SSL", _Broken)
    assert (
        send_review_alert(
            _settings(),
            reporting_label="X",
            records_extracted=1,
            blocking_finding_count=0,
            queue_url="https://x",
        )
        is False
    )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest apps/api/tests/test_collection_notify.py -v`
Expected: FAIL (settings fields / function missing).

- [ ] **Step 3a: Add SMTP settings to `config.py`**

Insert into `Settings` (after the `database_url` field, before the `_default_when_blank` validator):

```python
    smtp_host: str = ""
    smtp_port: int = 465
    smtp_username: str = ""
    smtp_password: str = ""
    alert_from: str = ""
    alert_to: str = ""
```

- [ ] **Step 3b: Write the notifier**

```python
# apps/api/src/gaiafaac_api/pipeline/collection/notify.py
from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

logger = logging.getLogger(__name__)


def send_review_alert(
    settings,
    *,
    reporting_label: str,
    records_extracted: int,
    blocking_finding_count: int,
    queue_url: str,
) -> bool:
    """Email an alert that a month is queued for review. Never raises."""
    if not all(
        [
            settings.smtp_host,
            settings.smtp_username,
            settings.smtp_password,
            settings.alert_from,
            settings.alert_to,
        ]
    ):
        logger.info("SMTP not configured; skipping alert for %s", reporting_label)
        return False

    message = EmailMessage()
    message["Subject"] = f"New OAGF month ready for review — {reporting_label}"
    message["From"] = settings.alert_from
    message["To"] = settings.alert_to
    message.set_content(
        f"{reporting_label}\n\n"
        f"Records extracted: {records_extracted}\n"
        f"Blocking findings: {blocking_finding_count}\n"
        f"Status: requires_review (nothing is published automatically)\n\n"
        f"Review and approve: {queue_url}\n"
    )
    try:
        with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port) as server:
            server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(message)
        return True
    except Exception as error:  # noqa: BLE001 - a failed email must not break collection
        logger.warning("Review alert email failed for %s: %s", reporting_label, error)
        return False
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest apps/api/tests/test_collection_notify.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add apps/api/src/gaiafaac_api/config.py \
        apps/api/src/gaiafaac_api/pipeline/collection/notify.py \
        apps/api/tests/test_collection_notify.py
git commit -m "feat(collection): Zoho SMTP review-alert notifier + settings"
```

---

### Task 5: `collect-oagf` CLI command

**Files:**

- Modify: `apps/api/src/gaiafaac_api/cli.py`
- Test: `apps/api/tests/test_cli_collect.py`

**Interfaces:**

- Consumes: `run_collection`, `http_download`, `candidate_urls`, `send_review_alert`, `get_settings`.
- Produces: `collect-oagf` subcommand with `--months-back N` (default 3) and `--dry-run`.

- [ ] **Step 1: Write the failing test**

```python
# apps/api/tests/test_cli_collect.py
from gaiafaac_api.cli import build_parser


def test_collect_oagf_defaults():
    args = build_parser().parse_args(["collect-oagf"])
    assert args.command == "collect-oagf"
    assert args.months_back == 3
    assert args.dry_run is False


def test_collect_oagf_flags():
    args = build_parser().parse_args(["collect-oagf", "--months-back", "6", "--dry-run"])
    assert args.months_back == 6
    assert args.dry_run is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest apps/api/tests/test_cli_collect.py -v`
Expected: FAIL (`invalid choice: 'collect-oagf'`).

- [ ] **Step 3a: Register the subparser** (in `build_parser`, before `return parser`)

```python
    collect = commands.add_parser(
        "collect-oagf", help="Fetch, import and queue new OAGF months (never publishes)"
    )
    collect.add_argument("--months-back", type=int, default=3)
    collect.add_argument("--dry-run", action="store_true")
```

- [ ] **Step 3b: Add the dispatch branch** (in `main`, as a new `elif`)

```python
        elif args.command == "collect-oagf":
            from gaiafaac_api.config import get_settings
            from gaiafaac_api.pipeline.collection.collector import run_collection
            from gaiafaac_api.pipeline.collection.downloader import http_download
            from gaiafaac_api.pipeline.collection.notify import send_review_alert
            from gaiafaac_api.pipeline.collection.oagf_urls import candidate_urls

            if args.dry_run:
                from datetime import date

                anchor = date.today().replace(day=1)
                for step in range(1, args.months_back + 1):
                    idx = (anchor.year * 12 + anchor.month - 1) - step
                    revenue = date(idx // 12, idx % 12 + 1, 1)
                    print(f"{revenue:%B %Y}: {candidate_urls(revenue.year, revenue.month)}")
                return

            summary = run_collection(
                session, months_back=args.months_back, downloader=http_download
            )
            settings = get_settings()
            queue_url = "https://gaiafaac-api-production.up.railway.app/review/pending"
            for month in summary.queued:
                send_review_alert(
                    settings,
                    reporting_label=month.reporting_label,
                    records_extracted=month.records_extracted,
                    blocking_finding_count=month.blocking_finding_count,
                    queue_url=queue_url,
                )
            print(
                f"Collection complete: checked={len(summary.checked)}, "
                f"queued={len(summary.queued)}, skipped={len(summary.skipped)}, "
                f"errors={len(summary.errors)}."
            )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest apps/api/tests/test_cli_collect.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add apps/api/src/gaiafaac_api/cli.py apps/api/tests/test_cli_collect.py
git commit -m "feat(cli): collect-oagf command with dry-run and email alerts"
```

---

### Task 6: Review-queue service + schema

**Files:**

- Create: `apps/api/src/gaiafaac_api/review_schemas.py`
- Create: `apps/api/src/gaiafaac_api/services/review_queue.py`
- Test: `apps/api/tests/test_review_queue.py`

**Interfaces:**

- Produces:
  - `PendingReviewItem` (Pydantic): `run_id, reporting_label, revenue_month, source_organization, status, covered_states, expected_states, finding_count, blocking_count, created_at`.
  - `list_pending_reviews(session) -> list[PendingReviewItem]` — real, unpublished periods only; **no allocation figures**.

- [ ] **Step 1: Write the failing test**

```python
# apps/api/tests/test_review_queue.py
import csv
from datetime import date
from pathlib import Path

from gaiafaac_api.database.seeds import seed_states
from gaiafaac_api.pipeline.extraction.file_import import import_file
from gaiafaac_api.pipeline.importer import ImportRequest
from gaiafaac_api.services.review_queue import list_pending_reviews


def _write_csv(path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["state", "gross_total", "total_deductions", "net_allocation", "reported_unit"])
        writer.writerow(["Lagos", "1000.00", "100.00", "900.00", "naira"])
        writer.writerow(["Kano", "2000.00", "200.00", "1800.00", "naira"])


def _import(session, path, *, label, is_demo=False):
    return import_file(
        session,
        ImportRequest(
            path=path,
            source_organization="OAGF",
            revenue_month=date(2024, 1, 1),
            reporting_label=label,
            reported_unit="naira",
            is_demo=is_demo,
        ),
    )


def test_lists_pending_real_period_metadata_only(session, tmp_path):
    seed_states(session)
    csv_path = tmp_path / "jan.csv"
    _write_csv(csv_path)
    _import(session, csv_path, label="OAGF Jan 2024")

    items = list_pending_reviews(session)
    assert len(items) == 1
    item = items[0]
    assert item.reporting_label == "OAGF Jan 2024"
    assert item.expected_states == 37
    assert item.covered_states == 2
    assert item.blocking_count >= 1  # MISSING_STATES
    # metadata only — no figures leak through the schema
    assert not hasattr(item, "allocations")
    assert "900" not in item.model_dump_json()


def test_excludes_demo_and_published(session, tmp_path):
    seed_states(session)
    demo_csv = tmp_path / "demo.csv"
    _write_csv(demo_csv)
    _import(session, demo_csv, label="DEMO period", is_demo=True)
    assert list_pending_reviews(session) == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest apps/api/tests/test_review_queue.py -v`
Expected: FAIL (module/symbols missing).

- [ ] **Step 3a: Write the schema**

```python
# apps/api/src/gaiafaac_api/review_schemas.py
from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel


class PendingReviewItem(BaseModel):
    run_id: str
    reporting_label: str
    revenue_month: date
    source_organization: str
    status: str
    covered_states: int
    expected_states: int
    finding_count: int
    blocking_count: int
    created_at: datetime | None
```

- [ ] **Step 3b: Write the service**

```python
# apps/api/src/gaiafaac_api/services/review_queue.py
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from gaiafaac_api.database.enums import ValidationSeverity
from gaiafaac_api.database.models import (
    ExtractionRun,
    ReportingPeriod,
    SourceDocument,
    StateAllocation,
    ValidationResult,
)
from gaiafaac_api.review_schemas import PendingReviewItem

EXPECTED_STATE_COUNT = 37
_BLOCKING = {ValidationSeverity.ERROR, ValidationSeverity.CRITICAL}


def list_pending_reviews(session: Session) -> list[PendingReviewItem]:
    """Real (non-demo), unpublished periods awaiting human review. Metadata only."""
    periods = session.scalars(
        select(ReportingPeriod)
        .where(
            ReportingPeriod.is_demo.is_(False),
            ReportingPeriod.is_published.is_(False),
        )
        .order_by(ReportingPeriod.revenue_month.desc())
    )
    items: list[PendingReviewItem] = []
    for period in periods:
        source = session.scalar(
            select(SourceDocument).where(SourceDocument.reporting_period_id == period.id)
        )
        if source is None:
            continue
        run = session.scalar(
            select(ExtractionRun)
            .where(ExtractionRun.source_document_id == source.id)
            .order_by(ExtractionRun.started_at.desc())
        )
        covered = (
            session.scalar(
                select(func.count())
                .select_from(StateAllocation)
                .where(
                    StateAllocation.reporting_period_id == period.id,
                    StateAllocation.is_demo.is_(False),
                )
            )
            or 0
        )
        findings = (
            list(
                session.scalars(
                    select(ValidationResult).where(
                        ValidationResult.extraction_run_id == run.id
                    )
                )
            )
            if run is not None
            else []
        )
        blocking = sum(finding.severity in _BLOCKING for finding in findings)
        items.append(
            PendingReviewItem(
                run_id=str(run.id) if run is not None else "",
                reporting_label=period.reporting_label,
                revenue_month=period.revenue_month,
                source_organization=source.source_organization,
                status=run.status.value if run is not None else "unknown",
                covered_states=covered,
                expected_states=EXPECTED_STATE_COUNT,
                finding_count=len(findings),
                blocking_count=blocking,
                created_at=run.started_at if run is not None else None,
            )
        )
    return items
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest apps/api/tests/test_review_queue.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add apps/api/src/gaiafaac_api/review_schemas.py \
        apps/api/src/gaiafaac_api/services/review_queue.py \
        apps/api/tests/test_review_queue.py
git commit -m "feat(review): pending-review queue service (metadata only)"
```

---

### Task 7: Review-queue API endpoint

**Files:**

- Create: `apps/api/src/gaiafaac_api/api/v1/routes/review.py`
- Modify: `apps/api/src/gaiafaac_api/api/v1/router.py`
- Test: `apps/api/tests/test_review_endpoint.py`

**Interfaces:**

- Consumes: `list_pending_reviews`, `PendingReviewItem`, `get_session`.
- Produces: `GET /api/v1/review/pending -> list[PendingReviewItem]`.

- [ ] **Step 1: Write the failing test**

```python
# apps/api/tests/test_review_endpoint.py
import csv
from datetime import date
from pathlib import Path

from fastapi.testclient import TestClient

from gaiafaac_api.database.seeds import seed_states
from gaiafaac_api.database.session import get_session
from gaiafaac_api.main import app
from gaiafaac_api.pipeline.extraction.file_import import import_file
from gaiafaac_api.pipeline.importer import ImportRequest


def test_pending_endpoint_returns_queued_month(session, tmp_path):
    seed_states(session)
    csv_path = tmp_path / "jan.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["state", "gross_total", "total_deductions", "net_allocation", "reported_unit"])
        writer.writerow(["Lagos", "1000.00", "100.00", "900.00", "naira"])
    import_file(
        session,
        ImportRequest(
            path=csv_path,
            source_organization="OAGF",
            revenue_month=date(2024, 1, 1),
            reporting_label="OAGF Jan 2024",
            reported_unit="naira",
        ),
    )

    app.dependency_overrides[get_session] = lambda: session
    try:
        client = TestClient(app)
        response = client.get("/api/v1/review/pending")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["reporting_label"] == "OAGF Jan 2024"
    assert body[0]["expected_states"] == 37
    assert "900" not in response.text  # no figures
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest apps/api/tests/test_review_endpoint.py -v`
Expected: FAIL (404 — route not registered).

- [ ] **Step 3a: Write the route**

```python
# apps/api/src/gaiafaac_api/api/v1/routes/review.py
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from gaiafaac_api.database.session import get_session
from gaiafaac_api.review_schemas import PendingReviewItem
from gaiafaac_api.services.review_queue import list_pending_reviews

router = APIRouter(prefix="/review", tags=["review queue"])
DatabaseSession = Annotated[Session, Depends(get_session)]


@router.get(
    "/pending",
    response_model=list[PendingReviewItem],
    summary="Real months awaiting human review (metadata only, no figures)",
)
def pending_reviews(session: DatabaseSession) -> list[PendingReviewItem]:
    return list_pending_reviews(session)
```

- [ ] **Step 3b: Register it in `router.py`**

```python
from gaiafaac_api.api.v1.routes.review import router as review_router
# ...
router.include_router(review_router)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest apps/api/tests/test_review_endpoint.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/api/src/gaiafaac_api/api/v1/routes/review.py \
        apps/api/src/gaiafaac_api/api/v1/router.py \
        apps/api/tests/test_review_endpoint.py
git commit -m "feat(api): GET /api/v1/review/pending endpoint"
```

---

### Task 8: Frontend "Pending review" page

**Files:**

- Create: `apps/web/src/lib/review-api.ts`
- Create: `apps/web/src/app/review/pending/page.tsx`
- Modify: `apps/web/src/components/site-header.tsx` (add nav link)
- Test: `apps/web/src/lib/review-api.test.ts`

**Interfaces:**

- Consumes: `GET /api/v1/review/pending`.
- Produces: `getPendingReviews(): Promise<ApiResult<PendingReviewItem[]>>` mirroring `published-api.ts`.

- [ ] **Step 1: Write the failing test**

```typescript
// apps/web/src/lib/review-api.test.ts
import { describe, expect, it } from 'vitest'
import { pendingReviewSchema } from './review-api'

describe('pendingReviewSchema', () => {
  it('parses a valid pending item', () => {
    const parsed = pendingReviewSchema.parse({
      run_id: 'r1',
      reporting_label: 'OAGF Jan 2024',
      revenue_month: '2024-01-01',
      source_organization: 'OAGF',
      status: 'requires_review',
      covered_states: 36,
      expected_states: 37,
      finding_count: 2,
      blocking_count: 2,
      created_at: '2026-07-31T00:00:00Z',
    })
    expect(parsed.reporting_label).toBe('OAGF Jan 2024')
  })

  it('rejects an item missing coverage', () => {
    expect(() => pendingReviewSchema.parse({ run_id: 'r1' })).toThrow()
  })
})
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm run test --workspace @gaiafaac/web -- src/lib/review-api.test.ts`
Expected: FAIL (module missing).

- [ ] **Step 3a: Write `review-api.ts`**

```typescript
// apps/web/src/lib/review-api.ts
import { z } from 'zod'

export const pendingReviewSchema = z.object({
  run_id: z.string(),
  reporting_label: z.string(),
  revenue_month: z.iso.date(),
  source_organization: z.string(),
  status: z.string(),
  covered_states: z.number().int(),
  expected_states: z.number().int(),
  finding_count: z.number().int(),
  blocking_count: z.number().int(),
  created_at: z.string().nullable(),
})

export type PendingReviewItem = z.infer<typeof pendingReviewSchema>

export interface ApiResult<T> {
  data: T | null
  error: string | null
}

function apiBaseUrl() {
  return z
    .url()
    .parse(
      process.env.API_INTERNAL_URL ??
        process.env.NEXT_PUBLIC_API_URL ??
        'http://localhost:8000',
    )
    .replace(/\/$/, '')
}

export async function getPendingReviews(): Promise<
  ApiResult<PendingReviewItem[]>
> {
  try {
    const response = await fetch(`${apiBaseUrl()}/api/v1/review/pending`, {
      next: { revalidate: 120 },
    })
    if (!response.ok) {
      return { data: null, error: 'The review queue is unavailable.' }
    }
    return {
      data: z.array(pendingReviewSchema).parse(await response.json()),
      error: null,
    }
  } catch {
    return { data: null, error: 'The review queue is unavailable.' }
  }
}
```

- [ ] **Step 3b: Write the page** (`apps/web/src/app/review/pending/page.tsx`)

```tsx
import type { Metadata } from 'next'

import { PageHeader } from '@/components/page-header'
import { getPendingReviews } from '@/lib/review-api'

export const metadata: Metadata = { title: 'Pending review' }
export const dynamic = 'force-dynamic'

export default async function PendingReviewPage() {
  const result = await getPendingReviews()
  return (
    <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
      <PageHeader
        eyebrow="Review queue"
        title="Months awaiting review"
        description="Collected from source, imported and validated — not verified and not published until a reviewer approves. Figures are hidden here by design."
      />
      {result.data && result.data.length > 0 ? (
        <div className="mt-8 overflow-x-auto">
          <table className="w-full min-w-3xl border-collapse text-left text-sm">
            <thead>
              <tr className="border-border border-b">
                <th className="py-3 pr-5 font-medium">Report</th>
                <th className="py-3 pr-5 font-medium">Coverage</th>
                <th className="py-3 pr-5 font-medium">Findings</th>
                <th className="py-3 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {result.data.map((item) => (
                <tr
                  key={item.run_id}
                  className="border-border border-b last:border-0"
                >
                  <td className="py-4 pr-5 font-medium">
                    {item.reporting_label}
                  </td>
                  <td className="py-4 pr-5">
                    {item.covered_states} / {item.expected_states}
                  </td>
                  <td className="py-4 pr-5">
                    {item.finding_count} ({item.blocking_count} blocking)
                  </td>
                  <td className="py-4">{item.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p className="text-muted-foreground mt-10 text-sm">
          Nothing awaiting review. Collected months appear here for approval.
        </p>
      )}
    </div>
  )
}
```

- [ ] **Step 3c: Add the nav link** in `site-header.tsx` `navigation` array (after the `live` entry):

```typescript
  { href: '/review/pending', label: 'Review queue' },
```

- [ ] **Step 4: Run test + build to verify**

Run: `npm run test --workspace @gaiafaac/web -- src/lib/review-api.test.ts`
Expected: PASS.
Run: `npm run build`
Expected: build succeeds (page compiles).

- [ ] **Step 5: Commit**

```bash
git add apps/web/src/lib/review-api.ts apps/web/src/lib/review-api.test.ts \
        apps/web/src/app/review/pending/page.tsx apps/web/src/components/site-header.tsx
git commit -m "feat(web): pending-review queue page + nav link"
```

---

### Task 9: Deploy the collector as a Railway cron service

**Files:** none (operational). Uses the existing `apps/api/Dockerfile` image.

**Interfaces:** Consumes the built CLI (`gaiafaac-db collect-oagf`) and the live Neon DB.

- [ ] **Step 1: Run the full verification suite locally**

```bash
python -m ruff format --check apps/api
python -m ruff check apps/api
python -m pytest apps/api/tests
npm run test --workspace @gaiafaac/web
npm run build
```

Expected: all green. Push the branch: `git push`.

- [ ] **Step 2: Dry-run the collector against production (no writes)**

```bash
railway link --project 366c7826-db5f-4507-8639-fddc9ba3dc02 \
  --environment 8a27a756-27f1-46cc-a736-ef4161005652 \
  --service 294b055c-85cd-430a-826e-b861db55975e >/dev/null 2>&1
DATABASE_URL="<neon url with current password>" gaiafaac-db collect-oagf --dry-run
```

Expected: prints candidate URLs for the last 3 revenue months.

- [ ] **Step 3: Create the cron service (shares the API image + env)**

```bash
railway add --service gaiafaac-collector \
  --repo oluwafemidiakhoa/gaiafaac-intelligence \
  --variables "DATABASE_URL=<neon url with current password>" \
  --variables "API_ENVIRONMENT=production" \
  --variables "RAILWAY_DOCKERFILE_PATH=apps/api/Dockerfile"
# force the Dockerfile build (Railway's first build defaults to Railpack)
railway variables --service gaiafaac-collector --set "RAILWAY_DOCKERFILE_PATH=apps/api/Dockerfile"
```

- [ ] **Step 4: Set the Zoho SMTP variables** (secret set by the human, never in chat/code)

The user sets these in the Railway dashboard for `gaiafaac-collector`:
`SMTP_HOST=smtp.zoho.com`, `SMTP_PORT=465`, `SMTP_USERNAME=<zoho address>`,
`SMTP_PASSWORD=<zoho app password>`, `ALERT_FROM=<zoho address>`,
`ALERT_TO=ethagagroalliedltd@gmail.com`.

- [ ] **Step 5: Set the cron schedule + start command**

In the Railway dashboard for `gaiafaac-collector` → Settings:

- **Cron Schedule:** `0 6 * * *` (daily 06:00 UTC)
- **Custom Start Command:** `gaiafaac-db collect-oagf`

- [ ] **Step 6: Trigger once and verify**

Redeploy the collector, then confirm a queued month appears:

```bash
curl -s https://gaiafaac-backend-production.up.railway.app/api/v1/review/pending | head -c 800
```

Expected: a JSON array; when OAGF's latest month is available it lists an entry with `expected_states: 37` and no figures. Confirm the "Review queue" page renders at the website domain.

- [ ] **Step 7: Commit any config/doc notes** (if a deployment README was updated)

```bash
git add -A && git commit -m "docs(collection): record collector cron deployment"
```

---

## Self-Review

**Spec coverage:**

- URL builder → Task 1. Downloader → Task 2. Collector runner (idempotent, never-publish) → Task 3. Zoho notifier + config → Task 4. `collect-oagf` CLI → Task 5. Review service → Task 6. `/review/pending` endpoint → Task 7. Web page + nav → Task 8. Railway cron → Task 9. Fail-closed behaviours are exercised in Tasks 2 (404/non-PDF), 3 (missing month, idempotency, never-publish), 4 (unconfigured/SMTP error). FCT caveat is documented in the spec; no task publishes. **All spec sections covered.**

**Placeholder scan:** No TBD/TODO; every code step contains full code. The only human-supplied values are the Neon URL and Zoho secrets in Task 9 (correctly kept out of code by design).

**Type consistency:** `run_collection` signature matches its callers (CLI Task 5) and returns `CollectionSummary`/`QueuedMonth` used verbatim in tests. `ImportRequest`/`ImportResult` fields match `importer.py`. `PendingReviewItem` fields match across schema (Task 6), endpoint (Task 7), and Zod schema (Task 8). `send_review_alert` keyword args match between `notify.py` and the CLI call. `candidate_urls(int, int)` used consistently.

Plan is internally consistent and complete.
