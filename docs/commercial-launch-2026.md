# Gaia Fiscal Intelligence: evidence-led commercial launch

Status: hypothesis-driven commercial plan, not validated revenue or customer traction.

Owner decision: prioritize repeatable institutional diligence over a generic stock-market terminal.

## Initial buyer and paid job

Primary buyer: Nigerian financial institutions, investment advisers, credit/risk teams, consultancies and development-finance analysts evaluating state-level fiscal exposure.

Job: assess a named jurisdiction for an investment/credit/operational decision and deliver an auditable evidence packet, including source references, coverage gaps, revisions, comparable periods and reviewer notes. This is not a credit rating or investment recommendation.

## Product path (existing systems first)

1. Discover a jurisdiction through the free public ledger.
2. Open /credit-committee-pack and select the jurisdiction and year from actual published observations.
3. Review FAAC evidence, IGR if governed, missing data and watch events without synthetic estimates.
4. Inspect primary sources and evidence fingerprints.
5. Request an institutional pilot at /pilot for an agreed scope, or choose an existing subscription at /pricing.
6. Paid delivery uses the existing Decision Packet, Decision Room, proof, account/entitlement and Paystack workflows, subject to validation.

## Offer experiments (NOT published prices)

- Pilot: one jurisdiction, one decision question, documented data boundary, reviewed evidence dossier, proof and gap log. Quote after scope confirmation.
- Retainer: limited set of jurisdictions, agreed monitoring frequency, revision alerts, decision packet updates, account-backed collaboration.
- API licensing: evidence-bound feeds for vetted institutional consumers; define downstream rights and rate limits.

Do not promise data coverage, human review, turnaround, SLA, supported exports or advisory conclusions unless verified and contractually deliverable.

## Sales experiment and measurement

- Approach 10-15 relevant institutional teams with a source-linked sample and a concrete decision question.
- Ask about current workflow, time spent, required source confidence, buying authority, permissible datasets, and budget.
- Track qualified leads, pilot requests, pilot-to-paid conversion, payment success, repeat usage, report completion time, alert relevance and gross margin, using persisted first-party records.
- No synthetic testimonials, fictitious clients, modeled revenue presented as actual, or claims of customer demand without evidence.

## Quality and launch gates

- Confirm current publication coverage and latest dates for each offered jurisdiction before a pitch.
- Test the full browser journey (selector, year, pack, missing evidence, source links, pilot form) and verify responsive layout/accessibility.
- Run formatter, lint, typecheck, unit tests, build and Playwright on PostgreSQL-backed staging where necessary.
- Validate plan entitlements, checkout callbacks, payment verification, refund and failed-payment paths before charging.
- Maintain explicit human approval/four-eyes controls, Decimal/NUMERIC monetary precision, immutable source lineage, and fail-closed unavailable values.
- Do not merge or deploy while required CI checks fail.

## Why not Yahoo Finance now?

The core differentiator is provenance and institutional review, not real-time equities, brokerage accounts or generic financial charts. A securities feed entails licensing, stale-data controls, financial compliance and a separate market-data domain. Reassess only if paid-customer discovery identifies demand and economics.

## Next implementation tranche

Build a single true end-to-end research-to-report journey from governed state selection to evidence completeness, peer comparison, artifact preview, and verified commercial checkout; add event funnel instrumentation with verified source data, not fabricated sample KPIs.
