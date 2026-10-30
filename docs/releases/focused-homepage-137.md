# PR #137 — Focused homepage release gate

This is a **release checklist**, not authorization to merge or deploy. Do not conflate green CI with production acceptance.

## Scope and evidence

- GitHub PR: https://github.com/oluwafemidiakhoa/gaiafaac-intelligence/pull/137
- Branch: `feature/focused-fiscal-home-20261029`
- Changes: homepage, homepage tests, terminal URL-query handoff, terminal-search regression test.
- Published data only. No changes to ingestion, financial calculations, review controls, payments, API database schema, or credentials.
- Verify exact head commit and required CI jobs **again immediately before promotion**.

## Verified Railway target (29 October 2026)

- Project: `zucchini-benevolence` (`366c7826-db5f-4507-8639-fddc9ba3dc02`)
- Environment: `production` (`8a27a756-27f1-46cc-a736-ef4161005652`)
- Web: `gaiafaac-backend` (`3ee1aa1b-48c5-4666-bec3-dc350a4b441e`), domain `gaiafaac-web.up.railway.app`
- API: `gaiafaac-api` (`294b055c-85cd-430a-826e-b861db55975e`)
- Both deploy from `main`. The web service has `checkSuites: false`, so passing GitHub checks is **not enforced by Railway**.
- Baseline before PR deployment: production `main` commit `e33343699909f290a01775746ab239756326c704`. Recheck immediately before a release; this value can become stale.
- Earlier deployment `00a4ce92-ee44-4c90-a717-d9008181115e` was marked rollback-capable; recheck its availability at promotion time.

## Pre-merge gate

- [ ] PR head is still the intended commit; review all changed paths, including tests.
- [ ] CI web (format/lint/tests/build), API, configuration, and Playwright pass on that exact commit.
- [ ] No unexpected migrations, collector, auth, billing or publication changes in the diff.
- [ ] Render homepage on desktop and a narrow mobile viewport **in an isolated preview using no production secrets or writable production database**. If no isolated preview exists, record the missing gate rather than calling it complete.
- [ ] Verify keyboard navigation, select control and contrast; no duplicate or hidden navigation issues.
- [ ] Submit a state (e.g. Lagos) through the homepage form: terminal URL contains `?q=Lagos`, terminal search is populated and filters to that state.
- [ ] Inspect unavailable-data path: no fake totals, no empty state selector, and an evidence-registry fallback.
- [ ] Check the displayed reporting label against the published API and distinguish reporting period from current calendar month.
- [ ] Obtain explicit production-promotion authorization.

## Production release gate (requires authorization)

1. Confirm exact `main` baseline, target service and rollback deployment *before* merge.
2. Confirm merge strategy won't unintentionally include unrelated collection, billing, or migration PRs.
3. Merge only the verified code. Railway source is `main`; anticipate web **and possibly other services** redeploying if connected to the repository. Check which services actually start deploying.
4. Verify the target web deployment reaches SUCCESS and homepage/terminal pages respond. Observe API, scheduled jobs, error rates and logs; inspect evidence availability without changing data.
5. Test homepage selection to a real governed jurisdiction and check responsive appearance on the live domain.
6. If the homepage fails, data access regresses or deployment crashes, roll back the web service to its last verified deployment; record the incident and separately assess any other services redeployed.

## Explicit non-goals

- Do not auto-publish quarantined or unpublished fiscal records.
- Do not connect a preview to writable production Neon, Paystack keys, or customer-alert credentials.
- Do not claim the collectors' staleness or full analytical terminal features are fixed by this homepage PR.
- Old `docs/deployment-railway.md` describes a demo-era configuration; **do not use it as a current production runbook**.
