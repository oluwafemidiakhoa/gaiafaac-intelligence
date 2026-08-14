# Fiscal Ledger Phase 1 implementation map

## Existing architecture reused

- Jurisdictions: `database/models.py::State`
- Fiscal periods and distinct dates: `ReportingPeriod`
- Source registry and SHA-256: `SourceDocument`
- Exact published FAAC values: `StateAllocation`
- Approval/publication boundary: `pipeline/approval.py`
- Legacy proof compatibility: `services/fiscal_proof.py` and
  `/api/v1/published/fiscal-proof/{state_slug}/{revenue_month}`
- Browser manifest compatibility: `fiscal-design-manifest-verifier.ts`

## Phase 1 file map

1. Canonical JSON and Gaia IDs: `apps/api/src/gaiafaac_api/ledger/`
2. Evidence lifecycle: `database/enums.py::EvidenceStatus`
3. Durable objects: `database/ledger_models.py`
4. API schemas: `fiscal_ledger_schemas.py`
5. Materialization and historical reads: `services/fiscal_ledger.py`
6. Public endpoints: `api/v1/routes/fiscal_ledger.py`
7. Migration: `20260814_0006_add_fiscal_ledger_foundation.py`
8. Web proof client: `apps/web/src/lib/fiscal-ledger-api.ts`
9. Proof page and download: `apps/web/src/app/proofs/[gaiaId]/`
10. Dual-format browser verification: existing `/fiscal-design/verify`

## Release boundary

The schema migration is intentionally empty of data. A separate reviewed operational
change must materialize existing published allocations. This avoids relabeling legacy
records as ledger-verified without explicit approval.
