# Implementation plan

## Current direction: Gaia Fiscal Intelligence

Gaia Fiscal Intelligence is the market-facing platform. GaiaFAAC remains the governed FAAC module inside it.

The active product goal is to become a trustworthy fiscal-intelligence infrastructure layer: a public discovery product, an institutional evidence network, a commercial data/API platform, and a machine-readable fiscal knowledge graph built on governed source provenance.

Homepage thesis:

> **Gaia knows where government money came from, where it went, what changed, and the evidence behind every number.**
>
> **Verified fiscal intelligence for governments, banks, investors, researchers and machines.**

The detailed Phase 9 architecture is documented in `docs/phase-9-fiscal-knowledge-graph.md`.

## What is already implemented

The repository currently includes substantial foundations for:

- governed publication of real, human-approved FAAC evidence;
- OAGF collection, PDF/Excel extraction and source retention;
- national FAAC/distribution evidence;
- state allocation evidence;
- OAGF Table IV local-government evidence with a fail-closed 774-jurisdiction gate;
- source registry, SHA-256 lineage and historical revision monitoring;
- deterministic validation and reconciliation findings;
- human review and four-eyes publication controls;
- state IGR evidence;
- Fiscal Claims, Proofs, States, Events and Certificates;
- Fiscal Pulse, Fiscal Watch and published analytics;
- Decision Packets;
- Fiscal Design scenarios;
- grounded Gaia Analyst functions;
- customer, entitlement, API-key and billing foundations;
- state financial-statement and liability-source discovery;
- immutable liability artifact archival and SHA-256 SourceDocument registration;
- deterministic state-liability extraction and governed approval staging.

Older milestone text that says these systems are future work is obsolete.

## Strategic product thesis

A fiscal-data application becomes defensible when it owns a trusted evidence graph rather than just a table of numbers.

Gaia should turn each important fiscal fact into a verifiable chain:

```text
claim
  -> primary source
  -> retained source bytes + SHA-256
  -> page/table/period semantics
  -> deterministic extraction
  -> validation/reconciliation
  -> human review
  -> publication event
  -> immutable proof/state
  -> derived intelligence
  -> alerts/API/workflow
```

Third-party fiscal websites may be used to benchmark usability, information architecture, search patterns and feature demand. They must not become canonical financial sources unless Gaia independently retains and verifies the underlying primary evidence.

## Phase 9 — Gaia Fiscal Knowledge Graph

### 9A — Source Universe

Build the authoritative source universe across OAGF, NBS, DMO, CBN, Finance Ministry, Budget Office, state budget/finance portals, Accountant-General portals, audited financial statements and other authoritative fiscal disclosures.

The state-financial discovery/archive work merged in PR #73 is the first Phase 9A tranche and the bridge into liabilities.

Source discovery is not publication. Authority checks, retention, hashing, semantics, validation and review remain mandatory.

### 9B — Liability Ledger

Continue the liability work already started. Govern explicitly reported:

- contractor arrears;
- pension and gratuity arrears;
- salary arrears;
- judgment obligations;
- guarantees/contingent liabilities where explicitly disclosed;
- other authoritative reported obligations.

Do not infer liabilities from debt, budget or expenditure movements.

### 9C — Economic Context

Add explicitly sourced economic context including inflation, food, transport, fuel/energy, electricity, GDP, employment, trade and relevant monetary/FX context.

Economic context must remain semantically separate from fiscal claims and must never fill missing fiscal evidence.

### 9D — Fiscal Event Graph

Make change over time a first-class machine-readable layer: publication, revision, supersession, debt changes, liability changes, budget changes, reconciliation changes and other deterministic fiscal evidence events.

Extend the existing `FiscalEvent` primitive rather than create a duplicate event store.

### 9E — State Twin

Build one continuously reconciled fiscal/economic representation for each state and the FCT.

The State Twin is a derived/materialized representation of governed graph state, not a competing database of truth. Extend the existing `FiscalState` primitive rather than duplicate it.

Every exposed value should remain traceable through claim -> evidence -> source -> hash.

### 9F — Fiscal Stress Lab

Build transparent, reproducible scenario analysis over observed state plus explicit assumptions.

Observed values, assumptions, modeled outputs, uncertainty and missing evidence must remain visibly distinct. Scenario output is not a credit rating or prediction of default.

### 9G — Gaia Questions

Provide natural-language fiscal research over governed evidence. Factual answers must attach evidence and expose conflicts/unavailable data rather than smooth them away.

### 9H — Africa Deployment

Deploy the same core evidence model to additional countries. Internationalization begins in schema discipline now; 9H is deployment, not redesign.

New domain concepts should be country-neutral where practical. Existing Nigeria-specific production contracts should be migrated incrementally through explicit compatibility layers rather than a destructive rewrite.

## Product layers

### 1. Public fiscal explorer

Make verified evidence extremely easy to discover:

- national FAAC overview;
- state and FCT pages;
- all local governments with state drill-down;
- monthly history and comparisons;
- component breakdowns where actually reported;
- IGR, debt, budget, expenditure and liability history where governed evidence exists;
- rankings and movers only over comparable published periods;
- evidence badges, source links and proof links beside figures;
- first-class search across jurisdictions, periods and fiscal domains;
- mobile-first tables/charts without hiding missing data.

### 2. Evidence network

Every public figure should be traceable and revision-aware:

- canonical source registry;
- independent corroborating evidence separated from canonical evidence;
- historical source versions;
- supersession and conflict records;
- source-page and table lineage;
- reconciliation status;
- portable Fiscal Proofs;
- point-in-time Fiscal States and Certificates;
- machine-readable evidence manifests.

### 3. Institutional intelligence

Build paid workflows that save analysts real time:

- jurisdiction watchlists;
- source revision alerts;
- new-evidence publication alerts;
- material movement alerts with deterministic explanations;
- evidence-quality and coverage alerts;
- state/LGA comparison workspaces;
- downloadable Decision Packets;
- licensed CSV/JSON/Excel exports;
- scheduled reports;
- team workspaces and saved research;
- institutional API and webhooks/event feeds when production-ready.

### 4. Fiscal knowledge graph

Expand domains only with authoritative sources, provenance, validators, review flows and clear publication rules.

The logical graph should be represented in PostgreSQL until measured traversal/query needs justify adding a specialized graph engine.

### 5. Grounded intelligence and simulation

Gaia Questions, Gaia Analyst and Fiscal Stress Lab should operate only on governed evidence and explicit assumptions.

Requirements:

- every factual answer must be traceable to published evidence;
- every scenario input must be displayed;
- observed values must be separated from assumptions and modeled values;
- uncertainty and unavailable evidence must survive through the answer;
- no corruption, misconduct, governance or credit claims may be inferred from allocation movements alone.

## Immediate engineering priorities

### P0 — Trust and correctness

1. Keep all documentation aligned with Phase 9 architecture.
2. Increase production PostgreSQL integration coverage for precision, migrations and publication constraints.
3. Add cross-level reconciliation where source semantics permit it: national -> state/FCT -> local government.
4. Harden source-authority rules and reconciliation status exposure in public/API responses.
5. Keep all collection/extraction paths unable to publish directly.
6. Expand fixtures for historically difficult source layouts and revisions.
7. Add invariant tests around four-eyes controls, supersession and conflict handling.

### P1 — Finish Phase 9A and advance 9B

1. Expand Source Universe registry to OAGF, NBS, DMO, CBN, Budget Office, Finance Ministry and authoritative state portals.
2. Complete governed liability publication from approved state-liability staging records into Fiscal Claims.
3. Preserve unreported obligations as unavailable rather than zero.
4. Add liability claim revision/conflict rules.
5. Expose liability evidence status through API before adding scoring.

### P2 — Discovery and institutional product

1. Unified search for states, FCT, LGAs, months, fiscal domains and evidence IDs.
2. Direct proof/source affordances beside every major number.
3. Saved watchlists and notification preferences.
4. Evidence revision timeline visible to users.
5. Stable commercial API contracts and export entitlements.
6. Decision Packets and certificate workflows suitable for diligence/research use.
7. Usage analytics, audit logs and enterprise administration.

### P3 — 9C/9D graph expansion

1. Introduce governed economic-context source/data dictionaries.
2. Extend FiscalEvent taxonomy and deterministic production rules.
3. Link events explicitly to claims/evidence.
4. Define country-neutral domain naming for new Phase 9 models.
5. Avoid broad `State` -> `Jurisdiction` rewrites until an actual cross-country tranche requires migration.

### P4 — 9E/9F/9G

1. Materialize State Twin from governed graph state.
2. Add coverage, conflict and freshness summaries.
3. Build transparent stress scenarios over State Twin inputs.
4. Ground Gaia Questions in published claims/evidence and return machine-readable identifiers.

## Non-negotiable assumptions

- PostgreSQL is the production system of record.
- Python and JavaScript runtimes remain environment/version controlled.
- Source documents require durable retention outside ephemeral application filesystems.
- Missing evidence remains unavailable, never zero-filled.
- Revisions do not erase historical source states.
- Third-party summaries are not silently promoted to canonical evidence.
- Publication is a governed transition, not a side effect of collection/extraction.
- The State Twin is derived from governed graph state, not an independent truth database.
- AI-generated output cannot upgrade evidence certainty.

## Primary risks

- government source documents change layout without notice;
- a document can be revised in place at the same URL;
- reporting periods can be semantically ambiguous;
- national/state/LGA aggregates may not be directly comparable because source scopes differ;
- rounded published figures can create apparent reconciliation differences;
- fiscal/economic domains can look related while representing different accounting semantics;
- premature internationalization can destabilize proven Nigeria-specific contracts;
- AI-generated explanations can overstate weak evidence;
- commercial pressure can incentivize premature scores or predictions.

The system should fail closed and expose uncertainty rather than smooth these risks away.

## Definition of done for a new fiscal capability

A capability is not complete merely because a page renders. It is complete when:

- authoritative source policy is documented;
- raw evidence is retained with SHA-256 lineage;
- jurisdiction, periods and units are explicit;
- extraction is deterministic or reviewable;
- validators exist;
- reconciliation behavior is documented;
- missing/conflicted evidence has explicit states;
- human review is enforced where required;
- publication authority is separate from ingestion;
- API and UI expose source/evidence status;
- tests cover happy, missing, conflicting and revised-source paths;
- revisions preserve historical reproducibility;
- derived intelligence never upgrades evidence certainty.
