# Fiscal Ledger Phase 2 plan

## Current architecture

Phase 1 already materializes immutable claims, verifications, manifests, proofs, and
Fiscal States after explicit approval. The API supports proof identity and historical
state reads; the existing source registry remains document-oriented.

## Existing strengths

- exact Decimal/NUMERIC money and canonical hashes;
- separate fiscal dates and verification dimensions;
- source SHA-256 lineage and explicit human approval;
- immutable, content-versioned proofs and states;
- no production backfill or inferred missing values.

## Technical debt and data-model gaps

- coverage and integrity placeholders have no published methodology;
- supersession lacks a structured revision calculation;
- disagreements cannot retain multiple claim participants;
- source metadata cannot be browsed by jurisdiction and domain;
- date-only historical queries are not explicitly inclusive.

## Target architecture and file map

- `ledger/trust.py`: pure, configured coverage and integrity functions;
- `database/ledger_models.py`: evidence sources, revisions, conflicts, participants;
- `services/fiscal_trust.py`: registry, revision, and conflict invariants;
- `services/fiscal_ledger.py`: state calculation and publication integration;
- `api/v1/routes/fiscal_ledger.py`: historical and registry reads;
- migration `20260814_0007`: additive trust tables without backfill.

## Migration risks

- A score can be mistaken for fiscal health: every response and document labels it as
  evidence quality only.
- Missing components can become accidental zeros: unavailable components remain null;
  only an explicit unresolved conflict yields zero cross-source agreement.
- Revisions can erase history: old claims remain immutable and new rows carry lineage.
- Source metadata can expose internals: storage paths and reviewer identity remain
  excluded, and unsafe URLs are not returned.

Phase 3 UX, events, certificates, and homepage changes are intentionally excluded.
