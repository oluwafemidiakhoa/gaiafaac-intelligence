# Gaia Fiscal Intelligence

**Verified public-finance data, evidence and fiscal events for Nigeria.**

Gaia Fiscal Intelligence is an independent public-finance research platform for governed Nigerian fiscal evidence. It turns official source documents into source-linked data, comparisons, fiscal events, and derived intelligence while preserving provenance, review status, and revision history. It is **not an official government platform**.

**GaiaFAAC** remains the platform's FAAC module. The platform publishes real, human-approved FAAC records extracted from Office of the Accountant-General of the Federation source documents, and is expanding the same evidence-governance model across IGR, debt, budgets, expenditure, liabilities, and related fiscal domains. Every published source preserves its URL, document metadata, and SHA-256 fingerprint.

## Live product

Live application:

- https://gaiafaac-api-production.up.railway.app/

Current public capabilities:

- Latest verified FAAC month across all 36 states and the FCT
- Gross allocation, deductions, and net allocation where reported
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

Commercial and institutional foundations are implemented:

- Customer sessions and organization membership are server-side and tenant-scoped
- Paystack checkout is verified server-to-server before entitlement activation
- Billing history retains verified payment references and receipt identifiers
- API keys are stored as hashes and API usage is recorded against canonical keys
- Plan entitlements are enforced server-side from the canonical subscription model
- Decision Rooms preserve decision context and immutable captured evidence
- Fiscal Receipts expose deterministic evidence-boundary verification
- Fiscal Watch Contracts connect governed changes to decision re-review
- Watch delivery supports auditable in-app, opted-in email, and institutional webhook channels
- Commercial lead stages and analytics are computed from first-party persisted records only

## Fiscal Pulse

GaiaFAAC Fiscal Pulse is a descriptive intelligence layer over published, human-approved allocation records.

Current indicators include:

- **Deduction burden** = annual deductions / annual gross allocation
- **Net retention** = annual net allocation / annual gross allocation
- **Allocation momentum** = latest three-month average compared with the preceding three-month average
- **Allocation volatility** = population coefficient of variation over valid monthly net allocations
- **Evidence status** = Verified, Partial, or Review required based on completeness of the published series

Missing values are never converted to zero or estimated. Where a comparable gross or deduction series is unavailable, the dependent metric is shown as unavailable.

Fiscal Pulse is **not** a credit rating, solvency test, corruption signal, governance score, or prediction of default. Broader fiscal-risk assessment requires additional evidence such as IGR, debt service, debt stock, expenditure, liabilities, and other economic variables.

## Commercial status

Gaia Fiscal Intelligence supports a production customer-account and billing path together with an institutional decision workflow.

Paid access is activated only after server-side payment verification. Analyst, Team, and API entitlements resolve from the canonical `subscriptions` model. Verified payment records, current access periods, renewal, Decision Rooms, Fiscal Receipts, Watch Contracts, team controls, and entitled API access are represented in the live product according to plan capability.

Commercial operations use explicit lead stages (`new`, `contacted`, `qualified`, `pilot`, `proposal`, `won`, `lost`) and first-party server-side events. Gaia does not require third-party analytics, device identifiers, or fingerprinting to report its commercial funnel. Revenue analytics count actual persisted successful payment records; they do not substitute demo or modeled KPI values.

Commercial and pilot enquiries:

- gaiafacc@gailabai.com

## Data-governance model

The system separates collection, extraction, validation, approval, publication, and public access:

```text
Official source document
  -> download and SHA-256 registration
  -> structured extraction
  -> deterministic validation
  -> review queue
  -> explicit human approval
  -> publication
  -> public pages and entitled API access
  -> derived intelligence and fiscal events
  -> Decision Room / Fiscal Receipt
  -> Watch Contract / governed change
  -> human re-review / successor Fiscal Receipt
```

Important safeguards:

- Collection and extraction never publish automatically.
- Demo, pending, rejected, and unpublished records are excluded from live-data and Fiscal Pulse endpoints.
- Missing figures remain unavailable; they are never silently converted to zero.
- Source inconsistencies are preserved and flagged rather than rewritten.
- The FCT may be published net-only when that is the only directly reconcilable value in the source.
- Derived metrics that require unavailable FCT gross or deduction values remain unavailable.
- Statistical movements are not treated as evidence of fraud, misconduct, governance performance, or credit quality.
- A Fiscal Receipt verifies the recorded evidence manifest and lineage; it does not certify the customer's institutional decision.

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
/terminal             Evidence-oriented product terminal
/decision-rooms       Institutional Decision Rooms and re-review queue
/watch-contracts      Customer-defined governed monitoring contracts
/fiscal-pulse         Derived state fiscal signals over verified published records
/live                 Latest verified allocations and source record
/insights             National trend, rankings, and movers
/overview             Latest published national overview
/states               All 36 states and the FCT
/states/{slug}        State detail
/compare              Two-to-six-jurisdiction comparison
/sources              Source record for every published month
/methodology          Collection, validation, publication, and Fiscal Pulse methodology
/pricing              Public plan positioning
/pilot                Pilot-access and commercial enquiry
/account/billing      Verified payment history, access period and renewal
/admin/leads          Protected commercial revenue control plane
/verify/{receipt_id}  Public privacy-safe Fiscal Receipt verification
```

API documentation is available at:

```text
/docs
/redoc
/api/v1/openapi.json
```

Important API routes include:

```text
GET   /api/v1/health
GET   /api/v1/published/overview/latest
GET   /api/v1/published/analytics
GET   /api/v1/published/fiscal-pulse?year=2024
GET   /api/v1/published/sources
GET   /api/v1/data/months                                # API key required
GET   /api/v1/data/allocations?month=...                 # API key required
POST  /api/v1/commercial/pilot-leads
GET   /api/v1/commercial/pilot-leads                     # Admin key required
PATCH /api/v1/commercial/pilot-leads/{lead_id}           # Admin key required
GET   /api/v1/commercial/analytics                       # Admin key required
GET   /api/v1/evidence-rooms                             # Customer session / plan gated
GET   /api/v1/fiscal-watch-contracts                     # Team/API customer gated
POST  /api/v1/fiscal-watch-contracts/deliveries/run      # Organization admin
GET   /api/v1/review/pending                              # Admin key required
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
npx playwright test
```

The Playwright release gate exercises critical surfaces at 1440, 1024, 768, and 390 pixels, captures screenshots into the report artifact, and fails on uncaught browser errors, failed requests, console errors, or horizontal overflow.

See the documentation in `docs/` for architecture, data definitions, source policy, validation methodology, collection operations, and deployment guidance.