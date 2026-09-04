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
- Playwright Control Plane coverage.

## What changed on PR #109

Commercial Revenue Completion adds or changes:

- privacy-preserving `commercial_events`;
- pilot intake no longer intentionally retains IP/user-agent metadata;
- admin CRM mutation for commercial leads;
- lead owner/next-action/loss/conversion metadata;
- factual admin commercial analytics;
- payment-confirmed commercial conversion event;
- optional canonical subscription linkage from successful payment records;
- removal of the legacy caller-supplied `X-Organization-ID` usage middleware from the live app;
- billing dashboard usage projection based on canonical plan/API request state rather than legacy subscription usage tables;
- README commercial status update;
- expanded Control Plane viewport/screenshot gate;
- required commercial/security/release documentation.

## Migrations created

- `20260904_0030_commercial_revenue_completion.py`
  - creates `commercial_events`;
  - adds CRM fields/indexes to `pilot_leads`;
  - adds canonical-subscription linkage to `payment_records`;
  - includes downgrade operations.

Migration upgrade and downgrade must be exercised before release.

## New / changed APIs

Commercial API additions:

- `PATCH /api/v1/commercial/pilot-leads/{lead_id}` — admin-only lead workflow mutation;
- `GET /api/v1/commercial/analytics` — admin-only factual commercial metrics.

Existing payment/Decision Room/Fiscal Receipt/Watch Contract routes remain the canonical product APIs and are not duplicated by this branch.

## New / changed tests

The branch extends commercial tests to cover:

- pilot submission persistence;
- privacy (no IP/user-agent retention for new leads);
- honeypot behavior;
- admin authorization;
- CRM-stage mutation;
- invalid-stage rejection;
- factual commercial analytics;
- payment/subscription linkage/event behavior;
- database metadata for the new commercial table/columns.

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

First-party commercial events are being introduced around real server-side transitions. The funnel must never be backfilled with invented activity.

## Production-real vs experimental

### Production-real foundations

- governed/public evidence architecture;
- organization/customer accounts and sessions;
- canonical subscription entitlement resolution;
- server-verified Paystack flow and payment ledger;
- Decision Rooms;
- Fiscal Receipts and verification;
- Watch Contracts and delivery/audit substrate;
- pilot lead capture.

### Release-candidate changes on PR #109

- commercial event ledger;
- CRM workflow/analytics;
- canonical billing-dashboard cleanup;
- payment conversion instrumentation;
- four-width Control Plane browser gate.

These remain release-candidate changes until green on the exact head.

### Still experimental / incomplete after PR #109

The original commercial-overhaul prompt is broader than PR #109. Remaining product items that require separate implementation or explicit validation include:

- a canonical product catalog/purchase abstraction for one-time, subscription, usage and quote products;
- transactional products such as individual Decision Packs / due-diligence snapshots;
- a dedicated Credit Committee Evidence Pack surface if it is not implemented as an existing Decision Packet variant;
- complete Fiscal Design scenario persistence/receipt linkage where not already covered;
- Ask Gaia workflow orchestration actions where not already covered;
- complete instrumentation of the full example funnel event list;
- explicit onboarding email/delivery audit after verified payment;
- all commercial analytics requested by the original prompt where a canonical source exists;
- verified production coverage for NBS IGR, DMO debt/debt-service, CBN macro and other public lanes before they are presented as verified;
- final SEO/trust page audit;
- full six-journey Playwright verification and visual review.

A missing capability must be labeled unavailable rather than simulated.

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

- governed data breadth is still uneven outside strongest FAAC coverage;
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
