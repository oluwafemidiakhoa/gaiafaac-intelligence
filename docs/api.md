# Fiscal Ledger API

All routes are versioned under `/api/v1` and appear in FastAPI OpenAPI documentation.

```text
GET  /api/v1/jurisdictions/{code}/state?as_of={ISO-8601}
GET  /api/v1/fiscal-states/{gaia_id}
GET  /api/v1/proofs/{gaia_id}
POST /api/v1/verify
```

Read responses contain `data`, `evidence`, and `meta`. `meta` includes schema and
methodology versions. Unknown objects return 404; they are not synthesized.

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
