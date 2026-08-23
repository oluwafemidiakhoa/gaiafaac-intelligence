# Phase 9 — Gaia Fiscal Knowledge Graph

## Product identity

**Gaia Fiscal Intelligence** is the market-facing platform.

**GaiaFAAC** remains the governed FAAC module and data product inside the platform.

Homepage thesis:

> **Gaia knows where government money came from, where it went, what changed, and the evidence behind every number.**
>
> **Verified fiscal intelligence for governments, banks, investors, researchers and machines.**

The objective is not to build another fiscal dashboard. The objective is to build a provenance-aware, machine-readable model of public finance in which important claims remain traceable to retained primary evidence.

## Architectural rule

The knowledge graph is the underlying truth layer.

State Twin, Fiscal Stress Lab, Gaia Questions, alerts, APIs and future machine interfaces are derived views or services over governed graph state. They must not create a second competing truth database.

Every published number must preserve the chain:

```text
number
  -> claim
  -> evidence location
  -> retained source document
  -> source authority
  -> SHA-256 lineage
  -> extraction
  -> validation/reconciliation
  -> human review where required
  -> publication state
  -> revisions/conflicts
```

Missing or conflicting evidence must survive into downstream products. It must never be silently converted to zero, guessed, or upgraded by a model.

## Phase 9 roadmap

### 9A — Source Universe

Establish a governed registry and collection boundary for authoritative Nigerian fiscal and economic evidence.

Priority source families:

- Office of the Accountant-General of the Federation (OAGF)
- National Bureau of Statistics (NBS)
- Debt Management Office (DMO)
- Central Bank of Nigeria (CBN)
- Federal Ministry of Finance
- Budget Office of the Federation
- state budget and finance portals
- state Accountant-General portals
- audited financial statements
- authoritative state debt, arrears and liability disclosures

Source discovery is not publication. A discovered URL or document becomes usable evidence only after authority checks, retention, hashing, period/unit semantics and the relevant validation/review path.

The state-financial source discovery, archive, extraction and approval work merged in PR #73 is the first tranche of 9A and the bridge into 9B.

### 9B — Liability Ledger

Represent explicitly reported obligations without inferring liabilities from unrelated fiscal movements.

Initial governed liability domains:

- contractor arrears
- pensions and gratuity arrears
- salary arrears
- judgment obligations
- guarantees and contingent liabilities where explicitly disclosed
- other reported domestic obligations

Each liability observation must retain fiscal period, amount semantics, currency/unit, source page/table, extraction method, verification status and publication state.

Debt, expenditure and liabilities must remain distinct concepts even when they are analytically related.

### 9C — Economic Context

Add contextual series that explain the environment in which fiscal events occur while keeping macroeconomic observations separate from reported fiscal claims.

Candidate domains include:

- CPI and headline inflation
- food inflation
- transport prices
- fuel/energy indicators
- electricity indicators
- GDP and sector output
- employment/labour indicators
- trade
- FX and monetary context where appropriate

Context may explain or condition analysis; it must not be used to fabricate missing fiscal evidence.

### 9D — Fiscal Event Graph

Promote change over time to a first-class machine-readable layer.

Examples include:

- new allocation published
- budget approved or revised
- debt stock changed
- liability disclosed or revised
- evidence source superseded
- official document revised in place
- reconciliation status changed
- claim superseded
- material deterministic movement detected

The existing `FiscalEvent` ledger model is the starting primitive. Phase 9D should extend event taxonomy and production rules rather than create a duplicate event store.

An event is evidence-linked and deterministic where possible. Statistical movement alone must never be described as corruption, misconduct, default or governance failure.

### 9E — State Twin

Build one continuously reconciled fiscal/economic representation for each state and the FCT.

The State Twin is a derived/materialized view of governed claims, evidence state, conflicts and events. It is not an independent source of truth.

A state twin may expose:

- FAAC
- IGR
- budget
- expenditure/outturn
- debt
- liabilities
- economic context
- recent fiscal events
- evidence coverage
- unresolved conflicts
- source freshness

The existing `FiscalState` ledger model is the starting primitive. Phase 9E should evolve its domain payload, versioning and materialization rules rather than create a separate twin table without a compelling migration reason.

Every displayed twin value must remain navigable back to evidence.

### 9F — Fiscal Stress Lab

Provide transparent scenario analysis over observed fiscal state plus explicit assumptions.

Rules:

- observed values and modeled assumptions must be visibly separated;
- scenario inputs must be inspectable;
- uncertainty must be retained;
- missing evidence must remain missing;
- results are scenarios, not credit ratings or predictions of default;
- methodology/version must be attached to reproducible outputs.

### 9G — Gaia Questions

Provide natural-language fiscal research over governed graph state.

Requirements:

- factual answers cite underlying evidence;
- claims distinguish observed, derived and modeled values;
- conflicts and unavailable evidence are surfaced;
- answers can return machine-readable claim/evidence identifiers;
- language models must not upgrade weak evidence certainty.

### 9H — Africa Deployment

Deploy the same evidence model to additional countries without redesigning the core system.

Potential deployments may include Ghana, Kenya and South Africa, but country selection is a product decision and not a schema assumption.

9H is an expansion phase, not the point at which internationalization begins.

## Country-independent core model

New Phase 9 concepts should be designed around portable public-finance entities:

```text
Country
Jurisdiction
GovernmentEntity
FiscalPeriod
RevenueObservation
Transfer
Budget
Expenditure
DebtPosition
Liability
EconomicIndicator
FiscalEvent
SourceDocument
EvidenceLocation
Claim
Revision
Conflict
```

Nigeria-specific concepts are specializations or source semantics:

```text
Transfer -> FAAC allocation
RevenueObservation -> IGR
Jurisdiction -> Nigerian State / FCT / LGA
GovernmentEntity -> OAGF / NBS / DMO / CBN / state authority
```

## Compatibility strategy

The repository currently has substantial Nigeria-specific production contracts, including the `State` model and many `state_id` foreign keys. Do not perform a broad rename or destructive rewrite merely to make the schema look international.

Instead:

1. keep current Nigerian APIs and governed data stable;
2. make new domain concepts country-neutral where practical;
3. introduce a generic jurisdiction abstraction through a dedicated, tested migration when cross-country implementation actually requires it;
4. provide compatibility mappings from existing `State` rows to the future jurisdiction model;
5. migrate one bounded domain at a time;
6. preserve identifiers, evidence lineage and historical reproducibility.

This avoids creating a premature cross-country abstraction while also preventing new Phase 9 work from hard-coding Nigeria unnecessarily.

## Graph semantics

The graph is logical first. PostgreSQL remains the production system of record unless an explicit architecture decision changes that.

A graph database is not required merely because the product uses graph semantics. Relationships can be represented through normalized PostgreSQL models, immutable ledger objects, manifests and derived materializations. A specialized graph engine should be introduced only when a measured query or traversal requirement justifies the operational complexity.

## Identity hierarchy

Market-facing hierarchy:

```text
Gaia Fiscal Intelligence
|
+-- GaiaFAAC
+-- GaiaIGR
+-- GaiaBudget
+-- GaiaExpenditure
+-- GaiaDebt
+-- GaiaLiabilities
+-- Gaia Economic Context
+-- Gaia Events
+-- Gaia State Twin
+-- Gaia Stress Lab
+-- Gaia Questions
```

Future country deployments should sit under Gaia Fiscal Intelligence rather than force a second company rename.

## Phase boundaries

Phase sequencing is architectural, not permission to pull all later features into current work.

- 9A may register/discover/archive evidence but must not silently publish downstream claims.
- 9B may publish liabilities only through explicit governed validation and approval.
- 9C context data must not be conflated with fiscal claims.
- 9D events must be evidence-linked and deterministic/reproducible.
- 9E twins must be materialized from governed graph state.
- 9F scenarios must expose assumptions.
- 9G answers must attach evidence.
- 9H must reuse the core schema instead of forking country-specific architectures.

## Definition of done for a Phase 9 domain

A new domain is not complete because an endpoint or page renders. It is complete when:

- authoritative source policy is documented;
- source bytes are durably retained where licensing/access permits;
- SHA-256 lineage is recorded;
- jurisdiction, period, units and semantic meaning are explicit;
- extraction is deterministic or reviewable;
- validators exist;
- reconciliation behavior is documented where meaningful;
- missing/conflicted/revised evidence has explicit states;
- human review is enforced where required;
- publication authority is separated from ingestion;
- API/UI expose evidence status;
- revisions preserve history;
- tests cover happy, missing, conflicting and revised-source paths;
- downstream intelligence cannot upgrade evidence certainty.
