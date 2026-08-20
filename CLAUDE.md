# CLAUDE.md

This file is the operating doctrine for coding agents working in GaiaFAAC Intelligence.

## What this is now

GaiaFAAC Intelligence is an **independent, non-governmental Nigerian fiscal-intelligence and evidence infrastructure platform**. It is not an official government platform and must never imply otherwise.

The repository is no longer a demo-only Milestone 4 application. It now contains governed real-data publication, OAGF PDF/Excel extraction, state and local-government evidence, national FAAC evidence, revision monitoring, source reconciliation, human review and four-eyes publication controls, analytics, Fiscal Pulse, Fiscal Watch, Fiscal Proof, Fiscal State, certificates, Decision Packets, Fiscal Design, Gaia Analyst, customer/account foundations, billing foundations, and institutional evidence APIs.

Do not remove, bypass, or downgrade these systems because an older milestone document says they are future work. Treat the current implementation and the current roadmap in `docs/implementation-plan.md` as authoritative.

## Product direction

The product is being built as a **Fiscal Intelligence Operating System for Nigeria**: easy enough for citizens and media to explore, but trustworthy enough for banks, investors, governments, development institutions, auditors, researchers, and enterprise API customers.

The core competitive advantage is not simply displaying more FAAC numbers. It is proving every important number and preserving its history:

```text
source -> retained bytes -> SHA-256 -> extraction -> deterministic validation
       -> reconciliation -> human review -> four-eyes publication
       -> immutable evidence/proof/state -> analytics/intelligence -> API/workflow
```

Public usability may take inspiration from fiscal-data products, but GaiaFAAC must outperform them on provenance, reconciliation, revisions, uncertainty, auditability, and institutional workflows.

## Non-negotiable evidence rules

Violating these rules is a correctness defect:

- Never invent, interpolate, backfill, silently infer, or coerce a financial value or unit.
- Missing is not zero. Unavailable is a valid result.
- Keep allocation period, revenue month, FAAC/disbursement month, publication date, and collection time distinct.
- Keep gross, deductions, statutory components, VAT, derivation, net, and other reported components distinct.
- Use `Decimal` in Python and fixed-precision `NUMERIC` in PostgreSQL. Never use binary floating point for money.
- Preserve the original reported text/value, reported unit, source URL, source organization, source page/table, document version, and SHA-256 where available.
- Automated extraction and validation never establish factual verification and never publish directly.
- Human approval is mandatory for governed publication. Publication paths that implement four-eyes control must use a different approver and publisher.
- Demo, pending, rejected, conflicted, superseded, and unpublished records must not leak into verified public outputs.
- Conflicting source evidence is retained and flagged; do not rewrite it to make arithmetic appear clean.
- Statistical anomalies, rankings, movements, simulations, and forecasts are not corruption findings, credit ratings, governance scores, or default predictions.
- AI/natural-language answers must be assembled from governed data/functions and must expose evidence status and citations/lineage.

## Architecture

Monorepo:

```text
apps/web/             Next.js App Router institutional/public UX
apps/api/             FastAPI, governed pipelines, services and APIs
packages/shared-types shared TypeScript contracts
database/             Alembic migrations and database assets
docs/                 operating, architecture and methodology documentation
```

Primary data flow:

```text
official/public source
  -> collector/archive
  -> SHA-256 + source registry
  -> extractor/transformer
  -> deterministic validators + reconciliation findings
  -> review queue
  -> explicit approval
  -> four-eyes publication where required
  -> published service/API
  -> Fiscal Claim / Proof / State / Certificate
  -> analytics, monitoring, scenarios and grounded analyst workflows
```

Document processing must remain isolated from publication authority. A collector or extractor must never be able to make a record public by itself.

### Current evidence domains

Agents must assume these areas are active unless the code proves otherwise:

- State FAAC allocation evidence
- National FAAC/distribution evidence
- OAGF Table IV local-government evidence (fail closed unless the governed 774-jurisdiction completeness rule is satisfied)
- State IGR evidence
- Evidence-source registry and revisions
- Conflicts and reconciliation
- Fiscal Claims, Proofs, States, Events and Certificates
- Fiscal Pulse / Fiscal Watch
- Decision Packets
- Fiscal Design scenarios
- Gaia Analyst grounded questions
- Customer/API entitlement and commercial foundations

## Source hierarchy

Prefer canonical primary evidence whenever available. Secondary official sources may corroborate or temporarily fill a source-availability gap only when their authority, limitations, period semantics, and reconciliation status are explicit. Third-party fiscal websites are **benchmarks or discovery aids, not canonical financial evidence**, unless their underlying primary source is independently retained and verified by GaiaFAAC.

For FAAC, OAGF/Accountant-General source documents and other clearly authoritative government publications take precedence over third-party summaries. Never copy a third-party value into the canonical ledger merely because it looks plausible.

## Validation doctrine

Every important quantitative import should answer:

1. What exact document/page/table produced this value?
2. What unit and period semantics did the source actually report?
3. Does the record reconcile internally within source-derived precision?
4. Does the aggregate reconcile to lower-level governed evidence where comparable semantics exist?
5. Is coverage complete enough for the claim being made?
6. Has a human reviewed it?
7. Has publication authority been applied separately where required?
8. Can a downstream user verify the published artifact later?

If any answer is unknown, expose the uncertainty instead of manufacturing confidence.

## Commands

Run from repo root. Python 3.12+, Node 20.9+.

```bash
npm ci
python -m pip install -e "apps/api[dev,extraction]"
alembic upgrade head
```

Common CLIs include the main database/import CLI plus the governed national and local-government evidence CLIs defined in `apps/api/pyproject.toml`.

Full verification suite before handoff:

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

CI runs the corresponding web, API, and Docker configuration checks in `.github/workflows/ci.yml`.

## Engineering rules

- Web: Next.js App Router, TypeScript, Tailwind, shadcn/ui.
- API: FastAPI, Pydantic, SQLAlchemy 2, Alembic.
- Endpoints are versioned under `/api/v1`.
- Keep authorization checks in API/service code, not only middleware.
- Add tests with every behavior change.
- Schema changes require matching Alembic migrations.
- Preserve deterministic hashing/canonicalization compatibility for proof artifacts.
- Treat historical evidence objects as immutable unless the model explicitly represents revision/supersession.
- Do not commit secrets or uncontrolled source documents.

## Test fidelity warning

A substantial part of the API test suite uses SQLite in memory while production targets PostgreSQL. SQLite does not reproduce every PostgreSQL constraint or `NUMERIC` behavior. Precision-sensitive, concurrency-sensitive, migration-sensitive, locking, and publication-integrity changes should also be exercised against PostgreSQL before production deployment.

## Strategic build order

Do not chase novelty at the expense of evidence integrity. Prioritize:

1. Evidence coverage and correctness.
2. Reconciliation and revision intelligence.
3. Exceptional state/LGA/national discovery UX.
4. Institutional alerts, watchlists, APIs, exports and decision workflows.
5. Broader fiscal domains such as IGR, debt, expenditure, liabilities and budgets with the same provenance standard.
6. Grounded AI and scenario intelligence only over governed evidence.

The objective is a defensible Nigerian fiscal-data network, not a fragile dashboard with impressive-looking numbers.
