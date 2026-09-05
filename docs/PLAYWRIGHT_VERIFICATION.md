# Gaia Fiscal Intelligence — Playwright Verification

## Purpose

Compilation is not the release gate. Critical customer journeys must be exercised in a real browser at desktop, tablet and mobile widths, with screenshots and inspection of console/network failures.

## Required viewport matrix

The Control Plane browser gate covers:

- 1440 × 1000 desktop;
- 1024 × 900 compact desktop/tablet landscape;
- 768 × 1024 tablet;
- 390 × 844 mobile.

The branch test captures screenshots for the primary Control Plane surfaces at each release width and checks horizontal overflow.

## Primary route coverage

At minimum inspect:

- `/`;
- `/terminal`;
- `/decision-rooms`;
- `/watch-contracts`;
- `/live`;
- `/fiscal-pulse`;
- `/sources` / evidence surface;
- `/review`;
- `/institutional`;
- `/pricing`;
- account/login/signup/billing paths as test credentials/configuration permit;
- Fiscal Receipt verification;
- state/jurisdiction drill-down.

## Critical journeys

### Journey A — public evidence to account

Visitor → Terminal → jurisdiction/state → proof/source verification → signup.

Assertions:

- public evidence renders without synthetic replacement values;
- source/provenance links remain visible;
- CTA path reaches customer signup;
- no unexpected 5xx response or fatal console exception.

### Journey B — purchase to entitlement

Signup/login → checkout → provider-confirmed payment → entitlement → paid feature.

This journey requires a configured non-production payment test environment or a deterministic mocked/provider test. A browser redirect by itself does not count as payment verification.

Assertions:

- payment reference is server-verified;
- entitlement appears only after provider confirmation;
- billing history reflects the persisted payment record;
- paid feature resolves server-side entitlement.

### Journey C — Decision Room to Fiscal Receipt

Analyst/team → create/open Decision Room → preserve evidence boundary → capture governed evidence → generate Fiscal Receipt → verify receipt.

Assertions:

- organization context is preserved;
- receipt hash/manifest is deterministic for the captured boundary;
- public verifier exposes only the privacy-safe verification manifest;
- no private room notes leak to public verification.

### Journey D — monitoring

Team → Decision Room/baseline receipt → Watch Contract → deterministic condition → match/review/delivery state.

Assertions:

- condition definition remains customer-defined/deterministic;
- triggered record points to evidence/provenance;
- no inference of distress/default/safety;
- failed delivery does not destroy the match.

### Journey E — institutional lead

Prospect → pilot/institutional request form → accepted response → lead persisted → admin CRM visibility.

Assertions:

- private CRM fields are not public;
- honeypot/bot submission is not persisted;
- new lead intake does not retain IP/device/fingerprint metadata for commercial analytics.

### Journey F — horizontal privilege

Authenticated Organization A attempts a private resource belonging to Organization B.

Expected result: denied/not found according to route convention; never return Organization B’s private content.

## Console and network policy

For critical pages, collect browser console errors and failed HTTP responses. Release is blocked by:

- uncaught runtime exceptions;
- hydration failures that break interaction;
- repeated unexpected 5xx responses;
- failed API calls required for the tested journey;
- security/authorization regressions.

Known third-party/browser warnings may be documented only after confirming they do not represent application failure.

## Screenshot policy

Capture stable screenshots for primary routes at all four release widths. Screenshots are evidence for review, not proof by themselves. They should be retained as CI artifacts with the Playwright HTML report.

## Current branch status

PR #109 extends the Control Plane test with the four-width release matrix and screenshot capture. The PR remains draft until the exact final head has green CI and Playwright runs. This document must be updated with the final run IDs/conclusions before the release is declared ready.

## Final evidence to preserve

For the release commit preserve:

- exact Git commit SHA;
- CI workflow run ID and conclusion;
- Playwright workflow run ID and conclusion;
- Playwright HTML report artifact ID;
- screenshot artifact/report contents;
- any failure triage notes;
- migration head verified against the release commit.
