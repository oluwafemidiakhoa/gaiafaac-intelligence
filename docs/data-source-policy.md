# Data-source policy

GaiaFAAC accepts fiscal evidence only under an explicit source-authority and provenance model. This policy supersedes the old Milestone 3 CSV-only policy.

## Source classes

### Canonical primary evidence

Preferred for authoritative fiscal claims. Examples include directly published OAGF/Accountant-General documents and other government publications that clearly establish the reported values, period, and scope.

Canonical evidence should retain:

- source organization;
- source URL;
- exact original filename/object identity;
- durable archived bytes;
- SHA-256 checksum;
- MIME/content type;
- publication date where known;
- collection/import timestamp;
- reporting-period semantics;
- document version/revision status;
- source page/table where extraction permits it;
- processing, review and publication status.

### Official secondary evidence

Official government press releases, ministry pages, or other official summaries may corroborate a canonical source or temporarily provide national context when the canonical publication is unavailable.

They must remain distinguishable from canonical evidence. A secondary source must never silently replace a canonical source when the two conflict.

### Contextual / independent evidence

Third-party fiscal sites, research products, news reports, mirrors, and independent datasets may be useful for discovery, benchmarking, context, or conflict detection. They are not canonical financial evidence merely because their values appear credible.

A third-party value may enter a governed claim only if GaiaFAAC independently obtains and verifies the underlying source evidence or explicitly records the claim as non-canonical contextual evidence with its authority and limitations visible.

## Collection rules

- Prefer HTTPS and allowlisted/known authoritative hosts for automated official-source collectors.
- Retain the exact bytes used for extraction whenever technically and legally possible.
- Hash retained source bytes with SHA-256 before or at ingestion.
- A URL is not sufficient provenance because documents can change in place.
- Detect same-URL hash changes and treat them as source revisions requiring review.
- Never infer a missing reporting period, monetary unit, jurisdiction scope, or component meaning from surrounding months.
- If source semantics are ambiguous, quarantine or defer the candidate for review.

## Extraction and normalization

Automated extraction is an observation step, not verification.

- Preserve original strings beside normalized `Decimal` values.
- Preserve source page/table information when available.
- Use explicit unit-aware parsing.
- Do not use fuzzy matching to manufacture jurisdiction identity where authoritative mapping is uncertain.
- PDF/Excel/table extractors must fail closed when expected structure or governed coverage cannot be established.
- For OAGF Table IV LGA evidence, publication requires the governed completeness rule expected by the implementation; incomplete/ambiguous extraction remains review-only.

## Reconciliation

Where source semantics permit comparison, deterministic reconciliation should be recorded rather than hidden.

Examples include:

- national distributable total versus reported national components;
- gross minus deductions versus net where all three are actually comparable;
- national/state/FCT aggregates versus jurisdiction-level evidence when scopes and periods align;
- state totals versus LGA aggregates only where the source definitions support that relationship.

Rounded official figures may reconcile only within source-derived reporting precision. Tolerance must come from the source precision/methodology, not from an arbitrary value chosen to force agreement.

A mismatch is retained as evidence and a finding. It is not silently corrected.

## Human governance

Source registration, collection, extraction, validation, and reconciliation do not establish factual verification.

Only an explicit authorized review transition may mark governed records human-verified. Publication is a separate transition and must respect four-eyes controls where implemented.

Demo, rejected, superseded, conflicted, pending, or unpublished records must not be surfaced as verified live evidence.

## Revision policy

Historical revisions are first-class evidence events.

When an authoritative source changes:

1. retain the previous archived bytes and hash;
2. archive the new bytes and hash;
3. record revision/supersession lineage;
4. re-extract and validate under the current governed workflow;
5. require human review before a revised claim changes public truth;
6. preserve the ability to reconstruct prior point-in-time states.

## Benchmarking external fiscal products

External fiscal-data products may inform UX, search, navigation, feature prioritization, and discovery. GaiaFAAC must not copy their financial values into canonical datasets without primary-source verification.

The product objective is not to have the largest number of rows. It is to make every material published row independently auditable.
