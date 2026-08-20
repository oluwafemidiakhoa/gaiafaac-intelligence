# Institutional Webhooks

Gaia institutional webhooks deliver deterministic Fiscal Event records to external organization systems without changing the underlying fiscal evidence ledger.

They are infrastructure for API-plan organizations. They are not a separate source of fiscal truth, a credit-rating feed, a corruption signal or a prediction service.

## Access and operating model

- Webhook configuration is organization-scoped.
- Only organization owners and administrators may create, rotate, enable or disable endpoints.
- The organization must currently have the `api_access` entitlement.
- Entitlement is checked again by the delivery worker before events are queued or sent.
- Creating an endpoint starts a subscription from the endpoint creation time. Gaia does not automatically replay older Fiscal Events.
- Disabling an endpoint stops delivery. Re-enabling it allows eligible deferred deliveries to resume.
- Global outbound delivery is independently controlled by `INSTITUTIONAL_WEBHOOK_ENABLED`; it defaults to `false`.

## Supported Fiscal Event classes

The webhook source is Gaia's immutable `fiscal_events` ledger. Supported event types are:

- `new_source_detected`
- `source_revised`
- `claim_superseded`
- `evidence_upgraded`
- `evidence_downgraded`
- `cross_source_conflict`
- `fiscal_state_changed`
- `faac_spike`
- `faac_decline`

An endpoint may subscribe to one or more event types and optionally restrict delivery to specific state/FCT codes. Leaving the jurisdiction list empty means all jurisdictions.

## Endpoint restrictions

Gaia treats webhook URLs as an outbound-network security boundary.

Endpoints must:

- use `https://`;
- use port 443;
- use a hostname rather than an IP literal;
- resolve only to globally routable addresses;
- contain no embedded username/password;
- contain no URL fragment;
- contain no spaces or control characters.

Gaia resolves the hostname, rejects the destination if any resolved address is non-public, then connects directly to the validated public IP while preserving the original hostname for TLS SNI and certificate verification. Redirect responses are not followed.

These controls are intended to reduce SSRF and DNS-rebinding exposure. A destination is revalidated on every actual delivery attempt.

## Signing secrets

`INSTITUTIONAL_WEBHOOK_MASTER_SECRET` is operator key material. Use a unique, high-entropy production value of at least 32 characters and keep it stable after webhook delivery is activated.

Gaia does not store plaintext endpoint signing secrets. An endpoint secret is deterministically derived from:

- the operator master secret;
- the endpoint ID;
- a random per-endpoint salt;
- the endpoint secret version.

The derived secret is returned only when the endpoint is created or explicitly rotated. Store that returned `gwhsec_...` secret in the receiving system's secret manager.

Per-endpoint secret rotation increments the secret version. Pending, retrying and deferred deliveries switch to the newly rotated endpoint secret. Already delivered records remain historical.

Changing the operator master secret changes every derived endpoint secret and therefore requires coordinated receiver rotation. Do not rotate it casually.

## Request headers

Every network delivery includes:

```text
Gaia-Webhook-Id: <delivery UUID>
Gaia-Webhook-Timestamp: <unix seconds>
Gaia-Webhook-Signature: v1=<hex HMAC-SHA256>
Gaia-Webhook-Secret-Version: <integer>
Gaia-Webhook-Event: <event type>
Content-Type: application/json; charset=utf-8
```

## Signature verification

Gaia signs the exact canonical request body.

Construct the signed message as:

```text
<timestamp>.<delivery-id>.<exact-request-body>
```

Then compute:

```text
HMAC-SHA256(endpoint_signing_secret, signed_message)
```

Compare the hex digest with the value after `v1=` in `Gaia-Webhook-Signature` using a constant-time comparison.

Receiver requirements should include all of the following:

1. Verify the signature before parsing or acting on the payload.
2. Reject timestamps outside a small acceptance window. Five minutes is a reasonable default.
3. Persist `Gaia-Webhook-Id` and reject a repeated delivery ID after a successful processing decision.
4. Keep the old secret only for the minimum overlap required during a deliberate rotation.
5. Return a 2xx response only after the event has been accepted idempotently.

## Payload

Webhook payloads use Gaia canonical JSON and are fingerprinted before delivery.

Example shape:

```json
{
  "created_at": "2026-08-19T18:30:00Z",
  "data": {
    "calculation": {},
    "detected_at": "2026-08-19T18:30:00Z",
    "effective_at": "2026-08-19T18:30:00Z",
    "event_id": "GFE-NG-LA-20260819-ABC123",
    "event_type": "source_revised",
    "evidence_ids": ["..."],
    "evidence_status": "verified",
    "explanation": "A revised source document was retained.",
    "fiscal_state_id": null,
    "jurisdiction": {
      "code": "NG-LA",
      "name": "Lagos"
    },
    "methodology_version": "1.0.0",
    "severity": "material"
  },
  "id": "<delivery UUID>",
  "meta": {
    "meaning": "Deterministic fiscal evidence lifecycle event. No causal, misconduct, credit, solvency, or predictive inference is implied.",
    "schema_version": "gaia-fiscal-webhook-v1"
  },
  "type": "source_revised"
}
```

The persisted delivery row records `payload_sha256`. The worker recomputes the canonical SHA-256 before every send. An integrity mismatch moves the delivery to `dead_letter` without making an outbound request.

## Delivery lifecycle

Delivery states are:

- `pending` — materialized but not attempted;
- `retrying` — a network attempt failed or returned non-2xx;
- `delivered` — a 2xx response was received;
- `dead_letter` — integrity failed or the maximum attempt count was reached;
- `deferred` — delivery cannot currently proceed, for example because the operator gate is disabled, the endpoint is disabled or the organization no longer has API entitlement.

Default retry delays are approximately:

```text
5 minutes -> 30 minutes -> 2 hours -> 12 hours -> 24 hours
```

Successful deliveries are not resent. A unique database constraint on `(endpoint_id, fiscal_event_id)` makes event materialization idempotent for each endpoint.

## Attempt audit history

The delivery table stores the current aggregate state. Every actual outbound network attempt also appends an immutable-style attempt record containing:

- attempt number;
- attempt timestamp;
- HTTP response status, when available;
- up to 1,000 characters of response-body excerpt;
- delivery error, when applicable.

Deferred states that make no network request do not increment the attempt counter and do not create attempt records.

Organization administrators can inspect delivery history through the customer API, including:

```text
GET /api/v1/account/webhooks/deliveries
GET /api/v1/account/webhooks/deliveries/{delivery_id}/attempts
```

Receiver response excerpts may contain receiver-provided content and should therefore be treated as operational audit data rather than public evidence.

## Worker

The delivery worker is registered as:

```text
gaiafaac-webhooks
```

Example:

```text
gaiafaac-webhooks --max-attempts 5 --max-deliveries 500
```

Scheduling the worker is an operational deployment decision. Committing this code does not enable or schedule outbound webhook traffic.

## Production activation checklist

Before enabling outbound delivery:

- apply migrations through head;
- generate and securely store a stable `INSTITUTIONAL_WEBHOOK_MASTER_SECRET`;
- leave `INSTITUTIONAL_WEBHOOK_ENABLED=false` while testing configuration and account controls;
- verify signing against a controlled public HTTPS receiver;
- confirm retry and dead-letter observability;
- configure a recurring worker schedule;
- only then set `INSTITUTIONAL_WEBHOOK_ENABLED=true`.

Gaia webhook events remain derived from the governed Fiscal Event ledger. If required evidence is unavailable, Gaia should preserve that limitation rather than manufacture a conclusion.
