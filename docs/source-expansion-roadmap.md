# GaiaFAAC governed source expansion roadmap

GaiaFAAC should expand breadth without weakening its evidence standard. Every new source must enter the same governed chain: source discovery -> retained document or API response -> deterministic fingerprint -> extraction -> validation -> human review where required -> publication -> version history.

## Source authority tiers

### Tier A — canonical fiscal evidence

Use as primary financial truth when available.

- Office of the Accountant-General of the Federation (OAGF): FAAC allocation tables and related monthly evidence.
- Federal Ministry of Finance / FAAC communiques: national distribution totals and official meeting outcomes.
- Debt Management Office (DMO): federal and sub-national domestic/external debt stock.
- National Bureau of Statistics (NBS): IGR and official economic statistics.
- Central Bank of Nigeria (CBN): monetary and macro-financial context.
- Budget Office of the Federation and state budget authorities: appropriations, revenue and expenditure evidence.
- Nigeria Revenue Service / successor official tax authority publications: tax and federation revenue context.

### Tier B — authoritative external context

Use for benchmarking and explanatory context, never to silently replace a Nigerian canonical source.

- World Bank
- IMF

### Tier C — discovery sources

Use to detect events or locate primary records. Do not publish a canonical fiscal value solely from these sources when a Tier A source should exist.

- Government press releases that summarize an underlying primary record
- Reputable journalism
- Secondary data aggregators

## Evidence classes

Every published metric should expose one of these classes:

- `OBSERVED`: directly reported in retained source evidence.
- `DERIVED`: deterministic calculation over governed observed values.
- `ESTIMATED`: model- or assumption-based; never presented as observed fact.
- `CONFLICTED`: authoritative sources disagree beyond tolerance.
- `MISSING`: required evidence is unavailable.

## Delivery order

### Phase 1 — national FAAC reconciliation

Add a governed national-distribution record for each month:

- total distributable revenue
- Federal Government share
- states share
- LGA share
- 13% derivation
- source fingerprint and publication metadata

Reconcile the official states share against the sum of the 37 published jurisdiction records. A material variance blocks publication or creates an explicit `CONFLICTED` state.

### Phase 2 — DMO sub-national debt

Ingest DMO domestic and external debt publications for all 36 states and the FCT. Preserve document SHA-256, period, currency/unit, and source table/page when available.

Derived metrics after publication:

- debt / annual FAAC
- debt / IGR
- domestic vs external debt mix
- debt trend

### Phase 3 — NBS fiscal and economic evidence

Expand verified IGR coverage and add official state-level statistics needed for fiscal context. Keep each NBS publication independently versioned and fingerprinted.

### Phase 4 — CBN and World Bank context

Add macro context series such as inflation, FX and population/GDP benchmarks. Label these as contextual series and preserve upstream source identity and retrieval timestamp.

### Phase 5 — budgets and expenditure

Add governed budget, actual revenue and expenditure evidence where official machine-readable or document sources are available. Do not infer missing actuals from budgeted values.

## Commercial rule

Breadth alone is not the product. The paid value is the governed evidence layer: provenance, reconciliation, revision history, exports, API access and institutional workflow.

No pricing or product page may advertise a source family as available until that source is being ingested, validated and published through the governed pipeline.
