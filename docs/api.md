# Fiscal Ledger API

All routes are versioned under `/api/v1` and appear in FastAPI OpenAPI documentation.

```text
GET  /api/v1/jurisdictions/{code}/state?as_of={ISO-8601}
GET  /api/v1/jurisdictions/{code}/evidence
GET  /api/v1/evidence-sources?jurisdiction={code}&publisher={name}&fiscal_domain={domain}
GET  /api/v1/fiscal-states/{gaia_id}
GET  /api/v1/proofs/{gaia_id}
POST /api/v1/verify
```

Read responses contain `data`, `evidence`, and `meta`. `meta` includes schema and
methodology versions. Unknown objects return 404; they are not synthesized.

`as_of` accepts either a timezone-aware ISO-8601 timestamp or an ISO date. A date is
inclusive through the end of that UTC day. Proof evidence includes revision and
conflict records. Source-registry results are capped at 200 records and expose no
internal storage path.

CLI verification example:

```bash
curl -X POST \
  -H 'Content-Type: application/json' \
  --data-binary @GF-FAAC-NG-LA-202606-A82F91.json \
  https://example.test/api/v1/verify
```

The response separates `artifact_integrity` from recorded source, reconciliation, and
human-review states. A mismatch is a normal 200 response with status `mismatch`; an
unsupported schema is a validation error.
