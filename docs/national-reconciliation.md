# National FAAC reconciliation

GaiaFAAC treats national FAAC evidence as independent from the jurisdiction-allocation table. The source families can describe the same reporting period while carrying different claims, scopes, precision, authority, and document fingerprints.

## Source authority

National evidence is classified explicitly instead of treating every official publication as an OAGF communiqué.

- `canonical_national_evidence`: the canonical national source for the reported claims, such as a retained communiqué or equivalent primary national-distribution record.
- `official_national_summary_evidence`: an official summary that reports national values but is not the canonical underlying national artifact.
- `official_government_press_release`: an official government release that reports national values and must remain visibly distinct from canonical evidence.

Source authority is exposed separately as `canonical`, `official_secondary`, or `contextual`. Non-canonical evidence may report observed national facts, but it cannot claim that a missing canonical source is available.

## Governed workflow

1. Publish the jurisdiction ledger through the existing import, validation, human-review, and administrator-publication workflow.
2. Register a distinct national source artifact. Its SHA-256 fingerprint is retained independently from the jurisdiction source. A source already backing `StateAllocation` rows cannot be reused as national evidence.
3. Enter only values observed in that national source, with its explicit monetary unit.
4. Declare how the source treats 13% derivation: `separate`, `included_in_states`, or `not_reported`.
5. Declare `states_only_36` or `states_plus_fct_37` only when the source explicitly establishes that basis. GaiaFAAC does not guess this semantic distinction.
6. Run deterministic national component reconciliation and validation.
7. A reviewer may approve evidence with no ERROR/CRITICAL findings. An unknown states scope is a warning and leaves jurisdiction reconciliation `unavailable`; it does not erase otherwise valid observed national facts.
8. A different administrator publishes the national record. The same person cannot review and publish it.

Operational commands are exposed through `gaiafaac-national`:

```bash
gaiafaac-national import official-national-source.html \
  --reporting-period-id <UUID> \
  --source-organization "Federal Ministry of Information and National Orientation" \
  --reported-unit billion_naira \
  --net-distributable-amount <OBSERVED_VALUE> \
  --federal-amount <OBSERVED_VALUE> \
  --states-amount <OBSERVED_VALUE> \
  --local-governments-amount <OBSERVED_VALUE> \
  --derivation-amount <OBSERVED_VALUE> \
  --derivation-treatment separate \
  --source-type official_government_press_release \
  --source-authority official_secondary \
  --canonical-source-status missing
```

When a stronger canonical source exists, use the canonical source metadata instead. If the source explicitly establishes the states basis, declare it separately:

```bash
gaiafaac-national declare-states-scope <RUN_ID> --states-scope states_plus_fct_37
```

Then review and publish under four-eyes control:

```bash
gaiafaac-national approve <RUN_ID> --reviewer-id <REVIEWER_UUID>
gaiafaac-national publish <RUN_ID> --reviewer-id <ADMINISTRATOR_UUID>
```

The public read model is available at:

`GET /api/v1/published/national-distribution/latest`

and:

`GET /api/v1/published/national-distribution/history?limit=12`

## Evidence semantics

Source values are classified as `observed`. Arithmetic totals, variances, and reconciliation conclusions are `derived`. A material mismatch is `conflicted`. Missing values or undeclared source semantics remain `missing` / `unavailable`; GaiaFAAC does not infer them.

### Recipient-component reconciliation

National component reconciliation is independent from jurisdiction reconciliation.

When derivation is declared `separate`, GaiaFAAC compares:

`Federal Government + States + Local Governments + 13% Derivation`

against the observed distributable total.

When derivation is declared `included_in_states`, the derivation amount is not added a second time.

When the source treatment is `not_reported`, additive reconciliation remains unavailable instead of choosing an interpretation.

A successful component reconciliation means only that the national values reconcile arithmetically on the source's stated basis. It does not mean GaiaFAAC has reconciled the states aggregate against the jurisdiction ledger.

### Source-precision tolerance

Official sources can display a headline at a coarser precision than the component amounts. A headline written as `2551` billion is not treated as if the source reported `2551.000000000000` billion.

GaiaFAAC derives tolerance from the displayed source precision: half of the least precise reported quantum, with a minimum of one kobo. This permits only differences explainable by the source's own rounding. It does not alter, smooth, or estimate any financial value.

### Cross-source jurisdiction reconciliation

The official states aggregate is compared with the independently published jurisdiction ledger only after the source scope is explicitly established.

- `states_only_36`: sum the 36 states and exclude the FCT.
- `states_plus_fct_37`: sum all 36 states plus the FCT.

All records on the declared basis must have published net allocations. Incomplete coverage produces `incomplete`; an undeclared basis produces `unavailable`; a material difference produces `conflicted`.

An undeclared basis is not a publication blocker for otherwise valid national component evidence. The public response keeps the two conclusions separate so a record cannot be described as fully reconciled merely because its component arithmetic passes.

## Allocation-report boundary

An OAGF allocation report that already backs jurisdiction rows is not eligible to serve as independent national evidence for the same period. This prevents circular reconciliation.

A gross-allocation table must also not be mapped to `net_distributable_amount` merely because a sum can be calculated from its rows. The national-distribution importer requires that the distributable total be an observed claim in the distinct national source.

## Publication integrity

A reporting period may carry multiple official source documents. The public state-allocation overview resolves its source from the published `StateAllocation.source_document_id` values rather than selecting an arbitrary period-level source. This prevents a national source fingerprint from being incorrectly shown as the jurisdiction-table source.

Published national responses expose source type, source authority, canonical-source status, component reconciliation, and jurisdiction reconciliation separately.

## Release gate

National reconciliation changes are not merged until repository formatting, API lint and tests, web lint and type checks, web tests, and the production web build all pass on the current pull-request head.
