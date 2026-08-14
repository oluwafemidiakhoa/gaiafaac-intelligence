# Evidence model

The normalized evidence layer around governed records includes:

- `FiscalClaim` answers what, where, when, value/unit/currency, source, extraction
  method, methodology, status, and prior claim.
- `EvidenceVerification` keeps source verification, arithmetic reconciliation,
  human review, and publication as separate assertions.
- `EvidenceManifest` stores canonical machine-readable payload and SHA-256.
- `FiscalProof` publishes one portable manifest for one claim.
- `FiscalState` groups claims without erasing unavailable domains.
- `EvidenceSource` snapshots publisher, document, jurisdiction, domain, cadence,
  retrieval, workflow, hash, and source-revision lineage.
- `ClaimRevision` records exact value deltas, percentage changes when the prior value
  is non-zero, materiality, and source-revision lineage without changing either claim.
- `EvidenceConflict` and `EvidenceConflictClaim` retain explicit unresolved
  disagreements and every participating value/source.
- `FiscalEvent` records a deterministic evidence lifecycle transition, its retained
  evidence IDs, status, severity, exact calculation inputs when applicable, and time.
- `FiscalCertificate` binds a point-in-time package to an immutable Fiscal State,
  proof IDs, canonical manifest, issuance timestamp, and SHA-256 integrity hash.

Evidence states are: `unavailable`, `detected`, `pending_extraction`, `extracted`,
`pending_verification`, `verified`, `partial`, `conflicting`, `superseded`, and
`rejected`.

Source authenticity means Gaia recorded an approved source with a matching document
hash. It does not mean cryptography establishes that the source's fiscal assertion is
true. Corrections create a new claim, proof, revision record, and Fiscal State. No
historical claim or manifest is rewritten.

Proof history is assembled only from retained retrieval, verification, publication,
and revision timestamps. A lifecycle step with no stored timestamp is omitted rather
than assigned an inferred time.
