# Deploying GaiaFAAC Intelligence to Railway

This deploys the **labelled DEMO** build: two services (FastAPI API + Next.js web)
on Railway, both pointed at the existing **Neon** Postgres database. Everything the
public sees is stamped `DEMO DATA - NOT REAL FAAC DATA`. There is **no login/auth
yet** (that is a later cycle), so treat this as a public demo, not a real-data product.

## Prerequisites

- Railway CLI installed (verified: `railway 4.16.1`).
- A Railway account (the CLI signs you in / signs you up on first use).
- The Neon connection string. It is already in the gitignored `.env` as
  `DATABASE_URL` (format `postgresql+psycopg://…@…neon.tech/neondb?sslmode=require`).
  Copy that value when a step below says `<NEON_DATABASE_URL>`. **Do not commit it.**

## Architecture on Railway

```
Internet ──▶ web (Next.js)  ──server fetch──▶ api (FastAPI) ──▶ Neon Postgres
             public domain                     public + private     (external)
```

- **One project**, two services: `api` and `web`.
- Both build from the **repo root** using their own Dockerfiles
  (`apps/api/Dockerfile`, `apps/web/Dockerfile`) — the build context must be the repo
  root because each Dockerfile copies root paths (`alembic.ini`, `database/…`,
  `packages/…`). This is set per service with the `RAILWAY_DOCKERFILE_PATH` variable.
- The DB is **Neon**, not a Railway database — do not add a Railway Postgres.

## One-time build nuances (already handled / to set)

1. **API must listen on `$PORT`.** The API Dockerfile hardcodes `--port 8000`; Railway
   injects a dynamic `$PORT`. Override the API service **start command** to:
   ```
   uvicorn gaiafaac_api.main:app --host 0.0.0.0 --port $PORT
   ```
2. **Web is build-time-baked.** `NEXT_PUBLIC_API_URL` is inlined into the web bundle at
   **build** time (it is a Docker build ARG). So the API's public URL must exist
   **before** the web service builds. That dictates the order below (API first).

## Step-by-step

Run from the repo root. Replace `<...>` placeholders.

### 1. Sign in and create the project
```bash
railway login                      # opens your browser
railway init --name gaiafaac-intelligence
```

### 2. Create and configure the API service
```bash
railway add --service api
# point this service at the API Dockerfile, built from repo root:
railway variables set RAILWAY_DOCKERFILE_PATH=apps/api/Dockerfile --service api
# app config:
railway variables set DATABASE_URL='<NEON_DATABASE_URL>' --service api
railway variables set API_ENVIRONMENT=production --service api
```
Set the **start command** for the `api` service to
`uvicorn gaiafaac_api.main:app --host 0.0.0.0 --port $PORT`
(Railway dashboard → api service → Settings → Deploy → Custom Start Command, or via
a `railway.json` scoped to the service).

Deploy it, then give it a public domain:
```bash
railway up --service api --detach
railway domain --service api        # note the generated https URL -> <API_PUBLIC_URL>
```
Verify: open `<API_PUBLIC_URL>/api/v1/health` — expect `{"status":"ok",...}`.

### 3. Create and configure the web service
```bash
railway add --service web
railway variables set RAILWAY_DOCKERFILE_PATH=apps/web/Dockerfile --service web
# build-time + runtime API URL (public), and internal URL for server-side fetch:
railway variables set NEXT_PUBLIC_API_URL='<API_PUBLIC_URL>' --service web
railway variables set API_INTERNAL_URL='http://api.railway.internal:8000' --service web
```
> `NEXT_PUBLIC_API_URL` must also be available at **build** time. In the Railway
> dashboard set it as a **build variable** too (Settings → Build), or Railway will pass
> service variables as build args — confirm the built bundle points at `<API_PUBLIC_URL>`.

Deploy and expose it:
```bash
railway up --service web --detach
railway domain --service web        # -> <WEB_PUBLIC_URL>
```

### 4. Close the CORS loop
The API only allows browser origins it is told about. Point it at the web domain:
```bash
railway variables set API_CORS_ORIGINS='<WEB_PUBLIC_URL>' --service api
railway up --service api --detach   # redeploy api to pick up CORS
```
(The web app fetches the API **server-side**, so CORS is mostly defensive, but set it
correctly anyway.)

### 5. Database
The Neon database is **already migrated and seeded** (schema + 37 states + the 3-row
demo period) from local setup, so the demo pages work immediately. The analytics
dataset seed did **not** complete over the network — it is not required for the M4 demo
pages. If you later want it, re-run `gaiafaac-db seed-analytics-demo` against Neon
(ideally after it is changed to commit in batches — see Known limitations).

Optional: run migrations as a release step so future schema changes auto-apply — set the
api service **pre-deploy command** to `alembic upgrade head`.

## Verify the deployment

- `railway deployment list --json` → newest deployment `status` is `SUCCESS` for **both**
  services (a queued/streaming build is not a success).
- `<API_PUBLIC_URL>/api/v1/health` returns ok.
- `<WEB_PUBLIC_URL>` loads with the amber **DEMO DATA** banner; `/overview`, `/states`,
  `/compare`, `/sources`, `/methodology` render.

## Known limitations to fix before this is a *real* product (not blockers for a demo)

- **No authentication** — anyone can view; there is no admin. Fine for a demo, required
  before real data. (Import/auth cycles are in progress.)
- **Demo data only** — nothing real is published; the publish path isn't built yet.
- **`/docs` and `/redoc` are always on** regardless of `API_ENVIRONMENT` — consider
  gating them off in production.
- **Per-request DB engine** — `get_session()` builds a new SQLAlchemy engine per request;
  under real traffic this should become a single app-lifecycle engine + pooled sessions.
  Neon's pooled endpoint (already in the URL) mitigates but does not fix this.
- **Analytics seed is one big transaction** — it dropped over the network to Neon; make
  it commit in batches before relying on it in a hosted environment.
- Set a strong `API_SECRET_KEY` (used once auth lands) and rotate the Neon password if it
  was ever shared.

## Rollback / teardown

- Redeploy a previous release from the Railway dashboard (each service keeps deployment
  history).
- `railway down --service <name>` removes a service's current deployment.
