# GaiaFAAC Intelligence agent guide

## Scope

GaiaFAAC Intelligence is an independent Nigerian public-finance research platform. Follow the milestone order in `docs/implementation-plan.md`; do not pull later milestones into the current one without an explicit decision.

## Non-negotiable data rules

- Never invent or silently infer financial figures or monetary units.
- Keep revenue month, FAAC meeting date, and publication date distinct.
- Keep gross allocation, deductions, and net allocation distinct.
- Retain source-document lineage and verification status for every published figure.
- Use `Decimal` in Python and `NUMERIC` in PostgreSQL for money; never use floating point.
- Do not label data verified until validation and explicit approval have completed.
- Describe anomaly flags statistically, never as evidence of corruption or misconduct.
- Label forecasts as estimates and include uncertainty.

## Engineering conventions

- Web: Next.js App Router, TypeScript, Tailwind CSS, and shadcn/ui.
- API: FastAPI, Pydantic, SQLAlchemy 2, and Alembic.
- Use versioned endpoints under `/api/v1`.
- Add tests with every behavior change.
- Do not commit secrets, source documents, processed data, or generated reports.
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
