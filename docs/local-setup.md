# Local setup

Copy `.env.example` to `.env` and replace the example database password. Do not commit `.env`.

Run the complete stack:

```bash
docker compose up --build
```

Apply the database migration and canonical reference seed:

```bash
alembic upgrade head
gaiafaac-db seed-states
```

For local source registration, place the document in the git-ignored `data/raw`
directory and record its metadata:

```bash
gaiafaac-db register-source data/raw/example.pdf \
  --source-organization "Source organization" \
  --publication-date 2026-07-01
```

Registration stores the resolved path and SHA-256 checksum. It does not copy the
file, so the referenced file must remain available to later pipeline stages.

The optional demo seed is synthetic and never publishable:

```bash
gaiafaac-db seed-demo
```

The Milestone 4 interface requires this demo seed. After loading it, open:

- `http://localhost:3000/overview`
- `http://localhost:3000/states`
- `http://localhost:3000/compare`
- `http://localhost:3000/sources`
- `http://localhost:3000/methodology`

Server Components use `API_INTERNAL_URL` when provided. Docker Compose defaults
it to `http://api:8000`; browsers continue to use `NEXT_PUBLIC_API_URL`.

## Controlled imports

The reviewed CSV contract requires these headers:

```text
state,gross_total,total_deductions,net_allocation,reported_unit
```

`extraction_confidence` is optional. Accepted units are `naira`,
`thousand_naira`, `million_naira`, and `billion_naira` plus documented aliases
such as `NGN` and `million naira`.

```bash
gaiafaac-db import-allocations data/raw/reviewed.csv \
  --source-organization "Source organization" \
  --revenue-month 2026-01-01 \
  --faac-meeting-date 2026-02-01 \
  --publication-date 2026-02-02 \
  --reporting-label "January 2026 allocation"
```

The command returns a run UUID and finding counts. After reviewing the source and
findings, use an existing active reviewer or administrator UUID:

```bash
gaiafaac-db validate-import RUN_UUID
gaiafaac-db approve-import RUN_UUID --reviewer-id USER_UUID
```

Approval produces human-verified, unpublished records. Use `reject-import` with
a non-empty reason when the source or extraction must be corrected.

Rollback the current schema only when you intentionally want to remove all
Milestone 2 tables:

```bash
alembic downgrade base
```

Validate the Compose model without starting services:

```bash
docker compose config --quiet
```

The Compose network uses `db` as the PostgreSQL hostname. When running the API directly on the host, set the database hostname to `localhost`.
Published development ports bind to `127.0.0.1` and are not exposed to other machines.

Stop services without deleting the database volume:

```bash
docker compose down
```

To run checks locally, follow the quality-check commands in the root README.
