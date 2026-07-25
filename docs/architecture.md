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
