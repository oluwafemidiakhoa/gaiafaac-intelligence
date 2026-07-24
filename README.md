# GaiaFAAC Intelligence

**Nigeria’s public revenue, explained.**

GaiaFAAC Intelligence is an independent research platform for turning Nigerian Federation Account Allocation Committee records into traceable public-finance intelligence. It is **not an official government platform**.

This repository currently contains Milestone 4: the validated data foundation
plus a read-only national overview, state directory and detail pages, state
comparison, source registry, and methodology page. Every exposed record is from
the labelled synthetic demo dataset; no real allocation data is published.

## Important notices

- Demo records are unmistakably labelled **DEMO DATA** and are not real FAAC data.
- Forecasts are estimates, not reported allocations.
- Users must inspect cited source documents before making consequential decisions.
- No data should be described as verified until it has passed validation and explicit approval.

## Repository layout

```text
apps/web/             Next.js App Router frontend
apps/api/             FastAPI backend
packages/shared-types Shared TypeScript contracts
pipelines/            Future document extraction and analytics stages
database/             Alembic migrations and seed assets
data/                 Git-ignored local source/processed files
docs/                 Architecture, plans, and operating documentation
```

## Local setup

Prerequisites: Node.js 20.9+, npm 10+, Python 3.12+, and Docker with Compose.

```bash
cp .env.example .env
npm ci
python -m venv .venv
source .venv/bin/activate
python -m pip install -e "apps/api[dev]"
docker compose up --build
```

Open the web app at `http://localhost:3000`, API health at `http://localhost:8000/api/v1/health`, and API docs at `http://localhost:8000/docs`.

For host-based development:

```bash
npm run dev
uvicorn gaiafaac_api.main:app --app-dir apps/api/src --reload
```

Initialize a database and load reference data:

```bash
alembic upgrade head
gaiafaac-db seed-states
```

Registering a local source records its SHA-256 checksum and lineage metadata; it
does not parse, copy, or publish the document:

```bash
gaiafaac-db register-source ./data/raw/example.pdf \
  --source-organization "Source organization" \
  --publication-date 2026-07-01
```

The optional demo seed contains three invented, future-dated records and is
blocked from publication:

```bash
gaiafaac-db seed-demo
```

Milestone 4 pages:

```text
/overview          Partial three-state demo dashboard
/states            All 36 states and the FCT
/states/{slug}     State detail with explicit unavailable states
/compare           Two-to-six-state comparison
/sources           Safe demo source metadata
/methodology       Scope and verification methodology
```

Run a controlled allocation import:

```bash
gaiafaac-db import-allocations data/raw/reviewed.csv \
  --source-organization "Source organization" \
  --revenue-month 2026-01-01 \
  --faac-meeting-date 2026-02-01 \
  --publication-date 2026-02-02 \
  --reporting-label "January 2026 allocation"
```

The CSV must contain `state`, `gross_total`, `total_deductions`,
`net_allocation`, and `reported_unit`. Imports remain unpublished and await an
explicit active reviewer or administrator:

```bash
gaiafaac-db validate-import RUN_UUID
gaiafaac-db approve-import RUN_UUID --reviewer-id USER_UUID
# or:
gaiafaac-db reject-import RUN_UUID --reviewer-id USER_UUID --reason "Reason"
```

## Quality checks

```bash
npm run format
npm run lint
npm run typecheck
npm run test
python -m ruff format --check apps/api
python -m ruff check apps/api
python -m pytest apps/api/tests
npm run build
npm run docker:config
```

See [the implementation plan](docs/implementation-plan.md),
[data dictionary](docs/data-dictionary.md), [architecture](docs/architecture.md),
[validation methodology](docs/validation-methodology.md),
[data-source policy](docs/data-source-policy.md), and
[local setup guide](docs/local-setup.md) for details.
"# gaiafaac-intelligence" 
