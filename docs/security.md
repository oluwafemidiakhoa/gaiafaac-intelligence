# Fiscal Ledger security

Phase 1 security boundaries:

- Public ledger endpoints are read-only except deterministic `/verify`, which does not
  write or fetch remote URLs.
- Ledger materialization remains a service-layer operation over already-published,
  non-demo records; no public creation endpoint exists.
- SQLAlchemy parameterization and Pydantic response/request validation are retained.
- Manifests exclude storage paths, API keys, reviewer identities, and secrets.
- Browser verification reads local files without uploading them.
- Source links are evidence references, not instructions for the API to fetch content.
- Published objects are guarded against update/delete in the application model.

Future ingestion changes must separately review SSRF protections, source URL allowlists,
file-size limits, rate limiting, conflict authorization, and database-level immutability
enforcement. Cryptographic integrity must never be presented as proof that source data
is substantively true.
