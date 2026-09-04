# Watch Contract outbound delivery

Gaia Watch Contracts create governed operational reviews when a persisted organization alert matches a declared monitoring mandate. Outbound delivery extends that existing review record; it does not create a second monitoring truth source.

## Delivery sequence

1. A governed organization alert matches a Fiscal Watch Contract.
2. Gaia persists the immutable Watch Contract match.
3. Gaia opens one organization-scoped operational review and records the in-app delivery.
4. The outbound delivery runner materializes eligible email and webhook destinations exactly once per review/destination.
5. Network attempts are recorded in an append-only attempt ledger.
6. Failed network attempts retry on the declared schedule and eventually dead-letter at the configured attempt limit.
7. Operational acknowledgement/resolution does **not** clear the linked Decision Room evidence review. A successor Fiscal Receipt is still required to record the institutional evidence re-review.

## Email eligibility

Watch email is not a blanket organization broadcast. A user receives a Watch email only when all of these remain true at delivery time:

- the user is active;
- the user is a current member of the organization;
- the user explicitly enabled customer alert email;
- the user opted to include Fiscal Watch notifications;
- the Watch operational review was created on or after the user's `email_enabled_at` boundary; and
- operator SMTP delivery is enabled and fully configured.

Gaia does not backfill Watch email for reviews that predate the user's explicit email opt-in.

The Watch runner reuses the existing SMTP settings:

- `CUSTOMER_ALERT_EMAIL_ENABLED`
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `ALERT_FROM`
- `CUSTOMER_APP_URL`

No new email credential family is introduced by this feature.

## Institutional webhook eligibility

Watch Contract webhook delivery reuses the existing organization webhook endpoint and signing infrastructure. A Watch review is materialized for an endpoint only when:

- the organization currently has API entitlement;
- the endpoint is enabled;
- the endpoint was created before the Watch review;
- the endpoint subscribes to the governed alert's underlying event type; and
- the endpoint's jurisdiction filter is empty or contains the alert jurisdiction.

The webhook payload uses schema `gaia-watch-contract-webhook-v1` and event type `watch_contract_match`. Endpoint routing still uses the underlying governed event type such as `source_revised`, so existing endpoint subscriptions remain explicit and understandable.

Outbound Watch webhooks reuse the existing institutional controls:

- HTTPS-only endpoints;
- public-network DNS validation / SSRF protection;
- organization ownership and API entitlement;
- derived HMAC-SHA256 signing secrets;
- delivery ID and timestamp headers; and
- the existing institutional webhook operator switches:
  - `INSTITUTIONAL_WEBHOOK_ENABLED`
  - `INSTITUTIONAL_WEBHOOK_MASTER_SECRET`

Headers sent with Watch webhooks include:

- `Gaia-Webhook-Id`
- `Gaia-Webhook-Timestamp`
- `Gaia-Webhook-Signature`
- `Gaia-Webhook-Schema: gaia-watch-contract-webhook-v1`

## Delivery states and retry policy

Outbound Watch delivery records are durable. Supported states are:

- `pending`
- `delivered`
- `retrying`
- `dead_letter`
- `deferred`
- `failed`

`deferred` is used when delivery should not be attempted because the operator integration is disabled/incomplete, the recipient is no longer eligible, the endpoint is disabled/missing, or API entitlement is no longer present. A deferred delivery can be reconsidered by a later runner invocation after the blocking condition is corrected.

Network failures retry on this schedule:

1. 5 minutes
2. 30 minutes
3. 2 hours
4. 12 hours
5. 24 hours

The default maximum is five actual network attempts. Once the limit is reached the delivery becomes `dead_letter` until an operator/customer action creates a future recovery mechanism; Gaia does not silently mark it delivered.

## Audit evidence

Each outbound destination has one durable `fiscal_watch_contract_deliveries` row identified by the review, channel and destination key. The row stores current delivery state, destination, attempt count, retry time, response metadata, last error, payload SHA-256 and the canonical payload.

Each actual network attempt is separately written to `fiscal_watch_contract_delivery_attempts` with:

- attempt number;
- attempted timestamp;
- response status;
- response excerpt; and
- error text.

Attempt rows are append-only at the ORM boundary and are never rewritten as the delivery progresses.

The customer Watch workspace exposes the delivery channel, destination, current state, attempt count, next retry, last error, payload SHA-256 and attempt history.

## Running delivery

Organization owners/admins can trigger an organization-scoped delivery pass from the Watch Contracts workspace. This is useful for immediate handling and testing, but production should also run the worker independently so delivery does not depend on a browser session.

Production CLI:

```bash
python -m gaiafaac_api.watch_contract_delivery_cli
```

Optional controls:

```bash
python -m gaiafaac_api.watch_contract_delivery_cli --max-attempts 5 --max-deliveries 500
```

For Railway, configure a dedicated cron/service invocation using that command and the same production API/database/integration environment variables. This repository provides the idempotent runner; creating or changing the Railway schedule is an operator deployment action and is not claimed by the code merge itself.

## Separation of duties

Outbound delivery is notification evidence, not evidence approval. A delivered email or webhook does not:

- approve the matched fiscal evidence;
- resolve the publication Review queue;
- certify a lending/investment/procurement decision;
- clear `DecisionRoom.review_required`; or
- create a successor Fiscal Receipt.

The evidence-review loop closes only when the institution performs the Decision Review and issues the successor Fiscal Receipt that records the new evidence boundary and predecessor lineage.
