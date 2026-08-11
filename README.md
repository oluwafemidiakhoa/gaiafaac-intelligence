# GaiaFAAC Intelligence

**Verified fiscal intelligence for every Nigerian state.**

GaiaFAAC Intelligence is an independent public-finance research platform that turns Nigerian Federation Account Allocation Committee records and governed state internally generated revenue evidence into source-linked data, comparisons, and derived fiscal signals. It is **not an official government platform**.

The platform publishes real, human-approved FAAC records extracted from Office of the Accountant-General of the Federation source documents and governed, human-verified IGR records from registered source documents. Published evidence preserves source lineage and SHA-256 fingerprints.

## Live product

Live application:

- https://gaiafaac-api-production.up.railway.app/

Current public capabilities:

- Latest verified FAAC month across all 36 states and the FCT
- Gross allocation, deductions, and net allocation where reported
- Published, human-verified state IGR evidence with source provenance
- Gaia Analyst natural-language questions over governed FAAC and IGR evidence
- IGR state lookup, latest-record lookup, comparable-period rankings, and two-state comparisons
- GaiaFAAC Fiscal Pulse for the verified 2024 series
- Deduction burden and net-retention indicators where comparable inputs are complete
- Allocation momentum and volatility signals
- Evidence-status labels that expose incomplete or partial records
- State directory and state-level detail pages
- Two-to-six-jurisdiction comparison
- Published-month source registry with SHA-256 fingerprints
- National trend, latest rankings, and month-to-month movers
- Methodology and data-governance documentation
- Public pricing and pilot-access information

Commercial API foundations are also implemented:

- API keys are stored as hashes
- Plan entitlements are enforced server-side
- Daily request limits are recorded and enforced
- Published historical-month and allocation endpoints require an entitled key

## Gaia Analyst

Gaia Analyst is an evidence-grounded natural-language interface over governed published data. It routes FAAC questions through the existing deterministic fiscal services and IGR questions through the published IGR evidence layer.

Supported IGR question patterns include:

- state-specific IGR for an exact fiscal year
- latest published IGR for a named state
- highest or lowest IGR rankings within one comparable published fiscal period
- two-state IGR comparisons when both states have matching period evidence

Gaia Analyst does not infer missing periods, annualize partial-year IGR, substitute another fiscal year for an exact-year question, or compare mismatched fiscal periods. IGR evidence surfaces its fiscal period, source organization, and source SHA-256 provenance in the public interface.

## Fiscal Pulse

GaiaFAAC Fiscal Pulse is a descriptive intelligence layer over published, human-approved allocation records.

Current indicators include:

- **Deduction burden** = annual deductions / annual gross allocation
- **Net retention** = annual net allocation / annual gross allocation
- **Allocation momentum** = latest three-month average compared with the preceding three-month average
- **Allocation volatility** = population coefficient of variation over valid monthly net allocations
- **Evidence status** = Verified, Partial, or Review required based on completeness of the published series

Missing values are never converted to zero or estimated. Where a comparable gross or deduction series is unavailable, the dependent metric is shown as unavailable.

Fiscal Pulse is **not** a credit rating, solvency test, corruption signal, governance score, or prediction of default. Broader fiscal-risk assessment would require additional evidence such as IGR, debt service, debt stock, expenditure, liabilities, and other economic variables.

## Commercial status

GaiaFAAC is currently accepting **manually provisioned pilot customers**.

The latest verified month and selected Fiscal Pulse indicators remain publicly accessible. Paid plans are intended to unlock historical intelligence, exports, reports, team access, and API use. Automated checkout, customer accounts, personalized licensed exports, and subscription self-service are not yet complete and must not be represented as available until they are implemented.

Commercial and pilot enquiries:

- gaiafacc@gailabai.com

## Data-governance model

The system separates collection, extraction, validation, approval, publication, and public access:

```text
Registered source document
  -> download and SHA-256 registration
  -> structured extraction
  -> deterministic validation
  -> review queue
  -> explicit human approval
  -> publication
  -> public pages and entitled API access
  -> deterministic analytical services
```

Important safeguards:

- Collection and extraction never publish automatically.
- Demo, pending, rejected, and unpublished records are excluded from public evidence services.
- IGR publication requires human-verified, non-demo evidence.
- Missing figures remain unavailable; they are never silently converted to zero.
- Source inconsistencies are preserved and flagged rather than rewritten.
- The FCT may be published net-only when that is the only directly reconcilable value in the source.
- Derived metrics that require unavailable FCT gross or deduction values remain unavailable.
- Gaia Analyst does not infer missing IGR periods, annualize partial-year IGR, or compare mismatched IGR periods.
- Statistical movements are not treated as evidence of fraud, misconduct, governance performance, or credit quality.

A scheduled GitHub Actions collector checks for newly available OAGF reports daily, imports and validates them, and queues them for review. Human approval remains mandatory.

## Repository layout

```text
apps/web/             Next.js App Router frontend
apps/api/             FastAPI backend and governed data pipeline
packages/shared-types Shared TypeScript contracts
pipelines/            Pipeline support and future processing stages
database/             Alembic migrations and seed assets
data/                 Git-ignored local source and processed files
docs/                 Architecture, methodology, and operating documentation
```

## Main routes

```text
/gaia-analyst       Natural-language questions over governed FAAC and IGR evidence
/fiscal-pulse       Derived state fiscal signals over verified published records
/live               Latest verified allocations and source record
/insights           National trend, rankings, and movers
/overview           Latest published national overview
/states             All 36 states and the FCT
/states/{slug}      State detail, including published IGR evidence where available
/compare            Two-to-six-jurisdiction comparison
/sources            Source record for every published month
/methodology        Collection, validation, publication, and Fiscal Pulse methodology
/pricing            Public plan positioning
/pilot              Pilot-access and commercial enquiry
/admin/leads        Protected commercial lead inbox
```

API documentation is available at:

```text
/docs
/redoc
/api/v1/openapi.json
```

Important API routes include:

```text
GET  /api/v1/health
GET  /api/v1/published/overview/latest
GET  /api/v1/published/analytics
GET  /api/v1/published/fiscal-pulse?year=2024
GET  /api/v1/published/gaia-analyst?question=...&year=2024
GET  /api/v1/published/igr?year=2024
GET  /api/v1/published/igr?year=2024&state_slug=lagos
GET  /api/v1/published/igr/latest?state_slug=lagos
GET  /api/v1/published/sources
GET  /api/v1/data/months                         # API key required
GET  /api/v1/data/allocations?month=...          # API key required
POST /api/v1/commercial/pilot-leads
GET  /api/v1/commercial/pilot-leads              # Admin key required
GET  /api/v1/review/pending                       # Admin key required
```

## Local setup

Prerequisites:

- Node.js 20.9+
- npm 10+
- Python 3.12+
- Docker with Compose

```bash
cp .env.example .env
npm ci
python -m venv .venv
source .venv/bin/activate
python -m pip install -e "apps/api[dev,extraction]"
docker compose up --build
```

Open:

- Web: `http://localhost:3000`
- API health: `http://localhost:8000/api/v1/health`
- API docs: `http://localhost:8000/docs`

For host-based development:

```bash
npm run dev
uvicorn gaiafaac_api.main:app --app-dir apps/api/src --reload
```

Initialize the database:

```bash
alembic upgrade head
gaiafaac-db seed-states
```

## Governed import workflow

Registering a source records its checksum and lineage metadata:

```bash
gaiafaac-db register-source ./data/raw/example.pdf \
  --source-organization "Office of the Accountant-General of the Federation" \
  --publication-date 2026-07-01
```

Run a controlled allocation import:

```bash
gaiafaac-db import-allocations data/raw/reviewed.csv \
  --source-organization "Office of the Accountant-General of the Federation" \
  --revenue-month 2026-01-01 \
  --faac-meeting-date 2026-02-01 \
  --publication-date 2026-02-02 \
  --reporting-label "January 2026 allocation"
```

The reviewed CSV must contain:

```text
state
gross_total
total_deductions
net_allocation
reported_unit
```

Imports remain unpublished until validation and an explicit reviewer decision:

```bash
gaiafaac-db validate-import RUN_UUID
gaiafaac-db approve-import RUN_UUID --reviewer-id USER_UUID
# or
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

See the documentation in `docs/` for architecture, data definitions, source policy, validation methodology, collection operations, and deployment guidance.
