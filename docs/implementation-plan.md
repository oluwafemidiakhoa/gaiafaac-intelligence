# Implementation plan

## Current direction: Fiscal Intelligence Operating System

GaiaFAAC has moved beyond the original demo milestones. The active goal is to become Nigeria's most trustworthy and useful fiscal-intelligence operating system: a public discovery product, an institutional evidence layer, and a commercial data/API platform built on governed source provenance.

The platform should be easier to explore than conventional fiscal-data portals while being materially stronger on source integrity, reconciliation, revisions, review controls, and reproducibility.

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
- customer, entitlement, API-key and billing foundations.

Older milestone text that says these systems are future work is obsolete.

## Strategic product thesis

A fiscal-data application becomes defensible when it owns a trusted evidence graph rather than just a table of numbers.

GaiaFAAC should turn each important fiscal fact into a verifiable chain:

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

Third-party fiscal websites may be used to benchmark usability, information architecture, search patterns and feature demand. They must not become canonical financial sources unless GaiaFAAC independently retains and verifies the underlying primary evidence.

## Product layers

### 1. Public fiscal explorer

Make verified evidence extremely easy to discover:

- national FAAC overview;
- state and FCT pages;
- all local governments with state drill-down;
- monthly history and comparisons;
- component breakdowns such as statutory allocation, VAT, deductions, derivation and ecology where actually reported;
- IGR history where governed evidence exists;
- rankings and movers only over comparable published periods;
- evidence badges, source links and proof links directly beside figures;
- first-class search across jurisdictions, periods and fiscal domains;
- mobile-first tables and charts without hiding missing data.

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
- new-month publication alerts;
- material movement alerts with deterministic explanations;
- evidence-quality and coverage alerts;
- state/LGA comparison workspaces;
- downloadable Decision Packets;
- licensed CSV/JSON/Excel exports;
- scheduled reports;
- team workspaces and saved research;
- institutional API and webhooks/event feeds when production-ready.

### 4. Broader fiscal graph

Expand beyond FAAC while preserving the same source standard:

- IGR;
- debt stock and debt service;
- expenditure and capital expenditure;
- budgets and outturns;
- liabilities/arrears where authoritative evidence exists;
- macro/context indicators used explicitly and separately from reported fiscal claims.

Do not create a composite fiscal-risk or credit score until the required governed evidence domains and methodology are sufficient. Component indicators may remain unavailable.

### 5. Grounded intelligence and simulation

Gaia Analyst and Fiscal Design should operate only on governed evidence and explicit assumptions.

Requirements:

- every factual answer must be traceable to published evidence;
- every scenario input must be displayed;
- observed values must be clearly separated from assumptions and modeled values;
- uncertainty and unavailable evidence must survive through the answer;
- no corruption, misconduct, governance or credit claims may be inferred from allocation movements alone.

## Immediate engineering priorities

### P0 — Trust and correctness

1. Keep all documentation aligned with current implementation.
2. Increase production PostgreSQL integration coverage for precision, migrations and publication constraints.
3. Add cross-level reconciliation where source semantics permit it: national -> state/FCT -> local government.
4. Harden source-authority rules and reconciliation status exposure in public/API responses.
5. Keep all collection and extraction paths unable to publish directly.
6. Expand fixtures for historically difficult OAGF layouts and source revisions.
7. Add invariant tests around four-eyes controls, supersession and conflict handling.

### P1 — Discovery and retention

1. Unified search for states, FCT, LGAs, months and evidence IDs.
2. Excellent LGA index and history UX.
3. National/state/LGA trend visualizations over verified comparable evidence.
4. Direct proof/source affordances beside every major number.
5. Saved watchlists and notification preferences.
6. Evidence revision timeline visible to users.

### P2 — Institutional product

1. Account/team workflows.
2. Saved jurisdictions and research collections.
3. Alerts for new evidence, revisions, conflicts and material movements.
4. Stable commercial API contracts and export entitlements.
5. Decision Packets and certificate workflows suitable for diligence/research use.
6. Usage analytics, audit logs and enterprise administration.

### P3 — Fiscal graph expansion

Add new domains only with authoritative sources, data dictionaries, provenance, validators, review flows and clear publication rules.

## Non-negotiable assumptions

- PostgreSQL is the production database target.
- Python and JavaScript runtimes remain environment/version controlled.
- Source documents require durable retention outside ephemeral application filesystems.
- Missing evidence remains unavailable, never zero-filled.
- Revisions do not erase historical source states.
- Third-party summaries are not silently promoted to canonical evidence.
- Publication is a governed transition, not a side effect of collection or extraction.

## Primary risks

- government source documents change layout without notice;
- a document can be revised in place at the same URL;
- reporting periods can be semantically ambiguous;
- national/state/LGA aggregates may not be directly comparable because source scopes differ;
- rounded published figures can create apparent reconciliation differences;
- AI-generated explanations can overstate weak evidence;
- commercial pressure can incentivize premature scores or predictions.

The system should fail closed and expose uncertainty rather than smooth these risks away.

## Definition of done for a new fiscal capability

A capability is not complete merely because a page renders. It is complete when:

- authoritative source policy is documented;
- raw evidence is retained with SHA-256 lineage;
- periods and units are explicit;
- extraction is deterministic or reviewable;
- validators exist;
- reconciliation behavior is documented;
- missing/conflicted evidence has explicit states;
- human review is enforced where required;
- publication authority is separate from ingestion;
- API and UI expose source/evidence status;
- tests cover happy, missing, conflicting and revised-source paths;
- derived intelligence never upgrades evidence certainty.
