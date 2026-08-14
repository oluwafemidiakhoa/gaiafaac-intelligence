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
- nullable evidence coverage and Evidence Integrity results;
- schema and methodology versions;
- an immutable manifest hash and `previous_state_id`.

Missing domains are `unavailable`, never zero. Phase 1 does not calculate evidence
coverage or Evidence Integrity, so both return `score: null` with
`status: insufficient_evidence`. New information creates a new Fiscal State; reads
support exact IDs and point-in-time `as_of` selection.
