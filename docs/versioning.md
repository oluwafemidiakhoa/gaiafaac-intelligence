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

The initial migration does not backfill IDs because doing so without a reviewed
publication process could overstate legacy verification.
