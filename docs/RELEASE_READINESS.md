# Gaia Fiscal Intelligence — Commercial Overhaul Release Readiness

## Release status

**Current status: DRAFT / NOT YET PRODUCTION-READY.**

The commercial overhaul must not be declared ready until the exact release head passes CI, migration verification and Playwright. This file is a release ledger, not marketing copy.

## What existed before this commercial completion branch

The repository already contained substantial production foundations:

- governed source ingestion, SHA-256 lineage, deterministic validation, human review and publication controls;
- public fiscal evidence/analytics surfaces;
- customer accounts, hashed sessions and organization invitations;
- canonical subscription entitlements;
- Paystack server-side checkout verification and signed webhook handling;
- billing history/payment records and renewal handling;
- Decision Rooms over organization-scoped evidence;
- immutable captured evidence snapshots;
- Fiscal Receipts with a public verification surface;
- Fiscal Proof, Decision Packets and Fiscal Events;
- Fiscal Watch Contracts with review/delivery workflows;
- organization alerts, opted-in email and institutional webhooks;
- pilot-lead persistence;
- NBS IGR and DMO debt ingestion/review foundations;
- Playwright Control Plane coverage.

## What changed on PR #109

Commercial Revenue Completion now includes:

- privacy-preserving `commercial_events` with no device/fingerprint analytics;
- pilot intake that does not intentionally retain IP/user-agent metadata;
- the requested institutional lead fields and stage sequence (`new`, `qualified`, `discovery`, `pilot_proposed`, `pilot_active`, `commercial_review`, `won`, `lost`);
- admin lead owner, next-action, due-date, internal-notes and closed-reason controls;
- factual admin commercial analytics sourced only from persisted Gaia records;
- configured-MRR projection explicitly distinguished from booked revenue;
- payment-confirmed conversion events and optional canonical-subscription linkage;
- server-side `checkout_started`, `checkout_completed` and `entitlement_activated` events;
- retry-safe post-payment onboarding email with success/failure audit events that never roll back verified entitlement;
- removal of the legacy caller-supplied `X-Organization-ID` usage middleware from the live app;
- billing dashboard usage projection based on canonical plan/API-request state;
- an outcome-oriented product-catalog abstraction for subscription, one-time, usage and enterprise-quote modes without inventing unapproved prices;
- `GET /api/v1/commercial/products`;
- a dedicated Credit Committee Evidence Pack surface built on the existing Decision Packet source of truth;
- Ask Gaia continuation actions into comparison, Decision Rooms, evidence packs, monitoring and Fiscal Design scenarios;
- homepage decision-chain positioning and a “Built for expensive decisions” institutional outcome section;
- expanded institutional pilot qualification fields (requested evidence domains, buying timeline and source page);
- full commercial/security/browser/revenue documentation required by the overhaul prompt;
- expanded Control Plane viewport/screenshot gate.

## Migrations created

- `20260904_0030_add_commercial_revenue_controls.py`
  - creates `commercial_events`;
  - adds institutional CRM fields/indexes to `pilot_leads`;
  - maps earlier branch stage names to the requested pipeline vocabulary;
  - adds canonical-subscription linkage to historical `payment_records` only where that legacy table exists;
  - includes downgrade operations.

The legacy-payment alteration is conditional because clean canonical migration history does not always contain the older payment table. Current entitlements remain sourced from canonical `subscriptions`.

## New / changed APIs

Commercial API additions:

- `GET /api/v1/commercial/products` — product modes and approved/configured public pricing only;
- `PATCH /api/v1/commercial/pilot-leads/{lead_id}` — admin-only lead workflow mutation;
- `GET /api/v1/commercial/analytics` — admin-only factual commercial metrics.

Existing payment, Decision Room, Fiscal Receipt and Watch Contract routes remain canonical and are not duplicated by this branch.

## Commercial analytics now exposed

Where a canonical persisted source exists the admin API reports:

- signups and active users;
- institutional lead counts/stages/plan interest;
- won-lead conversion rate;
- active paid organizations and plan distribution;
- configured MRR (active subscriptions × configured Paystack prices, clearly not booked revenue);
- successful payment count and revenue;
- failed payments;
- canceled/expired subscriptions;
- Decision Rooms;
- Fiscal Receipts;
- watchlists and Watch Contracts;
- API requests;
- recorded export events;
- first-party funnel event counts.

One-time purchase count remains explicitly unavailable until a canonical persisted purchase ledger exists. Quote requests are not misrepresented as purchases.

## New / changed tests

The branch extends coverage for:

- pilot submission persistence and qualification fields;
- privacy (no IP/user-agent retention for new leads);
- honeypot behavior;
- admin authorization;
- exact CRM-stage mutation and invalid-stage rejection;
- factual commercial analytics;
- product-catalog billing modes and no invented transactional/enterprise prices;
- payment/subscription linkage/event behavior;
- retry-safe onboarding delivery and non-rollback of entitlement on email failure;
- database metadata for new commercial persistence;
- migration upgrade/downgrade on clean canonical history.

The browser gate is expanded to run primary route checks and screenshots at 1440, 1024, 768 and 390 widths.

## Security findings

See `docs/SECURITY_REVIEW.md`.

Key release findings:

- organization isolation remains a critical release gate;
- payment/webhook verification has a strong server-side baseline;
- commercial analytics no longer requires invasive tracking;
- legacy caller-supplied organization usage middleware has been removed from the live app;
- account recovery/signup abuse/rate-limit behavior must be explicitly verified before institutional security claims;
- npm dependency audit findings must be triaged rather than ignored.

## Commercial funnel

Target loop:

**Evidence → Decision → Fiscal Receipt → Monitoring → New Evidence → Review → Renewal**

Server-side instrumentation now covers institutional lead creation/stage changes and checkout/payment/entitlement/onboarding transitions. Other first-party events should be added only at real workflow boundaries; the funnel must never be backfilled with invented activity.

## Production-real vs release-candidate

### Production-real foundations

- governed/public evidence architecture;
- organization/customer accounts and sessions;
- canonical subscription entitlement resolution;
- server-verified Paystack flow and payment ledger;
- Decision Rooms;
- Fiscal Receipts and verification;
- Watch Contracts and delivery/audit substrate;
- Decision Packets, Fiscal Design and Ask Gaia evidence interfaces;
- NBS IGR and DMO debt governed ingestion/review foundations;
- pilot lead capture.

### Release-candidate changes on PR #109

- commercial event ledger;
- complete institutional CRM fields/stages;
- full factual commercial-analytics API/dashboard;
- canonical billing-dashboard cleanup;
- payment conversion and onboarding instrumentation;
- product catalog abstraction;
- Credit Committee Evidence Pack UI;
- Ask Gaia workflow continuation actions;
- institutional homepage decision story;
- four-width Control Plane browser gate.

These remain release-candidate changes until green on the exact head.

## Remaining incomplete items from the original prompt

The following are intentionally **not** marked complete because doing so without evidence would violate the repository’s governance rules:

- canonical persisted one-time purchase/order ledger plus production checkout for transactional products; product definitions exist, but no unapproved price is invented;
- complete Fiscal Design scenario persistence directly inside Decision Rooms and direct Fiscal Receipt generation from persisted scenarios (scenario computation/integrity manifests exist today);
- full instrumentation of every example funnel event at every product boundary;
- verified production coverage for every requested NBS/DMO/CBN/federal-revenue lane; source/pipeline code is not treated as proof that production records are published;
- final SEO/trust-page audit and any missing legal/security copy;
- full six-journey Playwright verification and visual review on the frozen release commit;
- production deployment and post-deploy smoke test.

A missing capability is labeled unavailable rather than simulated.

## Playwright result

**Pending on final head.**

Do not paste an earlier green result here after additional commits. Record the final run ID, artifact ID and conclusion only when the release commit is frozen.

## CI result

**Pending on final head.**

Required gates:

- Ruff format/check;
- API tests;
- Prettier;
- web lint;
- TypeScript typecheck;
- web tests;
- production build;
- Docker configuration;
- migration upgrade/downgrade verification;
- Playwright.

## Remaining limitations

- governed data breadth is still uneven outside the strongest verified lanes;
- legacy billing tables remain for compatibility and must not be mistaken for the current entitlement source;
- one-time purchase accounting is not complete until a canonical purchase ledger exists;
- no claim of market validation or willingness-to-pay is implied by technical completion;
- Gaia does not provide a credit rating, investment recommendation or source-truth guarantee.

## Final release sign-off checklist

- [ ] exact head SHA frozen;
- [ ] reversible migration verified;
- [ ] CI green on exact head;
- [ ] Playwright green on exact head;
- [ ] screenshots/reports visually reviewed;
- [ ] no high-severity console/network regression;
- [ ] horizontal-privilege tests green;
- [ ] payment/webhook tests green;
- [ ] secrets/dependency findings triaged;
- [ ] production deployment green;
- [ ] smoke test after deployment;
- [ ] this document updated with final evidence.
