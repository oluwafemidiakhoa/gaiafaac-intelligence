# Gaia Fiscal Intelligence — Revenue Architecture

## Principle

Revenue state must be derived from real persisted customer, subscription and payment records. Commercial UI must not present modeled revenue, invented customers, synthetic transactions, fake MRR, or demo KPIs as production facts.

## Canonical entitlement source

The canonical current entitlement source is `subscriptions` / `Subscription` plus server-side `current_plan()` / `entitlements_for()` resolution.

A currently entitled organization is resolved from its canonical subscription status and billing-period boundary. Plan capability remains server-side; the browser is never authoritative for entitlement.

Legacy `subscription_tiers`, `organization_subscriptions`, `usage_logs`, `billing_events` and `invoices` remain compatibility/history structures while older callers are retired. They must not become a second current entitlement source.

`PaymentRecord` is retained because it is the existing persisted payment ledger. New successful Paystack records can be linked to the matching canonical subscription through `canonical_subscription_id` while the legacy nullable subscription reference remains backwards-compatible.

## Self-service payment lifecycle

Current Paystack lifecycle:

1. authenticated organization requests checkout;
2. server initializes Paystack with organization/plan metadata;
3. Paystack confirms payment by server verification and/or signed webhook;
4. Gaia validates transaction reference and organization ownership;
5. canonical `Subscription` is activated/renewed idempotently;
6. a successful `PaymentRecord` is created or updated idempotently;
7. invoice/reference metadata is retained;
8. billing history reflects the persisted payment ledger;
9. paid entitlement is resolved server-side;
10. renewal extends the access window.

A browser redirect is never proof of payment.

## Stripe compatibility

Stripe subscription code remains as a fallback compatibility path where configured. Stripe webhook signatures are verified by the provider library before subscription synchronization. Paystack is the primary path when its server secret is configured.

The existence of two provider paths does not justify two entitlement models. Both providers must converge on canonical `Subscription` state.

## Commercial event ledger

`commercial_events` is first-party, server-side instrumentation. It intentionally excludes IP address, device identifiers and browser fingerprinting.

Examples implemented on the Commercial Revenue Completion branch include:

- `pilot_lead_submitted`;
- `pilot_lead_stage_changed` / `pilot_lead_updated`;
- `payment_confirmed`.

Commercial events are evidence about product/commercial activity; they are not financial source evidence and must not be mixed into the governed fiscal ledger.

## Lead-to-customer lifecycle

Institutional enquiries persist in `pilot_leads`. Private CRM fields are admin-only and should include lifecycle stage, owner, next action/follow-up, notes/reason fields, and an optional link to the converted organization.

A conversion should be auditable but should not automatically infer revenue. Revenue is counted only from successful persisted payment records or an explicitly implemented one-time purchase ledger.

## Commercial analytics

Admin analytics must be generated from database state at request time or from an auditable derived table. Current factual metrics include:

- lead counts/stages;
- active canonical subscriptions by plan;
- successful payment count;
- successful payment revenue;
- first-party commercial-event counts.

Metrics that are not yet backed by a canonical record (for example one-time product purchases before a purchase ledger exists) must be labeled unavailable rather than invented as zero.

## Product catalog target

Gaia needs one product-catalog abstraction that can describe four commercial modes without hard-coding enterprise pricing:

- subscription;
- one-time purchase;
- enterprise quote;
- usage-based entitlement.

The catalog is a commercial configuration boundary, not a source of entitlement by itself. A paid entitlement becomes effective only after a successful purchase/subscription record is verified by the server.

Candidate product codes are intentionally outcome-oriented:

- Decision Pack;
- Multi-State Comparison Pack;
- Historical Fiscal Evidence Export;
- Due-Diligence Evidence Snapshot;
- Custom Fiscal Watch Setup;
- Institutional Research Pack;
- governed API/data usage.

Enterprise price remains `null`/quote-only unless a business-approved configuration explicitly supplies one.

## Payment-to-onboarding reliability

Payment success must not depend on email delivery. Onboarding/receipt email is a post-payment side effect: failure is logged/audited and retryable, but it must not roll back an already verified entitlement.

The desired order is:

**provider confirmation → idempotent payment record → canonical entitlement → receipt metadata → onboarding delivery attempt → product access → renewal/expiry → audit trail**

## Security boundary

- provider secrets remain environment variables;
- webhook signatures are verified;
- payment amount/reference/organization are checked server-side;
- customer billing endpoints require authenticated organization context;
- admin commercial analytics and CRM mutation require the admin control;
- caller-supplied organization IDs are not trusted as entitlement identity;
- secrets and full payment credentials must never be logged.

## Remaining consolidation work

The old invoice scheduler and legacy usage models still exist for compatibility and should be removed only after confirming no production process depends on them. Until then, they are historical/legacy and not authoritative for current entitlements or current commercial KPIs.

No code should silently migrate or delete production billing history as part of this consolidation.
