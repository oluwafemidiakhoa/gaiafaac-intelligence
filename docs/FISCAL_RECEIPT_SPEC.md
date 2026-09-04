# Gaia Fiscal Receipt Specification

## Objective

A Fiscal Receipt is a cryptographically identifiable record of the Gaia evidence boundary used in a Decision Room at a point in the workflow.

It answers a narrow question:

> Which governed Gaia evidence records and source fingerprints were captured behind this analysis boundary?

It does **not** certify the quality of a customer's decision, guarantee the truth of an external source, provide a credit rating, or imply government approval.

## Version

Current schema/methodology identifier:

`fiscal-receipt-v1`

The methodology/version identifier is part of the manifest so future receipt formats can remain independently interpretable.

## Private receipt

A private receipt is available only to the owning organization and includes:

- receipt ID;
- Decision Room ID;
- organization ID;
- generating user ID;
- generated timestamp;
- evidence cutoff;
- methodology version;
- canonical manifest;
- receipt SHA-256.

The canonical manifest currently includes:

- schema/version;
- Decision Room ID and title;
- decision question;
- jurisdictions;
- evidence domains;
- baseline date;
- effective evidence cutoff;
- room status;
- evidence count;
- captured evidence references;
- reference URI when applicable;
- source SHA-256 when available;
- captured record SHA-256;
- captured timestamp;
- captured point-in-time snapshot;
- aggregate source hash list;
- aggregate evidence-record hash list;
- explicit `missing_evidence` collection;
- explicit `assumptions` collection;
- methodology version.

`missing_evidence` and `assumptions` are currently empty until Gaia has a first-class governed mechanism for recording them. The system must not infer or fabricate them.

## Canonical hashing

The receipt digest is:

`SHA-256(canonical JSON manifest)`

Canonical JSON uses:

- sorted object keys;
- compact separators;
- UTF-8 encoding;
- stable string serialization for supported date/time/identifier values.

The generation service queries for an existing receipt with the same Decision Room ID and receipt hash before creating another record. Repeating receipt generation over an unchanged evidence boundary therefore returns the same receipt rather than creating duplicate audit artifacts.

Adding governed evidence changes the canonical manifest and therefore changes the receipt hash.

## Evidence cutoff semantics

If the Decision Room declares an `evidence_cutoff`, receipt generation includes captured evidence at or before that cutoff.

If no explicit cutoff is declared and evidence exists, the effective cutoff becomes the latest captured-evidence timestamp represented by the receipt. This makes the current captured boundary reproducible without pretending that uncaptured external evidence did not exist.

If the room contains no evidence and no explicit cutoff, the cutoff remains absent.

## Immutability

`FiscalReceipt` update and delete operations are rejected at the ORM event layer. Receipts are audit records, not editable documents.

Decision Room context may continue evolving after a receipt is generated. A later evidence boundary creates a new receipt rather than rewriting an earlier one.

## Public verification

Public endpoint:

`GET /api/v1/fiscal-receipts/{receipt_id}/verify`

Public web page:

`/verify/{receipt_id}`

The public verifier exposes only a privacy-safe manifest:

- receipt ID;
- receipt SHA-256;
- methodology version;
- generated timestamp;
- evidence cutoff;
- declared jurisdictions;
- declared evidence domains;
- evidence count;
- source SHA-256 values;
- evidence-record SHA-256 values;
- evidence kinds;
- verification statement;
- limitations.

It intentionally excludes:

- organization ID/name;
- generating user ID;
- Decision Room title;
- private decision question;
- human notes;
- private captured snapshot contents.

## Public verification statement

The verifier states that the receipt identifies the Gaia evidence records captured at the stated boundary and the SHA-256 digest of the canonical manifest.

It also states that the receipt:

- does not certify or approve lending, investment, procurement or policy decisions;
- does not make Gaia an official government publisher or credit-rating agency;
- does not prove that every possible source existed or was captured;
- does not expose private organization notes or decision context.

## Authorization

Receipt generation, listing and full private retrieval require the same organization-scoped Decision Room entitlement and membership checks used by the owning room.

Private retrieval filters by `organization_id`; another organization receives 404.

Public verification accepts only a receipt UUID and returns the restricted public manifest.

## Required tests

The release gate includes tests that prove:

1. repeated generation over an unchanged evidence boundary is idempotent;
2. receipt SHA-256 is 64 hexadecimal characters;
3. adding governed evidence changes the receipt hash;
4. a different organization cannot retrieve the private receipt;
5. public verification excludes private decision context and tenant identifiers;
6. receipt mutation is rejected;
7. pre-existing Evidence Room behavior remains functional.

## Future extensions

Planned receipt inputs must remain explicitly typed rather than silently embedded in narrative:

- deterministic calculation inputs/results;
- named user assumptions;
- Fiscal Design scenario IDs and equations;
- monitoring-condition definitions and triggered Watch Event IDs;
- revision identifiers and “what changed” comparison;
- generated Decision/Credit Committee Pack IDs;
- explicit missing-evidence declarations.

Any extension that changes canonical manifest semantics must use a new methodology version or a backwards-compatible schema rule documented here.
