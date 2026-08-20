# Fiscal Intelligence OS

## North star

Build the most trusted and useful operating system for Nigerian public-finance evidence.

GaiaFAAC should become the place where a user can move from a national fiscal headline to the exact state, local government, month, source document, page/table, revision history and proof artifact without losing provenance.

The ambition is larger than a dashboard. The product should support three markets from one evidence graph:

1. **Public intelligence** — citizens, journalists, researchers and civic users.
2. **Professional intelligence** — banks, investors, consultants, development institutions, legal/diligence teams and policy researchers.
3. **Government/institutional infrastructure** — evidence exchange, monitoring, audit trails, exports and APIs.

## Competitive posture

Many fiscal portals win on simplicity: searchable states/LGAs, rankings, history, IGR and alerts. GaiaFAAC should match that ease of use, then create a defensible moat through evidence integrity.

The differentiation is:

```text
other portal: number -> chart
GaiaFAAC:     number -> source -> hash -> extraction -> reconciliation
                    -> review -> revision history -> proof -> intelligence
```

A visually impressive but untraceable number is weaker than an unavailable value with a clear explanation.

## Core product primitives

### Jurisdiction graph

Every state, FCT and local government is a stable object with linked fiscal domains, evidence history, proofs, events, comparisons and watchlists.

### Evidence graph

Every governed value connects to:

- source authority;
- source URL;
- archived bytes/hash;
- fiscal period semantics;
- source page/table;
- reported text and normalized Decimal value;
- extraction run;
- validation/reconciliation findings;
- reviewer/publication events;
- revision/supersession/conflict lineage;
- proof/state/certificate identities.

### Time graph

Users should be able to ask "what did Gaia know on this date?" Point-in-time states and source revisions make historical truth reproducible.

### Alert graph

Events become customer subscriptions without becoming a second fiscal source of truth.

Implemented foundation:

- authenticated per-user state watchlists;
- persistent notification records with stable event keys;
- deterministic Fiscal Watch allocation signals;
- immutable Fiscal Event lifecycle signals, including source revisions, claim supersession, evidence status changes, conflicts and Fiscal State changes;
- read/unread state and durable alert history;
- evidence IDs and links back into governed proof/event surfaces;
- ownership isolation between customer accounts.

Next distribution layers:

- new verified publication notifications across additional fiscal domains;
- organization-shared watchlists and alert routing;
- email digests and immediate email delivery;
- signed webhooks / event feeds for API and enterprise customers;
- delivery attempts, retry policy and idempotency ledger;
- per-event-type and per-severity notification preferences.

### Decision graph

Institutional users should be able to turn governed evidence into saved comparisons, Decision Packets, downloadable evidence bundles, certificates, API feeds and team workflows.

## Billion-naira product wedges

### 1. Fiscal terminal for Nigeria

A fast search-first terminal for state/LGA fiscal evidence with professional tables, timelines, comparisons, filters, exports, saved views and provenance beside every number.

### 2. Revision intelligence

Government documents can change after publication. GaiaFAAC can make same-URL source revision detection and historical diffing a premium monitoring product.

### 3. Diligence API

Banks, investors, consultants and development institutions can consume verified fiscal evidence, proof manifests and evidence status programmatically instead of building fragile scraping pipelines.

### 4. Government evidence rooms

Generate verifiable point-in-time evidence packages for a state/LGA and period: source documents, hashes, claims, findings, approvals, proofs and certificates.

### 5. Fiscal watchlists

Teams follow jurisdictions and receive governed alerts when verified evidence changes. This creates recurring usage rather than one-off dashboard visits.

### 6. Cross-domain fiscal intelligence

Once FAAC + IGR + debt + expenditure + budgets are sufficiently governed, GaiaFAAC can support richer resilience, dependency, liquidity and fiscal-capacity analysis without pretending to be a credit-rating agency.

## AI doctrine

AI is an interface over the evidence graph, not the source of truth.

Gaia Analyst should:

- retrieve only eligible governed evidence;
- show which period/domain each claim uses;
- distinguish observed, derived and assumed values;
- cite proof/source identities;
- refuse conclusions unsupported by evidence;
- return unavailable when required evidence is absent;
- never convert statistical movement into allegations.

## Monetization ladder

### Free

Latest verified evidence, basic jurisdiction pages, limited comparisons, source/proof visibility.

### Analyst

Longer history, saved watchlists, persistent alerts, enhanced comparisons, exports and Decision Packets.

### Team

Shared workspaces, scheduled reports, evidence collections, admin/audit controls and higher export limits.

### API / Data

Versioned API, bulk licensed exports, event feeds, evidence manifests, higher rate limits and service commitments.

### Enterprise / Institutional

Custom data coverage, evidence rooms, procurement/security support, private workspaces and organization-specific monitoring.

## What not to do

- Do not optimize for page count before evidence coverage.
- Do not copy third-party fiscal values as canonical data.
- Do not create a mysterious black-box "fiscal score" prematurely.
- Do not hide conflicting sources.
- Do not let scheduled collectors publish autonomously.
- Do not let AI fill gaps.
- Do not treat rounded values as exact beyond their source precision.
- Do not sacrifice provenance for a prettier chart.

## Success metrics

Trust metrics:

- percentage of published claims with retained source bytes/hash;
- percentage with page/table lineage;
- reconciliation coverage;
- source-revision detection latency;
- unresolved conflict age;
- review/publication SLA;
- proof verification success.

Product metrics:

- returning jurisdiction-watchlist users;
- saved searches/comparisons;
- alert engagement and unread-to-read conversion;
- Decision Packet generation;
- institutional API active keys;
- export/API retention;
- conversion from public evidence pages to professional workflows.

## Build sequence

1. Make the evidence graph unbreakable.
2. Make state/LGA/national discovery exceptional.
3. Turn evidence changes into alerts/watchlists.
4. Add reliable outbound alert distribution and organization-level routing.
5. Turn research into saved institutional workflows and exports.
6. Expand authoritative fiscal domains.
7. Make AI the fastest way to query the governed graph.
8. Build enterprise distribution around the same verifiable evidence core.
