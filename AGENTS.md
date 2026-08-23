# Gaia Fiscal Intelligence agent guide

## Scope

Gaia Fiscal Intelligence is an independent public-finance research platform. **GaiaFAAC** is the governed FAAC module inside the broader platform.

Follow the milestone order in `docs/implementation-plan.md` and the Phase 9 architecture in `docs/phase-9-fiscal-knowledge-graph.md`; do not pull later milestones into the current one without an explicit decision.

The knowledge graph is the underlying truth layer. State Twin, Fiscal Stress Lab, Gaia Questions, alerts and APIs are derived views/services over governed evidence and must not create competing truth stores.

## Non-negotiable data rules

- Never invent or silently infer financial figures or monetary units.
- Keep revenue month, FAAC meeting date and publication date distinct.
- Keep gross allocation, deductions and net allocation distinct.
- Keep debt, expenditure, liabilities and economic context semantically distinct.
- Retain source-document lineage and verification status for every published figure.
- Use `Decimal` in Python and `NUMERIC` in PostgreSQL for money; never use floating point.
- Do not label data verified until validation and explicit approval have completed.
- Missing evidence remains unavailable; never zero-fill or model it into an observed claim.
- Describe anomaly flags statistically, never as evidence of corruption or misconduct.
- Label forecasts/scenarios as estimates and include uncertainty.
- AI-generated output must not upgrade source certainty.

## Phase 9 design rules

- Make new fiscal-domain concepts country-neutral where practical.
- Do not perform a broad destructive `State` -> `Jurisdiction` rewrite merely for future internationalization.
- Extend existing `FiscalEvent` and `FiscalState` primitives before creating duplicate event/twin stores.
- A State Twin is derived/materialized from governed graph state.
- Economic context can condition analysis but cannot fabricate missing fiscal evidence.
- Africa expansion must reuse the core evidence model rather than fork country architectures.
- PostgreSQL remains the production system of record unless a measured requirement justifies another persistence engine.

## Engineering conventions

- Web: Next.js App Router, TypeScript, Tailwind CSS and shadcn/ui.
- API: FastAPI, Pydantic, SQLAlchemy 2 and Alembic.
- Use versioned endpoints under `/api/v1`.
- Add tests with every behavior change.
- Do not commit secrets, source documents, processed data or generated reports.
- Keep administrative authorization checks in the API handler/service layer, not only in middleware.

## Verification

Run before handing off changes:

```bash
npm run format
npm run lint
npm run typecheck
npm run test
python -m ruff format --check apps/api
python -m ruff check apps/api
python -m pytest apps/api/tests
npm run build
npm run docker:config
```
