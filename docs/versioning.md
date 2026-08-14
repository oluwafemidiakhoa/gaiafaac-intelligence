# Versioning and immutability

Ledger objects retain `schema_version` and `methodology_version`. Manifests additionally
retain `manifest_version` and `canonicalization_version`.

- Schema changes follow semantic versioning.
- Methodology changes that can change values or status require a new methodology
  version and new object.
- Published claims, proofs, and Fiscal States are immutable in the application model.
- Corrections create new objects with `supersedes_gaia_id`,
  `previous_proof_gaia_id`, or `previous_state_id`.
- Historical reads select the latest Fiscal State whose `effective_at` is on or before
  the requested `as_of` timestamp.

Phase 2 publishes Fiscal State schema `1.1.0`, state manifest
`gaia-fiscal-state-manifest-v2`, ledger methodology `1.1.0`, coverage methodology
`gaia-evidence-coverage-v1`, and integrity methodology
`gaia-evidence-integrity-v1`. Fiscal Proof schema and manifest remain at `1.0.0` and
`gaia-fiscal-proof-manifest-v1`; their canonical payload and browser verification
semantics are unchanged. The verification endpoint continues to accept stored state
manifest v1 objects.

The initial migration does not backfill IDs because doing so without a reviewed
publication process could overstate legacy verification.

Phase 3 lifecycle events and certificates use schema and methodology `1.0.0`.
Certificate manifests use `gaia-fiscal-certificate-manifest-v1` and the unchanged
`gaia-canonical-json-v1` rules. Events and certificates are immutable application
records. A certificate ID is content-versioned from its jurisdiction, fiscal period,
Fiscal State hash, proof IDs, issuance time, and methodology; a later package creates
a new ID instead of replacing one.
