# OAGF Automated Collector — Design

**Date:** 2026-07-31
**Status:** Approved (design), pending implementation plan
**Author:** GaiaFAAC engineering

## Purpose

Keep GaiaFAAC current with newly published OAGF FAAC monthly reports **automatically**,
reducing the recurring work of ingesting a month to a single human approval. The collector
is the _supply engine_ for the Monthly FAAC Data Pack (revenue) and the historical dataset.

It **fetches → imports → validates → queues → emails**, and **never publishes**. Publication
remains a governed, human-approved step. This is a correctness guarantee, not a preference.

## Non-negotiable constraints (from AGENTS.md / CLAUDE.md)

- The collector **cannot publish.** It imports only `import_file` + validation; it does not
  import `approve_import` / `publish_import`. Publishing stays a separate manual step.
- **Fail closed.** A 404 (month not yet released), a scanned/unparseable PDF, or any error
  leaves nothing published and surfaces the item for review.
- **Source lineage.** Every downloaded document is SHA-256'd and registered as a
  `SourceDocument` before extraction (handled by the existing `import_file`).
- **Idempotent.** Running daily must not create duplicates: a month already ingested (by
  revenue-month or by SHA-256) is skipped.
- Demo records are untouched and can never be published (existing DB CHECK).

## Scope

**In:**

- `pipeline/collection/` module: OAGF URL builder, collector runner, Zoho email notifier.
- `collect-oagf` CLI command.
- `GET /api/v1/review/pending` endpoint (metadata only) + a read-only "Pending review" web page.
- A scheduled Railway cron service running the collector daily.
- Tests for URL building, collection orchestration (idempotency, never-publish), notifier, and the endpoint.

**Out (later milestones):**

- Click-to-approve from the UI (needs the auth milestone; approval stays on the CLI).
- HTML scraping of the OAGF listing page (URL-pattern discovery is enough).
- NBS or other second sources.
- FCT reconciliation (a separate data-policy decision; see caveat).

## Architecture

New module `apps/api/src/gaiafaac_api/pipeline/collection/`, mirroring the existing
`pipeline/extraction/` layout.

### 1. `oagf_urls.py` — URL builder

Maps a **revenue month** to candidate OAGF PDF URLs. Verified pattern:

- Filename uses the **revenue** month name + revenue year: `Disbursement-<MonthName>-<Year>.pdf`.
- Upload folder uses the **publication** year/month (revenue month + 1, occasionally + 2),
  with correct year rollover (e.g. revenue Dec 2024 → folder `2025/01`).
- Base: `https://oagf.gov.ng/wp-content/uploads/{pub_year}/{pub_month:02d}/{filename}`

`candidate_urls(revenue_year, revenue_month) -> list[str]` returns the folder+1 and folder+2
variants, in order. Pure function, fully unit-tested (Jan 2024 → `.../2024/02/Disbursement-January-2024.pdf`).

### 2. `collector.py` — runner

`run_collection(session, *, months_back=3, downloader=..., importer=import_file, notifier=None, now=None) -> CollectionSummary`

For each of the last `months_back` revenue-months (most recent first):

1. **Pre-check dedup:** if a non-demo `ReportingPeriod`/`SourceDocument` already exists for that
   revenue-month, skip without downloading.
2. Build candidate URLs; try each; on the first successful PDF download:
   - Compute SHA-256; if a `SourceDocument` with that hash exists, skip.
   - Else call `importer(...)` (default `import_file`) with source metadata
     (org = OAGF, `revenue_month`, `reporting_label`, `source_url`, `reported_unit="naira"`).
   - On a fresh `requires_review` run, record it and send a review alert.
3. If no candidate URL returns a PDF (all 404), skip — the month isn't out yet; retry tomorrow.

Writes an `AuditLog` (`action="collection.run"`) summarizing checked / downloaded / imported /
skipped / errored. Returns a `CollectionSummary` dataclass. **Injectable `downloader`,
`importer`, `notifier`, and `now`** keep the orchestration unit-testable in isolation.

`downloader` default: streams the URL to `data/raw/`, verifies `%PDF` magic bytes and a
content-type/size sanity check, returns the path (or `None` on 404/non-PDF).

### 3. `notify.py` — Zoho email notifier

`send_review_alert(settings, *, reporting_label, coverage, finding_count, queue_url) -> bool`

Sends via `smtplib.SMTP_SSL(smtp_host, smtp_port)` (Zoho `smtp.zoho.com:465`), logging in with
`SMTP_USERNAME`/`SMTP_PASSWORD`, `From: ALERT_FROM`, `To: ALERT_TO`. If SMTP settings are unset,
returns `False` (email skipped, logged). **All exceptions are caught and logged — a failed email
never blocks or breaks collection.**

### 4. Review queue — API + page

- `GET /api/v1/review/pending`: real (non-demo), not-yet-published reporting periods whose run is
  `requires_review` (or approved-but-unpublished). Returns **metadata only**:
  `reporting_label, revenue_month, source_organization, covered_states, expected_states,
finding_count, blocking_count, status, run_id, created_at`. **Never the unverified figures.**
- `/review/pending` web page: a read-only table of the above, each row clearly labelled
  "pending review — not verified". Approval remains a CLI action.

### 5. Config additions (`config.py`)

New **optional** settings (blank ⇒ email disabled), read from env:
`SMTP_HOST, SMTP_PORT(=465), SMTP_USERNAME, SMTP_PASSWORD, ALERT_FROM, ALERT_TO`.
`SMTP_PASSWORD` is a Zoho **app-specific password**, set directly in Railway — never committed
or pasted into chat.

### 6. CLI — `collect-oagf`

Options: `--months-back N` (default 3), `--dry-run` (report candidates without importing),
`--revenue-month YYYY-MM-01` (force a specific month). Wires to `run_collection` and prints the summary.

### 7. Deployment — Railway cron

A third Railway service `gaiafaac-collector` built from `apps/api/Dockerfile` (via
`RAILWAY_DOCKERFILE_PATH`), sharing `DATABASE_URL` + SMTP vars, with:

- **Cron schedule:** daily (e.g. `0 6 * * *`).
- **Start command:** `gaiafaac-db collect-oagf`.
  Run-and-exit, so it does not interact with the web/API services. Managed via the Railway CLI.

## Data flow

```
daily cron → collect-oagf → run_collection
   for each recent revenue-month not already ingested:
     build OAGF URL(s) → download → SHA-256 (skip if seen) → import_file → requires_review
     └ send_review_alert (Zoho)            (never publishes)
   write AuditLog(collection.run)

you → GET /review/pending  → gaiafaac-db approve-import → gaiafaac-db publish-import → /live
```

## Error handling / fail-closed

| Condition                               | Behaviour                                                           |
| --------------------------------------- | ------------------------------------------------------------------- |
| Month not released (all URLs 404)       | Skip; retry next run. No error.                                     |
| Already ingested (revenue-month or SHA) | Skip (idempotent).                                                  |
| Scanned / unparseable PDF               | `import_file` flags `requires_review` with warnings; not published. |
| Blocking validation findings (e.g. FCT) | Stays queued; not publishable until resolved.                       |
| Email send fails                        | Logged; month still queued.                                         |
| Network/DB error on one month           | Logged; loop continues to next month.                               |

## Testing

- `test_oagf_urls`: revenue-month → expected candidate URLs, including year rollover.
- `test_collector`: injected `downloader` returns a fixture; asserts an import runs and lands
  `requires_review`; second run is a no-op (dedup); asserts nothing is ever published; asserts
  the module never references `publish_import`.
- `test_notify`: monkeypatched `smtplib`; asserts message headers/body; asserts a raised SMTP
  error is swallowed and returns `False`.
- `test_review_pending`: seed a pending real run + a demo run + a published run; assert only the
  pending real run is returned and no allocation figures are present.

Runs on the existing SQLite in-memory harness.

## FCT caveat

The collector does **not** resolve the FCT gap. Every collected month arrives with the same
36/37 completeness finding and waits in the queue until the FCT publish-policy is set (reconcile
to 37, or publish 36/37 with transparent coverage). Automation delivers months to the doorstep,
clean and validated; the FCT decision still governs whether they reach `/live`.

## Success criteria

- Running `collect-oagf` twice ingests each available month exactly once and publishes nothing.
- A newly released OAGF month appears in `/review/pending` within a day, with an email alert.
- All new code covered by tests; full CI suite green.
