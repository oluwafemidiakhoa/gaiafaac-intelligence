# Gaia Fiscal Intelligence — Commercial Product Audit

## Executive conclusion

Gaia already contains substantially more institutional infrastructure than the public product story exposes. The repository is not merely a fiscal-data website: it contains governed source ingestion, SHA-256 lineage, explicit review/publication gates, Fiscal Proof, Decision Packets, Fiscal Events, organization watchlists and alerts, tenant-scoped Evidence Rooms, customer accounts, hashed sessions and invitations, API entitlements, institutional webhooks, pilot-lead capture, and payment records.

The commercial problem is fragmentation. These capabilities are presented as separate routes and features rather than one durable institutional workflow. The highest-value move is therefore not another dashboard or generic AI layer. It is to join the existing primitives into a defensible decision lifecycle:

**Evidence → Decision Room → Fiscal Receipt → Monitoring → New Evidence → Review → Renewal**

The first implementation target is to evolve the existing Evidence Room into a Gaia Fiscal Decision Room and add a cryptographically identifiable Fiscal Receipt that preserves the evidence boundary used for a decision.

This audit distinguishes observed repository capability from commercial hypotheses. No customer demand, revenue, adoption, or willingness-to-pay claim is treated as proven unless represented by actual stored product data.

## Current architecture

- **Web:** Next.js App Router in `apps/web`.
- **API:** FastAPI in `apps/api`.
- **Persistence:** PostgreSQL through SQLAlchemy; Alembic migrations under `database/migrations/versions`.
- **Deployment:** Railway web/API services.
- **Governed evidence:** source registration, SHA-256 fingerprinting, extraction, deterministic validation, human review, publication, public/entitled access.
- **Evidence domains already represented in code:** FAAC state/national evidence, local-government Table IV, IGR, debt, budgets, budget performance, liabilities, fiscal events and related provenance records. Presence of a model or pipeline does not imply production-complete published coverage.
- **Customer domain:** Organization, User, organization memberships/invites, customer sessions, subscriptions, API keys, watchlists, alerts, notification delivery and institutional webhooks.
- **Commercial domain:** pilot leads, Paystack/Stripe billing paths, payment records, plan entitlements and billing history.
- **Decision/evidence domain:** Fiscal Proof, Decision Packet, Fiscal Watch, Fiscal Events and Evidence Rooms.

## Current customer journey

The current product journey is fragmented across public evidence, Terminal/Live/Intelligence, state pages, Fiscal Proof, Decision Packets, Fiscal Design, Ask Gaia, pricing, account, billing, watchlists and Evidence Rooms. A user can obtain evidence and perform several useful actions, but the application does not yet give that work a durable institutional decision context.

The strongest existing journey is:

1. discover public governed evidence;
2. inspect a state or fiscal signal;
3. verify a source/proof;
4. sign up;
5. purchase or receive a plan;
6. use historical/export/team/API capabilities;
7. create watchlists, alerts or Evidence Rooms.

The missing commercial bridge is a persistent answer to: **what decision was being made, what was known at the time, what assumptions were used, and what changed afterward?**

## Current revenue journey

The current billing path has real production components:

- server-side customer authentication;
- canonical subscription/entitlement resolution;
- Paystack checkout initialization when configured;
- server-to-server Paystack verification;
- organization ownership validation for returned transactions;
- payment records and invoice/reference metadata;
- 30-day access/renewal handling;
- Stripe fallback code.

A significant technical-debt item remains: there are two generations of subscription models. The canonical entitlement path uses `Subscription`, while legacy `SubscriptionTier` / `OrganizationSubscription` / `UsageLog` / `Invoice` models remain in `subscription_models.py`. `PaymentRecord` is still reused from that older module. This split should be consolidated after the Decision Room/Receipt work, because billing analytics and entitlements should have one subscription source of truth.

## Current entitlement journey

`current_plan()` resolves the active canonical subscription and maps it to `Entitlements`. Free, Analyst, Team and API plans are represented. Evidence Rooms currently require Team or API because the implementation checks organization membership and a multi-user entitlement. Organization membership is enforced separately from internal reviewer roles.

The entitlement architecture is usable, but it currently encodes capability indirectly (for example, Evidence Rooms infer eligibility from `max_users > 1`). Commercial capabilities should move toward explicit feature entitlements such as `decision_rooms`, `fiscal_receipts`, `shared_monitoring`, `decision_packets`, `api_access` and plan-specific limits.

## Current evidence and data capability

Strongest production-ready evidence behavior:

- source identity and retained source metadata;
- SHA-256 fingerprints;
- reporting periods;
- deterministic extraction/validation boundaries;
- explicit human approval and publication controls;
- published-only public services;
- no silent substitution of missing values;
- revision-aware source structures;
- deterministic Fiscal Proof and Decision Packet services;
- immutable evidence capture inside Evidence Rooms.

The local-government Table IV path has been upgraded on this branch to choose a dedicated Excel or PDF extractor based on retained source type while preserving the governed 774-jurisdiction completeness gate. Public LGA pages also expose pipeline state rather than collapsing all unpublished states into a generic absence message.

Data-readiness caveat: the repository contains models/pipelines for IGR, debt, budgets and liabilities, but commercial UI must only present a lane as verified when governed published evidence actually exists.

## Existing institutional workflows

### Evidence Rooms

This is the strongest latent commercial primitive. Rooms are organization-scoped durable case files. Captured evidence is snapshotted, hashed and immutable. Human notes are structurally separate and editable. Room deletion is blocked; archival is required. Existing reference types include organization alerts, Fiscal Proof, Decision Packets, retained sources and Fiscal Events.

### Organization monitoring

Organization watchlists, alerts, delivery state and institutional webhooks already provide much of the substrate for a commercial Fiscal Watch Contract.

### Fiscal Proof and Decision Packets

These already create deterministic, evidence-linked outputs suitable for use inside a Decision Room and later Fiscal Receipt.

### Ask Gaia and Fiscal Design

These can become orchestration and scenario-entry surfaces, but they must remain downstream of governed evidence and explicit user assumptions.

### Institutional lead capture

Pilot leads are stored with organization/person/use-case context and can trigger internal email notification. The lead lifecycle is not yet a complete CRM pipeline.

## Production-real vs incomplete/legacy

### Production-real foundations

- governed source/published evidence architecture;
- organization/customer account model;
- hashed customer sessions and invite tokens;
- canonical plan resolution and server-side entitlements;
- Paystack server verification path and payment records;
- tenant-scoped Evidence Rooms;
- immutable captured evidence hashes;
- Fiscal Proof / Decision Packet / Fiscal Event primitives;
- watchlists, alerts and webhooks;
- pilot lead persistence;
- Playwright/browser-gate infrastructure on the Control Plane branch.

### Incomplete or legacy

- Evidence Rooms are not yet modeled/presented as decisions: no decision question, evidence cutoff, baseline date, declared jurisdictions or evidence domains.
- No durable Fiscal Receipt model or public receipt verification route exists yet.
- No receipt linkage from Decision Packets/scenarios/watch events.
- No explicit Decision Room monitoring policy lifecycle.
- No product-catalog abstraction for one-time purchases versus subscriptions versus enterprise quotes.
- Commercial analytics are fragmented and should not present legacy/demo KPI values.
- Lead status is a generic string and does not yet implement the required qualification/pilot/commercial stages.
- Duplicate subscription generations remain.
- README commercial-status language is stale relative to newer customer/billing functionality.
- Route naming is inconsistent in places (`/institutional` vs legacy `/institutions`, `/sources` vs `/evidence`).
- A legacy institutional dashboard contains assumptions/hard-coded presentation and should not be revived as a production source of truth.

## Security observations

### Existing strengths

- customer session tokens are stored as SHA-256 digests, not plaintext;
- organization invitations are hashed;
- Evidence Room access queries include `organization_id`;
- cross-organization room tests already exist;
- captured evidence is immutable at the ORM layer;
- admin lead access is protected;
- Paystack payment verification is server-side rather than trusting the browser redirect;
- source fingerprints are preserved.

### Required hardening / verification

- add explicit horizontal-privilege tests for Fiscal Receipts and every new Decision Room subresource;
- audit the `/api/customer` proxy for cookie/header forwarding and CSRF implications;
- review password reset/account recovery and signup-abuse controls;
- verify rate-limiting scope for login, signup, Ask Gaia and public verification endpoints;
- ensure no private Decision Room content leaks through public receipt verification;
- consolidate duplicate billing models to reduce inconsistent authorization/revenue reporting;
- rotate any credentials previously exposed outside the secret store; never log provider secrets.

## UX and conversion problems

- current capability is distributed across routes rather than organized around an expensive institutional job;
- users must manually know internal evidence IDs to add some Evidence Room references;
- no single screen preserves decision question + evidence boundary + assumptions + monitoring;
- no Fiscal Receipt makes a completed analysis portable and verifiable;
- missing/partial evidence has historically been represented too generically in some pages;
- core product navigation has changed repeatedly and temporarily orphaned Review/dashboard capability;
- public pages explain what Gaia is better than they explain what institutional work it replaces;
- paid value boundaries are still plan-centric rather than outcome-centric.

## Technical debt

1. canonical vs legacy subscription schemas;
2. duplicate/legacy institutional dashboard expectations versus current API schemas;
3. inconsistent route vocabulary;
4. capability checks inferred from unrelated entitlement fields;
5. manual evidence-reference capture UX;
6. documentation lagging implementation;
7. several pipeline/model lanes existing ahead of verified public data coverage;
8. Control Plane branch is large and must remain draft until CI and Playwright are green.

## Defensible commercial product primitive matrix

Scores are hypotheses based on repository capability, not proven market validation. `Regulatory risk` uses **10 = highest risk**, so lower is preferable.

| Primitive | Pain | WTP | Differentiation | Data readiness | Feasibility | Defensibility | Regulatory risk | Recurring revenue |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Decision Room + Fiscal Receipt + revision replay | 9 | 9 | 10 | 8 | 8 | 9 | 3 | 9 |
| Customer-defined Fiscal Watch Contract | 8 | 8 | 8 | 8 | 8 | 8 | 2 | 10 |
| Credit Committee Evidence Pack | 9 | 9 | 8 | 8 | 8 | 8 | 4 | 7 |
| Governed Evidence API + Receipt Verification | 8 | 8 | 8 | 8 | 9 | 8 | 2 | 9 |
| Due-Diligence Evidence Snapshot / transactional pack | 8 | 7 | 7 | 9 | 9 | 7 | 2 | 6 |
| Scenario Lab with explicit assumptions + receipts | 7 | 7 | 7 | 8 | 8 | 7 | 3 | 6 |

## Selected product

**Gaia Fiscal Decision Room + Fiscal Receipt** is selected first because it combines the highest differentiation with strong existing implementation foundations.

It is difficult to reproduce with an ordinary spreadsheet or generic LLM because its value comes from the combination of:

- governed source lineage;
- time-bounded evidence snapshots;
- immutable captured evidence hashes;
- organization-scoped decision context;
- deterministic calculations and explicit assumptions;
- later revision/monitoring events;
- a verifiable receipt that can be referenced outside the workspace.

The product claim is intentionally narrow: Gaia preserves and verifies the evidence manifest behind an institutional analysis. It does **not** certify the correctness of the customer's decision, provide a credit rating, or guarantee source truth beyond the provenance/verification state represented in Gaia.

## Recommended implementation sequence

1. Extend the existing Evidence Room into a backwards-compatible Decision Room with decision question, jurisdictions, evidence domains, baseline date and evidence cutoff.
2. Add an immutable Fiscal Receipt model, deterministic canonical hash and tenant-scoped receipt API.
3. Add public `/verify/{receipt_id}` rendering that exposes a privacy-safe verification manifest and clearly states what the receipt does and does not prove.
4. Upgrade the room UI from manual case-file CRUD into a decision workflow with evidence boundary, captured evidence, human notes, receipt generation and monitoring handoff.
5. Link Decision Packets and Fiscal Design scenarios into rooms/receipts without duplicating source-of-truth calculations.
6. Evolve organization monitoring into customer-defined Fiscal Watch Contracts and attach triggered events to rooms/receipts.
7. Instrument meaningful first-party commercial events without invasive tracking.
8. Expand lead stages and authorized commercial analytics using actual database values only.
9. Consolidate the legacy subscription/billing generation into the canonical subscription model.
10. Run unit/integration/security tests and Playwright at 1440/1024/768/390, capture screenshots, inspect console/network failures, and keep the release blocked until both CI and browser gates pass.

## Release boundary

This document is an audit and implementation plan, not a production-readiness declaration. Control Plane v2 remains a draft until current changes pass repository CI and Playwright. The Decision Room/Fiscal Receipt work must include reversible migrations, authorization tests, deterministic hash tests and browser verification before merge.
