# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

GaiaFAAC Intelligence is an **independent, non-governmental** research platform that turns Nigerian FAAC (Federation Account Allocation Committee) records into source-grounded public-finance intelligence. It is not an official government platform. The repo is currently at **Milestone 4**: everything exposed is clearly-labelled synthetic **demo data**; no real allocation data is published yet.

Follow the milestone order in [docs/implementation-plan.md](docs/implementation-plan.md). Do not pull later-milestone work (real-data publication, analytics, forecasting, "Ask Gaia" AI, auth endpoints, admin web UI) into the current milestone without an explicit decision — the schema models many of these tables, but they are intentionally schema-only for now.

## Non-negotiable data rules

These are the point of the project. Violating them is a correctness bug, not a style issue (source: [AGENTS.md](AGENTS.md)):

- Never invent or silently infer financial figures or monetary units. The pipeline **fails closed** rather than guessing.
- Keep revenue month, FAAC meeting date, and publication date distinct; keep gross allocation, deductions, and net allocation distinct.
- Money is `Decimal` in Python and `NUMERIC` in PostgreSQL — never floating point. See [monetary.py](apps/api/src/gaiafaac_api/pipeline/monetary.py) for exact unit-aware parsing.
- Retain source-document lineage (SHA-256, original text, reported unit, version) and verification status for every figure.
- Never label data verified until validation **and** explicit human approval complete. `is_demo` records can never be published (DB `CHECK` enforces this).
- Describe anomaly flags statistically, never as evidence of corruption. Label forecasts as estimates with uncertainty.

## Commands

Run from the repo root. Setup: `npm ci` then `python -m pip install -e "apps/api[dev]"` (Python 3.12+, Node 20.9+).

**Full stack (Docker):** `docker compose up --build` → web `:3000`, API `:8000`, health at `/api/v1/health`, docs at `/docs`.

**Host dev:** `npm run dev` (web) · `uvicorn gaiafaac_api.main:app --app-dir apps/api/src --reload` (API).

**Database & ingestion CLI** (`gaiafaac-db`, defined in [cli.py](apps/api/src/gaiafaac_api/cli.py)):

```bash
alembic upgrade head            # run from repo root (alembic.ini prepends apps/api/src)
gaiafaac-db seed-states         # 36 states + FCT, idempotent
gaiafaac-db seed-demo           # labelled synthetic demo rows (year-2099, unpublishable)
gaiafaac-db import-allocations <csv> --source-organization ... --revenue-month YYYY-MM-01 --reporting-label ...
gaiafaac-db validate-import <run_uuid>
gaiafaac-db approve-import <run_uuid> --reviewer-id <user_uuid>   # requires an active reviewer/administrator User row
```

**Full verification suite** (must all pass before handing off — mirrors [.github/workflows/ci.yml](.github/workflows/ci.yml)):

```bash
npm run format          # prettier --check (repo-wide)
npm run lint            # eslint, --max-warnings=0
npm run typecheck
npm run test            # vitest (web)
python -m ruff format --check apps/api
python -m ruff check apps/api      # rules: E,F,I,UP,B,SIM
python -m pytest apps/api/tests
npm run build
npm run docker:config   # docker compose config --quiet
```

**Single tests:**

```bash
python -m pytest apps/api/tests/test_monetary.py::test_name
python -m pytest apps/api/tests -k "monetary"
npm run test --workspace @gaiafaac/web -- src/lib/format.test.ts   # or: -- -t "test name"
```

## Architecture

Monorepo: npm workspaces (`apps/web`, `packages/*`) + a separate Python package (`apps/api`). Data flows one way into the read API; document processing is deliberately isolated so it can never publish directly ([docs/architecture.md](docs/architecture.md)).

```
Browser → Next.js Server Components → FastAPI /api/v1 (read-only) → PostgreSQL 16
                                          ▲
      CLI-only ingestion:  reviewed CSV → parse/normalize/validate → durable findings → explicit human approval (never publishes)
```

**Read path.** Pages are React Server Components. They fetch server-side through [apps/web/src/lib/demo-api.ts](apps/web/src/lib/demo-api.ts), which **re-validates every API response with Zod** before rendering. The API constrains all demo queries to `is_demo=true AND is_published=false` ([services/demo_data.py](apps/api/src/gaiafaac_api/services/demo_data.py)). Missing state records render as **unavailable** (null), never zero or an inferred value. Endpoints live under `/api/v1` ([api/v1/router.py](apps/api/src/gaiafaac_api/api/v1/router.py)).

**Governed write path (CLI only, no HTTP endpoints yet).** [pipeline/importer.py](apps/api/src/gaiafaac_api/pipeline/importer.py) registers a SHA-256'd source, parses money by explicit unit, normalizes state names via a curated alias table with **no fuzzy matching** ([pipeline/states.py](apps/api/src/gaiafaac_api/pipeline/states.py)), and writes `pending` allocations. [pipeline/validation.py](apps/api/src/gaiafaac_api/pipeline/validation.py) rebuilds durable `ValidationResult` findings (gross−deductions=net, component-sum reconciliation, month-over-month movement, full-state-set completeness) and moves the run to `requires_review`. [pipeline/approval.py](apps/api/src/gaiafaac_api/pipeline/approval.py) **re-runs validation** (to avoid approving stale results), enforces an active `reviewer`/`administrator` role, writes an `AuditLog`, and sets records to `human_verified` — still unpublished.

**Three-layer integrity invariant.** Every data guarantee is enforced at three layers, and all three must stay in sync when you change a field:

1. DB constraints in [database/models.py](apps/api/src/gaiafaac_api/database/models.py) (`NOT (is_demo AND is_published)`, confidence 0–1, forecast bound ordering, sha256 length, unique period/state).
2. Pydantic response models in [demo_schemas.py](apps/api/src/gaiafaac_api/demo_schemas.py) (every response carries a literal `data_label` = `"DEMO DATA - NOT REAL FAAC DATA"`).
3. Frontend Zod schemas in [demo-api.ts](apps/web/src/lib/demo-api.ts) and the **hand-maintained** TS mirror in [packages/shared-types/src/index.ts](packages/shared-types/src/index.ts) — these are not generated from OpenAPI, so update them by hand.

**Enums** are non-native (`native_enum=False`) with DB check constraints ([database/enums.py](apps/api/src/gaiafaac_api/database/enums.py)) — keeps the schema portable and lets migration/model tests run on SQLite.

## Conventions & gotchas

- Web: Next.js App Router, TypeScript, Tailwind, shadcn/ui. API: FastAPI, Pydantic, SQLAlchemy 2 (typed `Mapped[...]`), Alembic. All endpoints versioned under `/api/v1`.
- Keep authorization checks in the API handler/service layer, not only in middleware.
- Add tests with every behavior change. The schema is defined once in `models.py`; corresponding Alembic revisions live in [database/migrations/versions/](database/migrations/versions/).
- **Test fidelity caveat:** pytest and the migration test run on **SQLite in-memory** ([tests/conftest.py](apps/api/tests/conftest.py)), but production is Postgres 16. SQLite does not enforce `NUMERIC(24,2)` precision, so DB-level money precision is not exercised in CI — validate precision-sensitive changes against Postgres manually.
- Do not commit secrets, source documents, processed data (`data/` is git-ignored staging), or generated reports.
- The `pipelines/` directory (collectors/extractors/transformers/loaders/analytics) is intentionally empty scaffolding for future milestones — real PDF/Excel document extraction is not yet implemented.
