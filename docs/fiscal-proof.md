# Gaia Fiscal Proof

A Fiscal Proof is a portable representation of one published fiscal claim. The
manifest version is `gaia-fiscal-proof-manifest-v1`, schema version `1.0.0`, and
canonicalization version `gaia-canonical-json-v1`.

The payload includes Gaia ID, jurisdiction, fiscal period, exact string value,
currency/unit, distinct fiscal dates, source URL/hash, methodology, publication time,
supersession, and separate verification states. The proof response also exposes
immutable revision records and any explicit source conflicts without changing the v1
manifest payload.

Proofs are available at `GET /api/v1/proofs/{gaia_id}` and
`/proofs/{gaia_id}`. The page exposes the manifest, source, hash, lineage, and browser
verification. `POST /api/v1/verify` supports independent command-line verification.

Successful SHA-256 verification proves that the canonical Gaia artifact matches its
embedded hash. It does not independently establish the truth of the government source.
The API and UI state that boundary explicitly.
