# Evidence model

Phase 1 introduces a compact normalized evidence layer around existing governed
records:

- `FiscalClaim` answers what, where, when, value/unit/currency, source, extraction
  method, methodology, status, and prior claim.
- `EvidenceVerification` keeps source verification, arithmetic reconciliation,
  human review, and publication as separate assertions.
- `EvidenceManifest` stores canonical machine-readable payload and SHA-256.
- `FiscalProof` publishes one portable manifest for one claim.
- `FiscalState` groups claims without erasing unavailable domains.

Evidence states are: `unavailable`, `detected`, `pending_extraction`, `extracted`,
`pending_verification`, `verified`, `partial`, `conflicting`, `superseded`, and
`rejected`.

Source authenticity means Gaia recorded an approved source with a matching document
hash. It does not mean cryptography establishes that the source's fiscal assertion is
true. Conflicts and revision workflows are Phase 2; the schema already retains
supersession references.
