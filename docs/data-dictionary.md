# Milestone 3 data dictionary

All identifiers are UUIDs. Monetary values are `NUMERIC(24, 2)` and application
code uses `Decimal`. Timestamps are timezone-aware. Fields shown here summarize
the storage contract; the migration is authoritative.

| Entity | Purpose and key lineage |
| --- | --- |
| `states` | Canonical 36 states plus FCT: code, slug, zone, capital, and FCT marker. |
| `reporting_periods` | Distinct revenue month, FAAC meeting date, publication date, verification and publication state. |
| `source_documents` | Publisher, source URL, local/object path, file name, MIME type, SHA-256, version, dates, processing/source status, and supersession. |
| `national_distributions` | National gross, deductions, net distribution and government/component totals, tied to one period and source. |
| `state_allocations` | Per-state gross, deductions and net amounts, source, reported text/unit, confidence, and review metadata. |
| `state_allocation_components` | Typed components of a state allocation with reported text/unit and source page/table. |
| `state_indicators` | Sourced, period-specific numeric indicators with unit and methodology. |
| `extraction_runs` | Extractor identity/version, execution state, counts, configuration and errors. |
| `validation_results` | Rule outcome, severity, details and tolerance linked to a period or allocation. |
| `forecasts` | Method, training window, estimate and uncertainty interval; always identifiable as an estimate. |
| `generated_insights` | Generated narrative, methodology, model identity, grounding and approval state. |
| `organizations` | Tenant/account organization identity. |
| `users` | Organization membership, identity and role storage for future authorization behavior. |
| `subscriptions` | Organization plan and external billing references for future billing behavior. |
| `audit_logs` | Actor, action, entity, request metadata and structured change payload. |

## Publication safety

`reporting_periods`, `national_distributions`, `state_allocations`, `forecasts`,
and `generated_insights` carry explicit demo and publication fields. Each has a
database check preventing `is_demo=true` and `is_published=true` simultaneously.
No Milestone 3 command publishes a record.

Milestone 3 controlled imports begin as pending. Successful automated validation
sets records to `automatically_validated`, but the extraction run remains
`requires_review`. An active reviewer or administrator may move a clean import to
`human_verified`; this transition writes an `audit_logs` record and does not set
`is_published`.

The database intentionally does not require `gross - deductions = net`. Source
documents can be inconsistent, and Milestone 3 validators must preserve and flag
such records instead of making them impossible to store for review.
