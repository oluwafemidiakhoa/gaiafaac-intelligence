# National FAAC reconciliation

GaiaFAAC treats an official national FAAC communique as evidence distinct from the jurisdiction-allocation table. The two source families can describe the same reporting period while carrying different claims, scopes, precision, and document fingerprints.

## Governed workflow

1. Publish the 36 states + FCT jurisdiction ledger through the existing import, validation, human-review, and administrator-publication workflow.
2. Register the official national-distribution document. Its SHA-256 fingerprint is retained independently from the jurisdiction source.
3. Enter only values observed in that document, with the document's explicit monetary unit.
4. Declare how the source treats 13% derivation: `separate`, `included_in_states`, or `not_reported`.
5. Declare whether the source's states aggregate means `states_only_36` or `states_plus_fct_37`. GaiaFAAC does not guess this semantic distinction.
6. Run deterministic reconciliation and validation.
7. A reviewer may approve only evidence with no ERROR/CRITICAL findings.
8. A different administrator publishes the national record. The same person cannot review and publish it.

Operational commands are exposed through `gaiafaac-national`:

```bash
gaiafaac-national import official-communique.pdf \
  --reporting-period-id <UUID> \
  --source-organization "Federal Ministry of Finance" \
  --reported-unit billion_naira \
  --net-distributable-amount <OBSERVED_VALUE> \
  --federal-amount <OBSERVED_VALUE> \
  --states-amount <OBSERVED_VALUE> \
  --local-governments-amount <OBSERVED_VALUE> \
  --derivation-amount <OBSERVED_VALUE> \
  --derivation-treatment separate

gaiafaac-national declare-states-scope <RUN_ID> --states-scope states_plus_fct_37
gaiafaac-national approve <RUN_ID> --reviewer-id <REVIEWER_UUID>
gaiafaac-national publish <RUN_ID> --reviewer-id <ADMINISTRATOR_UUID>
```

The public read model is available at:

`GET /api/v1/published/national-distribution/latest`

## Evidence semantics

Source values are classified as `observed`. Arithmetic totals, variances, and reconciliation conclusions are `derived`. A material mismatch is `conflicted`. Missing values or undeclared source semantics remain `missing` / `unavailable`; GaiaFAAC does not infer them.

### Recipient-component reconciliation

When derivation is declared `separate`, GaiaFAAC compares:

`Federal Government + States + Local Governments + 13% Derivation`

against the observed distributable total.

When derivation is declared `included_in_states`, the derivation amount is not added a second time.

When the source treatment is `not_reported`, additive reconciliation remains unavailable instead of choosing an interpretation.

### Source-precision tolerance

Official communiques can display a headline at a coarser precision than the component amounts. A headline written as `2551` billion is not treated as if the source reported `2551.000000000000` billion.

GaiaFAAC derives tolerance from the displayed source precision: half of the least precise reported quantum, with a minimum of one kobo. This permits only differences explainable by the source's own rounding. It does not alter, smooth, or estimate any financial value.

### Cross-source jurisdiction reconciliation

The official states aggregate is compared with the independently published jurisdiction ledger only after the source scope is explicitly declared.

- `states_only_36`: sum the 36 states and exclude the FCT.
- `states_plus_fct_37`: sum all 36 states plus the FCT.

All records on the declared basis must have published net allocations. Incomplete coverage produces `incomplete`; an undeclared basis produces `unavailable`; a material difference produces `conflicted`.

## Publication integrity

A reporting period may now carry multiple official source documents. The public state-allocation overview resolves its source from the published `StateAllocation.source_document_id` values rather than selecting an arbitrary period-level source. This prevents the national communique fingerprint from being incorrectly shown as the jurisdiction-table source.

## Release gate

National reconciliation changes are not merged until repository formatting, API lint and tests, web lint and type checks, web tests, and the production web build all pass on the current pull-request head.
