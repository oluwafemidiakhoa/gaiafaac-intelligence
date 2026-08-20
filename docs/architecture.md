# Architecture

GaiaFAAC Intelligence is a deployable monorepo that separates source collection, evidence processing, publication authority, public reads, institutional workflows, and derived intelligence.

```text
                         +--------------------------+
                         |  Official/public sources |
                         +------------+-------------+
                                      |
                           collect/archive + SHA-256
                                      |
                                      v
+---------+      +--------------------+---------------------+
| Browser | ---> | Next.js web / institutional interfaces  |
+---------+      +--------------------+---------------------+
                                      |
                                      v
                         +------------+-------------+
                         | FastAPI /api/v1          |
                         | auth/read/review services|
                         +------------+-------------+
                                      |
                                      v
                              PostgreSQL 16
                                      ^
                                      |
     extract -> normalize -> validate -> reconcile -> human review -> publication
                                      |
                         retained source evidence
```

The critical boundary is that **collection and extraction do not have publication authority**.

## Evidence lifecycle

The governed path is:

```text
source discovered
  -> exact bytes retained
  -> SHA-256/source metadata registered
  -> deterministic extraction
  -> unit/period/jurisdiction normalization
  -> deterministic validation
  -> reconciliation findings
  -> review queue
  -> explicit human approval
  -> separate publication transition
  -> immutable claims/proofs/states/certificates
  -> public and commercial intelligence
```

A source inconsistency remains an inconsistency. The system does not mutate observed values to make them reconcile.

## Core data domains

### State FAAC evidence

State allocations preserve source lineage, reporting-period semantics, gross/deduction/net values where reported, components, validation findings, review state and publication state.

### National distribution evidence

National evidence records distributable totals and reported components such as federal, states, local governments and derivation according to explicit source semantics. Reconciliation uses source-derived precision and preserves conflicts rather than forcing equality.

### Local-government evidence

OAGF Table IV extraction produces individual local-government observations tied to the retained OAGF source. The governed workflow fails closed when expected coverage or panel/table interpretation is incomplete. The current LGA ledger requires complete governed jurisdiction coverage before approval/publication and applies four-eyes publication controls.

### IGR evidence

State IGR is a separate fiscal domain with its own source, period, unit and publication semantics. It must not be merged into FAAC claims without explicit methodology.

## Fiscal Ledger

Published fiscal evidence can be materialized into an immutable ledger layer:

```text
published governed record
  -> FiscalClaim
  -> EvidenceVerification
  -> EvidenceManifest
  -> FiscalProof
  -> FiscalState
  -> FiscalEvent
  -> FiscalCertificate
```

Canonical hashing is deterministic. Decimal values remain decimal strings in canonical JSON; object ordering, Unicode and timezone handling must stay stable so historical proofs remain reproducible.

Reads must not silently mutate or recalculate historical immutable evidence objects.

## Trust layer

The trust layer adds explicit evidence quality and change history without replacing the source record:

```text
source registry
  + claim revision/supersession
  + explicit evidence conflict
  + deterministic coverage/integrity
  -> point-in-time Fiscal State
```

Conflict detection must be based on retained claims and explicit scope, not an LLM narrative. A conflict is data, not an accusation.

## Institutional UX

The web application exposes both public discovery and institutional evidence workflows. Current areas include state/FCT and LGA drill-down, source/evidence exploration, Fiscal Pulse, Fiscal Watch, Fiscal Proof, Fiscal State, certificates, events, Decision Packets, Fiscal Design, Gaia Analyst and account/commercial foundations.

The intended experience is:

- extremely simple jurisdiction/month discovery;
- evidence status visible beside important numbers;
- direct source and proof access;
- missing/conflicted data rendered explicitly;
- revision history visible rather than overwritten;
- institutional workflows layered on top of the same governed data.

## Derived intelligence

Derived services may calculate analytics, monitoring signals, comparisons, scenarios and grounded natural-language answers only from eligible governed data.

Derived intelligence must preserve the distinction between:

- observed source values;
- deterministic derived metrics;
- assumptions;
- modeled/scenario values;
- unavailable evidence.

No analytic movement alone is evidence of corruption, misconduct, governance quality, credit quality or default risk.

## Authorization boundaries

Operational review/publication endpoints are protected by server-side authorization. Customer/commercial endpoints use their own session/API-key/entitlement controls. Authorization belongs in API/service code and must not rely on frontend hiding or middleware alone.

Four-eyes flows must prevent the same authorized actor from both approving and publishing the governed batch when that control applies.

## Source authority and third-party data

Primary official evidence is preferred. Official secondary sources may corroborate or fill clearly labeled availability gaps. Third-party fiscal portals may be used for feature benchmarking, discovery or contextual comparison, but their figures do not enter the canonical ledger without independent source verification.

## Database and integrity

Money uses fixed-precision database types and Python `Decimal`. Production targets PostgreSQL. Database constraints, Pydantic contracts, service-layer invariants and frontend runtime schemas should agree on publication and evidence semantics.

The test suite uses SQLite for many API tests, so PostgreSQL-specific precision, migration, locking and concurrency behavior requires additional production-like verification.

## Scheduled operations

GitHub Actions currently provide CI plus governed collection/revision-monitoring workflows. Scheduled collection may discover, archive, extract, validate and queue evidence, but human review remains the publication boundary.

## Next architecture priorities

1. Production PostgreSQL integration tests for monetary precision, migrations and publication invariants.
2. Cross-level reconciliation where national/state/FCT/LGA source semantics are genuinely comparable.
3. Unified search and evidence identity across jurisdictions, periods and domains.
4. Durable notification/event delivery for source revisions, new publications, conflicts and material deterministic movements.
5. Expanded fiscal domains (debt, expenditure, budgets, liabilities) only with the same source/review/proof contract.
6. Stable institutional APIs, exports and saved-workspace primitives.
