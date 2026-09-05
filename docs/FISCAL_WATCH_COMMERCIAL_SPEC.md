# Gaia Fiscal Watch Contracts — Commercial Specification

## Purpose

Fiscal Watch Contracts are organization-scoped monitoring mandates over governed fiscal evidence. “Contract” means a monitoring configuration/service agreement; it is not a financial security, derivative, credit rating, solvency opinion, or investment recommendation.

The commercial job is to preserve a customer-defined monitoring policy after a Decision Room has established an evidence boundary, then surface factual governed changes that require review.

## Existing production architecture

The repository already contains:

- `FiscalWatchContract` and related match/review/delivery persistence models;
- organization-scoped service queries;
- API routes for contract lifecycle and evaluation;
- Decision Room and Fiscal Receipt linkage;
- in-app organization alerts;
- opted-in email delivery;
- institutional webhook delivery;
- delivery attempt/audit records;
- review/escalation workflows;
- unit/integration coverage for contract operations and delivery.

The implementation remains downstream of governed evidence. A threshold never creates a Gaia opinion such as “distress”, “safe”, “unsafe”, “default”, “solvent”, “corrupt”, or “creditworthy”.

## Customer configuration

A contract defines, where supported by published evidence:

- Decision Room / baseline Fiscal Receipt;
- one or more jurisdictions;
- supported evidence domains;
- deterministic monitoring conditions;
- threshold values and operators;
- delivery channels explicitly enabled by the organization;
- review/escalation state.

Supported conditions must be deterministic and must identify the evidence object and calculation used. Examples include a customer-defined FAAC percentage movement, a deduction-burden threshold, a newly published official source, a source revision, or previously unavailable governed evidence becoming available.

A domain must not be presented as active simply because a database table or ingestion model exists. Customer-facing monitoring is enabled only where the governed evidence lane is actually publishable and queryable.

## Trigger record

Each material match should preserve enough information to reconstruct why it fired:

- contract and condition identifier;
- organization and jurisdiction;
- event/match identifier;
- prior value and new value where the condition is numeric;
- deterministic calculation or comparison;
- customer-defined threshold/operator;
- governed evidence identifier(s);
- source/provenance reference(s);
- observed/trigger timestamp;
- verification or review link;
- baseline/linked Fiscal Receipt when applicable.

Missing evidence remains missing; a condition must not silently substitute zero, interpolate a value, or ask an LLM to supply a fact.

## Delivery contract

Delivery is separated from detection. A detected match can exist even when an external notification fails. That separation preserves the evidence/audit record and allows delivery retries without reinterpreting the fiscal event.

Supported outbound channels are intentionally explicit:

1. in-app organization alert;
2. email only where the relevant user/customer preference permits it;
3. institutional webhook only to configured organization endpoints.

Delivery failures must be retained as operational state and must not delete the underlying match.

## Tenant isolation

Every private read/write path is organization-scoped. A customer must never be able to read, update, evaluate, review, deliver, or enumerate another organization’s contract, match, receipt, Decision Room, or delivery record.

Horizontal-privilege tests are release-gating tests for this product family.

## Commercial packaging

The architecture supports packaging by outcome rather than by invented risk score:

- **Analyst:** personal governed monitoring where entitlement permits;
- **Team:** shared organization monitoring, Decision Rooms, review and alerts;
- **API:** programmatic governed evidence plus revision/monitoring integration and webhooks;
- **Institutional:** quoted monitoring mandates, portfolio surveillance, evidence-room workflows and permitted downstream rights.

Enterprise pricing is not hard-coded in this specification.

## Evidence-language boundary

Fiscal Watch reports what changed and why a configured condition matched. It does not infer legal, credit, investment, governance, fraud, corruption, default or solvency conclusions.

## Release criteria

A Watch Contract release is acceptable only when:

- organization isolation tests pass;
- deterministic condition tests pass;
- source/revision provenance is preserved;
- delivery preference enforcement passes;
- webhook verification/delivery tests pass;
- failed delivery remains auditable and retryable;
- the browser workflow passes at desktop, tablet and mobile release widths;
- no high-severity console or network regression remains.
