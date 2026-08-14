# Fiscal State

A `FiscalState` is Gaia's immutable, evidence-backed snapshot of one Nigerian
jurisdiction at a stated effective time. Its ID has the form
`GFS-{jurisdiction}-{YYYYMMDD}-{content suffix}`.

Each state stores:

- canonical jurisdiction identity and fiscal period;
- explicit domain states for FAAC, IGR, debt, debt service, budget, expenditure,
  and liabilities;
- claim Gaia IDs rather than copied or inferred values;
- source-document hashes;
- versioned Evidence Coverage and Evidence Integrity results with nullable components;
- schema and methodology versions;
- an immutable manifest hash and `previous_state_id`.

Missing domains are `unavailable`, never zero. Coverage is calculated from explicit
domain statuses under `gaia-evidence-coverage-v1`. Evidence Integrity is calculated
only when its documented minimum evidence exists; missing components remain
`insufficient_evidence`. New information creates a new Fiscal State; reads support
exact IDs and inclusive point-in-time `as_of` selection by date or timestamp.
