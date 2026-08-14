# Fiscal Ledger Phase 3 — institutional UX

## Architecture assessment

Phase 2 already provides the required immutable claims, proofs, Fiscal States,
source registry, revisions, conflicts, exact coverage, and Evidence Integrity. Phase 3
extends those records rather than creating a parallel dashboard data model. Existing
Fiscal Pulse, Fiscal Watch, Decision Packets, Gaia Analyst, Fiscal Design, publication,
and verification flows remain in place.

## Delivered scope

- `/jurisdictions/{code}` renders proof-linked Fiscal State domains, stored coverage
  and integrity, source lineage, recent lifecycle events, and explicit evidence gaps.
- `/proofs/{gaia_id}` includes stored revision details, conflicts, and an evidence
  timeline that never invents missing timestamps.
- `/events` provides jurisdiction, type, severity, date, and evidence-status filters.
- `/certificates/{gaia_id}` provides institutional HTML, print/PDF-ready output,
  linked proofs, a downloadable JSON manifest, and browser verification entry point.
- The homepage leads with the verifiable fiscal ledger position and exposes Evidence,
  Verification, History, jurisdictions, events, proofs, coverage, sources, verification,
  and API entry points.

## Deliberate boundaries

Only evidence lifecycle events are emitted. Financial event classification and
cross-jurisdiction derived intelligence remain Phase 4. No production objects are
backfilled, no unsupported domain is assigned a value, no manifest semantics are
changed, and no public creation endpoint is introduced.
