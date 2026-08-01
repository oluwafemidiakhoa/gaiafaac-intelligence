# Milestone 5 · Sub-project 1 — Analytics engine (design)

Date: 2026-07-24
Status: Draft for review
Scope: Milestone 5, sub-project 1 of 3 (analytics engine). Reports (sub-project 2)
and grounded Ask Gaia (sub-project 3) are separate cycles with their own specs.

## Context

The platform is at Milestone 4: a read-only, demo-only interface over a labelled
synthetic dataset of **3 state allocations in a single reporting period**
(Lagos/Kano/Rivers, revenue month 2099-01). Milestone 5 adds analytics, reports,
and a grounded Ask Gaia Q&A. This spec covers only the analytics engine.

Analytics cannot run on 3 rows in one period. Rankings, volatility,
revenue-dependency, and forecasting all need many states across many periods. The
project's non-negotiable rule is that we never invent or infer _real/published_
financial figures. A **clearly-labelled synthetic demo dataset** is the sanctioned
exception (the existing `seed-demo` already relies on it); analytics then computes
deterministically over those stored figures and never fabricates values.

## Goals

1. Generate a larger, labelled synthetic, multi-period demo dataset to analyze.
2. Compute four analytics deterministically from stored figures: rankings,
   volatility, revenue-dependency, forecasting.
3. Persist results in the existing `state_indicators` and `forecasts` tables with
   full provenance, marked `is_demo=true`, unpublished.
4. Expose read-only, demo-labelled `/api/v1` endpoints for each analytic.
5. Full deterministic test coverage.

## Non-goals (this sub-project)

- No web UI or charts (deferred to cycle 1b).
- No reports (sub-project 2) and no LLM / Ask Gaia (sub-project 3).
- No real-data ingestion or publication; nothing is ever marked published.
- No new database migration — `state_indicators` and `forecasts` already exist in
  the schema and the Milestone 2 migration.

## Architecture decision

**Precomputed pipeline → analytics tables → read API.** A CLI-invoked pipeline
computes analytics and writes them to `state_indicators` / `forecasts`; endpoints
serve stored rows. This matches the established "pipelines are separate from
request handling" boundary, makes every figure persistent, reproducible, and
**citable to its source periods**, and produces exactly the durable, pre-computed
numbers that grounded Ask Gaia (sub-project 3) will later read verbatim so the LLM
never computes or infers a figure. Rejected: on-the-fly computation (no
persistence/provenance, weaker downstream grounding) and a hybrid (two provenance
paths, unnecessary complexity now).

## Component 1 — Synthetic multi-period dataset generator

New CLI verb `gaiafaac-db seed-analytics-demo` (idempotent). Produces a
self-contained analytics dataset, independent of the existing 3-row demo period.

- **Coverage:** 37 jurisdictions × **36 consecutive monthly periods**, revenue
  months **2096-01 through 2098-12**.
- **Separation from existing demo:** analytics periods carry `reporting_label`
  prefixed `"DEMO ANALYTICS — "` and attach to a dedicated synthetic source
  document. Because the pre-existing demo period is 2099-01 (later than any
  analytics period), Milestone 4's `latest_demo_period` still resolves to the
  original period and **existing M4 pages are unaffected**. Analytics code scopes
  strictly to the `"DEMO ANALYTICS — "` periods.
- **Determinism:** every value is seeded reproducibly from a fixed namespace hash
  of `(state_code, revenue_month)`, so repeated runs and tests are stable. Each
  state has a base net level, a 12-month seasonal pattern, and mild bounded noise,
  giving volatility and forecasting real signal.
- **Components:** each `StateAllocation` gets multiple `StateAllocationComponent`
  rows across component types (statutory, VAT, derivation for a fixed set of
  oil-producing states, plus others) whose amounts reconcile to the allocation
  totals — feeding revenue-dependency.
- **Invariants honored:** `gross − deductions = net` within tolerance; components
  reconcile; explicit `reported_unit = naira`; every row `is_demo=true`,
  `is_published=false`, `verification_status=pending`,
  `data_label = "DEMO DATA - NOT REAL FAAC DATA"`.
- **Volume:** 36 periods × 37 states = 1 332 allocations (+ components). Written in
  one transaction; re-running is a no-op when the dataset already exists.

## Component 2 — Analytics definitions (deterministic, stored figures only)

Modules under `apps/api/src/gaiafaac_api/pipeline/analytics/` (`rankings.py`,
`volatility.py`, `dependency.py`, `forecasting.py`) plus an orchestrator
`run.py`, consistent with where M3/M4 pipeline code already lives. Let `L` be the
latest analytics period (2098-12).

- **Rankings** — for `L`, order the 37 jurisdictions by `net_allocation` desc →
  `net_allocation_rank` (1..37); `net_allocation_rank_change` = prior-period rank
  − current rank (omitted where no prior period). Money uses `Decimal`.
- **Volatility** — per state, coefficient of variation
  `stddev(net) / mean(net)` of `net_allocation` over the trailing **12 periods**
  ending at `L`. Requires ≥ 3 non-null periods and a non-zero mean, else the
  indicator is **omitted** (never zero). Stored as a ratio.
- **Revenue-dependency** — for `L`, per state: each component type's share of net
  (`component_net / total_net`) and a Herfindahl–Hirschman concentration index
  (`Σ share²`, range 0–1) over the component mix. Computed from
  `StateAllocationComponent`. Omitted where components or net are missing.
- **Forecasting** — per state, forecast `net_allocation` for the next period
  (2099-01) from history through `L`. Requires ≥ 6 periods, else **omitted**.
  Supported methods (existing `ForecastMethod` enum): `moving_average` (default,
  stored) and `seasonal_naive`; the interval is `point ± 1.96 × residual_stddev`
  from a one-step backtest over the training window (≤ 24 periods). All money in
  `Decimal`, quantized to kobo, with `lower_bound ≤ point_estimate ≤ upper_bound`
  (existing DB check). Surfaced strictly as an **estimate**.

Money math uses `Decimal`; ratios and CV use the `NUMERIC` precise/confidence
column types already defined (`PRECISE_NUMBER`, `CONFIDENCE`). No floats for money.

## Component 3 — Storage & provenance

- Rankings, volatility, dependency → `state_indicators`, upserted on the existing
  unique key `(reporting_period_id, state_id, indicator_type, indicator_name)`
  (idempotent recompute). `indicator_type` ∈ {`ranking`, `volatility`,
  `dependency`}; `methodology` records the formula and the exact input period
  range.
- Forecasting → `forecasts` with `method`, `training_start`/`training_end`,
  `point_estimate`, `lower_bound`, `upper_bound`, and `metrics` JSON capturing
  backtest error (MAE/RMSE), residual stddev, and the source period ids.
- All rows: `is_demo=true`, `is_published=false`, `verification_status=pending`
  (never labelled verified without human approval). A recompute deletes prior
  demo analytics rows of these types for the analytics periods and rewrites them in
  one transaction (mirrors how `validate_import` rebuilds findings).
- **Provenance is the grounding seed for Ask Gaia:** every stored figure traces to
  the periods/allocations it derives from, so sub-project 3's LLM can cite exact
  rows and never needs to compute a number.

## Component 4 — Orchestration & CLI

- `gaiafaac-db seed-analytics-demo` — generate the dataset (idempotent).
- `gaiafaac-db compute-analytics` — run the orchestrator over the analytics
  dataset and write results. Only ever writes `is_demo`, unpublishable rows; it
  refuses to touch or produce published data.

## Component 5 — Read API (`/api/v1`, GET, demo-constrained)

New router `analytics` under the existing v1 router. All queries filtered to
`is_demo=true AND is_published=false` and scoped to the analytics periods.

- `GET /analytics/rankings` — ranked states for `L` (net, rank, rank_change).
- `GET /analytics/volatility` — per-state CV over the trailing window.
- `GET /analytics/dependency` — per-state component shares + concentration index.
- `GET /analytics/forecasts` (and `/analytics/forecasts/{slug}`) — point estimate,
  interval, method, training window.

Pydantic responses carry the `data_label` literal and a scope note; forecast
responses additionally carry `is_estimate=true` and the interval, and never
present a forecast as a reported allocation. Missing analytics render as
absent/null, never zero. (Shared TS types, Zod schemas, and pages/charts are
cycle 1b.)

## Integrity & error handling

- **Fail closed:** insufficient history → the analytic is omitted (absent/null),
  never zero or fabricated — mirrors M4's "unavailable, not zero".
- Forecasts always carry an uncertainty interval and estimate labelling.
- Volatility / anomaly wording is strictly statistical; never framed as misconduct
  or governance performance.
- Demo-vs-published separation stays enforced by the existing DB check
  (`NOT (is_demo AND is_published)`).

## Testing

SQLite in-memory (existing `conftest`). Deterministic dataset → exact assertions:

- **Dataset:** 1 332 allocations across 36 periods × 37 states; every row demo +
  unpublished; `gross − deductions = net`; components reconcile.
- **Rankings:** known ordering and rank_change for a seeded period.
- **Volatility:** known CV for a seeded state; insufficient/zero-mean → omitted.
- **Dependency:** known component shares and HHI for a seeded state.
- **Forecasting:** `lower ≤ point ≤ upper`; `is_estimate` labelling; < 6 periods →
  omitted; metrics/provenance populated.
- **API:** every response demo-labelled and constrained; forecasts labelled
  estimates; missing analytics absent, not zero.
- **Idempotence:** running `compute-analytics` twice yields identical rows.
- **M4 non-regression:** `latest_demo_period` still resolves to the 2099-01 period;
  existing demo endpoints unchanged.

No new migration; `state_indicators` and `forecasts` already exist.

## Assumptions

- PostgreSQL 16 / Python 3.12 as elsewhere; no new third-party dependencies
  (statistics via the standard library and `Decimal`).
- Analytics is demo-only this milestone; there is no real or published data.
