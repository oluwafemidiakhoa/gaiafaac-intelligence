# Architecture

GaiaFAAC Intelligence uses a deployable monorepo with a clear boundary between presentation, public API, durable storage, and offline processing.

```text
Browser -> Next.js web -> FastAPI /api/v1 -> PostgreSQL
                              ^
                              |
                    reviewed pipeline outputs

Source files -> collectors -> extractors -> transformers
             -> validators -> explicit approval -> loaders
```

The Next.js app is a server-first App Router application. The FastAPI service owns validation, authorization, database access, publication policy, and future approved Ask Gaia functions. Data pipelines are deliberately separate from request handling so document processing cannot publish directly.

Milestone 2 adds the durable data model and source registry. All monetary columns
use fixed-precision `NUMERIC`; reported text and unit metadata remain alongside
normalized values. Reporting periods retain revenue month, FAAC meeting date, and
publication date separately.

Source registration is intentionally a metadata-only boundary:

```text
local source file -> SHA-256 + metadata -> source_documents
                                       -> no extraction or publication
```

Demo records have `is_demo=true`, remain unpublished, and are protected by
database checks that reject a demo/published combination.

Milestone 3 implements the controlled ingestion path:

```text
reviewed CSV
  -> extension and size contract
  -> SHA-256 source registration
  -> exact unit-aware monetary parsing
  -> explicit state alias normalization
  -> pending allocation records
  -> durable reconciliation findings
  -> active reviewer/administrator decision
  -> human-verified or rejected (still unpublished)
```

Invalid rows become reviewable findings rather than silently corrected values.
Approval re-runs validation to avoid approving stale results and writes an audit
record. Administrative HTTP endpoints, document extraction from PDF/Excel,
publication, dashboards, and analytics remain outside Milestone 3.

Milestone 4 adds a demo-only read boundary:

```text
Next.js Server Components
  -> versioned FastAPI read endpoints
  -> queries constrained to is_demo=true and is_published=false
  -> labelled demo responses
```

The overview aggregates only the three synthetic seed rows and calls the result
a demo-sample total. The state directory still lists all 37 jurisdictions; the
34 without a demo allocation receive `null`, never zero or an inferred value.
Internal source storage paths are not exposed. Pages render an explicit
unavailable state when the API or seed is absent.

## Gaia Fiscal Ledger foundation

The Phase 1 ledger extends the publication boundary rather than replacing it:

```text
published StateAllocation + State + ReportingPeriod + SourceDocument
  -> explicit ledger materialization service
  -> immutable FiscalClaim + EvidenceVerification
  -> canonical EvidenceManifest + FiscalProof
  -> versioned FiscalState
  -> /api/v1/proofs/{gaia_id}
  -> /api/v1/jurisdictions/{code}/state
```

Reads never materialize or mutate ledger objects. No migration backfills production
records. An approved process must explicitly call the materialization services after
the underlying allocation has been published. The original published and demo APIs,
Fiscal Pulse, Fiscal Watch, Decision Packets, Gaia Analyst, Fiscal Design, and legacy
Fiscal Proof endpoint remain compatible.

Canonical hashing lives in `gaiafaac_api.ledger.canonical`. It preserves Decimal
scale as JSON strings, normalizes Unicode to NFC, normalizes aware datetimes to UTC,
sorts object keys, and rejects binary floating point. Browser verification implements
the same canonical object ordering for proof manifests while preserving the existing
Fiscal Design v1 `JSON.stringify(payload)` behavior.

## Gaia Fiscal Ledger trust layer

Phase 2 remains inside the governed publication boundary:

```text
approved source + published claim
  -> versioned evidence-source registry record
  -> optional immutable claim revision
  -> optional explicit conflict + participants
  -> deterministic coverage + Evidence Integrity
  -> immutable Fiscal State v1.1
  -> historical state and source-registry APIs
```

Trust calculations are pure `Decimal` functions configured in
`gaiafaac_api.ledger.trust`. Conflict detection is not inferred from narrative or an
LLM: a service must explicitly register claims that share jurisdiction, domain,
period, and metric but have different retained values. Reads do not recalculate old
states, so historical methodology and results remain reproducible.

### Phase 2 assessment

- **Strengths retained:** exact money, distinct fiscal dates, source SHA-256 lineage,
  human approval, deterministic services, and fail-closed missing data.
- **Debt addressed:** deterministic coverage/integrity, immutable revision records,
  explicit conflict participants, richer source metadata, and inclusive date history.
- **Reusable foundation:** Phase 1 claims, manifests, proofs, states, canonical hashing,
  and approval integration are extended rather than replaced.
- **Remaining gaps:** conflict-resolution governance, historical backfill, expanded
  evidence ingestion, and deterministic fiscal classification remain later work.
- **Primary migration risk:** implying quality where evidence is absent. Component
  scores therefore remain `insufficient_evidence` until their documented inputs exist;
  the migration creates no synthetic registry, revision, conflict, or state records.

## Institutional UX layer

Phase 3 adds two immutable read models without changing Fiscal Proof or Fiscal State
hash semantics:

```text
recorded source / revision / conflict / state transition
  -> deterministic FiscalEvent
  -> filterable institutional event stream

published FiscalState + its proof IDs
  -> immutable Fiscal Certificate manifest
  -> HTML / print / JSON representations
```

The web application reads these objects through Server Components. Jurisdiction pages
link every available domain claim to its proof and render absent domains as
`unavailable`. No public event or certificate mutation endpoint exists. Classification
of financial movements remains Phase 4 work; Phase 3 emits evidence lifecycle events
only.
