# Gaia Fiscal Decision Room

## Purpose

A Gaia Fiscal Decision Room is a persistent organization-scoped workspace for preserving the fiscal evidence boundary around an institutional decision or review.

The core question is:

> Can the institution reconstruct what governed evidence was available, what decision question was being considered, and what later changed?

A Decision Room is not a credit rating, investment recommendation, government approval, risk score, or substitute for an institution's own underwriting or governance process.

## Backwards-compatible architecture

Decision Rooms evolve the existing `evidence_rooms` storage rather than replacing it. Existing Evidence Room IDs, captured evidence and notes remain valid. `/evidence-rooms` remains an API compatibility surface, while the customer-facing product is `/decision-rooms`.

This preserves the strongest existing guarantees:

- organization scoping;
- Team/API entitlement enforcement;
- immutable captured evidence;
- editable human notes stored separately;
- durable room lifecycle (archive instead of delete);
- deterministic evidence hashes.

## Decision context

A Decision Room can declare:

- title;
- description / mandate;
- decision question;
- jurisdictions;
- supported evidence domains;
- baseline date;
- evidence cutoff;
- room status.

Decision context is organization-authored metadata. It is never promoted into governed fiscal fact.

## Evidence boundary

The room captures existing governed Gaia evidence references. Current supported reference classes are:

- retained source documents;
- Fiscal Proof;
- Decision Packet;
- Fiscal Event;
- organization alert.

Each captured reference stores:

- reference kind;
- reference identifier;
- internal/public reference URI where applicable;
- source SHA-256 where available;
- a point-in-time JSON snapshot;
- deterministic record SHA-256;
- capture timestamp;
- capturing user ID.

Captured evidence cannot be updated or deleted through the ORM. A repeated capture of the same reference in the same room is idempotent.

## Human review boundary

Human notes are deliberately stored in a separate table from governed evidence. They are editable by their author and are not included in public Fiscal Receipt verification.

This separation is fundamental:

1. reported fact / governed evidence;
2. deterministic calculation;
3. customer-authored decision context or assumption;
4. human interpretation;
5. AI explanation.

These categories must not silently collapse into one another.

## Fiscal Receipt

A Decision Room can generate a Fiscal Receipt over its current evidence boundary. The receipt is immutable and links to the room, organization and generating user privately. The public verifier exposes only the privacy-safe evidence fingerprint manifest.

See `docs/FISCAL_RECEIPT_SPEC.md`.

## Monitoring integration

The next commercial extension is to bind organization watchlists and deterministic monitoring conditions to a Decision Room. A triggered Fiscal Watch event should be capturable as new evidence and, when appropriate, generate a new Receipt representing the changed boundary.

The intended lifecycle is:

**Evidence → Decision Room → Fiscal Receipt → Monitoring → New Evidence → Review → Renewal**

## Authorization

Private room operations require:

- an active customer session;
- an organization;
- an organization membership;
- a Team or API entitlement under the current implementation.

Every room lookup includes `organization_id`. Cross-organization access must return 404 rather than revealing resource existence.

Public receipt verification is intentionally separate and privacy-reduced.

## Current limitations

- Room eligibility is currently inferred from the plan's multi-user entitlement; this should become an explicit `decision_rooms` feature entitlement.
- Evidence capture still accepts raw reference IDs; future UX should offer direct “Save to Decision Room” actions from Fiscal Proof, Decision Packet, Watch and source pages.
- Assumptions and deterministic scenario outputs are not yet first-class receipt objects.
- Decision Room membership currently inherits organization membership rather than supporting room-specific membership.
- Monitoring policies are not yet attached directly to rooms.

These limitations do not relax the evidence-governance contract.
