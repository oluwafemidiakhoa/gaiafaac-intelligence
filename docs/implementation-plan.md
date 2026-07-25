# Implementation plan

## Current scope: Milestone 4

Milestone 4 establishes:

1. A read-only, demo-constrained API for overview, states, comparisons, and sources.
2. A national-overview interface that identifies its three-row partial coverage.
3. State directory and detail pages with explicit unavailable values.
4. Two-to-six-state comparison without inferred data.
5. Safe source metadata and methodology pages.
6. Server-rendered loading failure states and demo labelling throughout.

Real-data publication, charts requiring historical data, rankings, analytics,
reports, authentication endpoints, administrative web interfaces, and AI answers
are not implemented in this milestone.

## Assumptions

- PostgreSQL 16 is the initial local and managed-database compatibility target.
- Python 3.12 and Node.js 20 are the minimum supported runtimes.
- The browser calls a public API base URL configured at build/deployment time.
- Raw documents will eventually live in durable object storage; local `data/` folders are development staging only.
- Data becomes publishable only after a separate explicit approval transition.

## Primary risks

- Source publications vary in format and may conflate revenue, meeting, and publication dates.
- Monetary units and OCR output can be ambiguous; the system must fail closed instead of silently inferring.
- Revisions and superseded documents require immutable lineage and versioning.
- A public AI interface could overstate incomplete data unless every answer is assembled from approved functions and carries citations and status.
- Frontend and container deployments have different networking models, so API URLs must remain environment-driven.

## Milestone sequence

1. Foundation (complete)
2. Schema, migrations, state seed, source registration, labelled demo dataset (complete)
3. Import, parsing, normalization, validation, and tests (complete)
4. Dashboards, state pages, comparison, sources, and methodology (current)
5. Analytics, reports, grounded Ask Gaia functions
6. Security hardening, end-to-end verification, deployment preparation

## Definition of done for Milestone 4

- Every read query is constrained to labelled demo records.
- Partial totals are never described as national totals.
- Missing state records render as unavailable rather than zero.
- Source responses omit internal storage paths.
- Pages work as Server Components with only semantic form controls requiring
  browser interaction.
- Runtime API responses are validated before rendering.
- Format, lint, type, unit-test, production-build, and Docker configuration checks pass.
