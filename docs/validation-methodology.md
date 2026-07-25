# Validation methodology

Milestone 3 validation fails closed: it preserves submitted text, records
findings, and never alters a value to make totals reconcile.

## Import checks

- The source must be a non-empty CSV no larger than 10 MiB.
- Required columns are `state`, `gross_total`, `total_deductions`,
  `net_allocation`, and `reported_unit`.
- Demo imports require both `DEMO DATA` in the period label and the literal
  `DEMO DATA - NOT REAL FAAC DATA` on every row.
- State values must match a canonical name, code, slug, common `State` suffix,
  or a small reviewed alias set. There is no fuzzy matching.
- Every non-blank monetary value requires an explicit supported unit.
- Invalid rows are skipped and represented by durable `IMPORT_*` findings.

## Reconciliation checks

The default absolute tolerance is ₦0.01 and can be supplied explicitly by
application code.

- Gross allocation minus total deductions must equal net allocation.
- Where components are present, component gross, deduction, and net sums must
  match their allocation totals.
- All 36 states and the FCT must be present exactly once.
- Allocation source IDs must match the extraction-run source.
- Where a national `states_amount` exists, it must match the sum of state net
  allocations.
- Revenue month, FAAC meeting date, and publication date are checked in their
  distinct chronological roles.
- Negative values produce warnings requiring human review.
- Absolute month-over-month movement above the configured ratio produces a
  statistical warning. It is not evidence of corruption or misconduct.

Errors and critical findings block approval. Warnings remain visible but may be
accepted by an authorized human reviewer.

## Approval

Approval re-runs validation. It requires:

1. An active user with reviewer or administrator role.
2. Every canonical state and the FCT.
3. No error or critical findings.
4. Every allocation to have passed automated validation.

Approval changes verification status to `human_verified`, records reviewer and
time, completes source processing, and writes an audit event. It never publishes
records.
