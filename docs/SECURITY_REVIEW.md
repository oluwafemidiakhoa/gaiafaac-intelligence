# Gaia Fiscal Intelligence — Security Review

## Scope

This review covers the repository’s customer authentication, sessions, organization authorization, API keys, payments/webhooks, exports, admin routes, commercial CRM, Decision Rooms/Fiscal Receipts, Watch Contracts, secrets/configuration and relevant browser proxy behavior.

This is an engineering review, not a penetration-test certification.

## Authentication and password handling

Customer authentication is server-side. Session tokens are opaque and their SHA-256 digests, not plaintext tokens, are stored in `customer_sessions`. Organization invitation tokens are also stored as hashes. Password implementation and recovery paths must remain subject to automated abuse/rate-limit review whenever authentication code changes.

### Finding

**Status: acceptable foundation; abuse/recovery hardening remains release-sensitive.**

The repository has customer authentication/session primitives, but account recovery and signup-abuse controls must be explicitly rechecked before any enterprise security claim.

## Session/token handling

The Next.js `/api/customer/[...path]` proxy reads the HttpOnly `gaiafaac_session` cookie and converts it to a Bearer token only for the internal API request. Login/register/invite responses set an HttpOnly cookie; logout clears it.

Cookies are `sameSite=lax`, `httpOnly=true`, and `secure=true` in production.

### Finding

**Status: good baseline.**

Because the customer proxy accepts state-changing POST/PATCH/DELETE requests using cookie-derived authentication, CSRF assumptions must remain part of security review. SameSite=Lax materially reduces cross-site form/cookie risk, but sensitive future endpoints should not assume this alone is a universal CSRF defense.

## Organization authorization / IDOR

Organization-scoped Decision Rooms, Fiscal Receipts, Watch Contracts and customer resources must always query with authenticated organization context. Existing service patterns include `organization_id` in private resource queries and cross-organization tests exist for core evidence-room flows.

### Release rule

Every new private commercial subresource must have a horizontal-privilege test proving Organization A cannot read/update/delete Organization B’s resource even when A knows B’s UUID.

**Status: release gate.**

## SQL injection

The API predominantly uses SQLAlchemy expressions/ORM parameters rather than concatenating user input into SQL strings.

**Status: no injection issue identified in the reviewed commercial paths.**

Any future raw SQL must use bound parameters.

## XSS

The Next.js UI renders user-controlled lead/evidence text through React’s normal escaped text rendering. No reviewed commercial path requires raw HTML from customer input.

**Status: no stored-XSS path identified in reviewed commercial UI.**

Avoid `dangerouslySetInnerHTML` for evidence, notes, CRM fields or AI output unless a sanitizer and explicit security test are introduced.

## CSRF

Customer browser authentication is cookie-backed at the web proxy, while the upstream API sees a Bearer token. SameSite=Lax reduces cross-site cookie submission.

**Status: partial protection; document endpoint-specific assumptions.**

Do not introduce cross-origin credentialed customer APIs without a dedicated CSRF design.

## Rate limiting / abuse

Rate-limit behavior is important for login, signup, password recovery, public verification and AI question endpoints.

**Finding: verification is required before enterprise release.**

The commercial overhaul does not invent a claim that all these routes are already rate limited. A production readiness review must verify each externally abusable path against deployed middleware/provider controls.

## API key storage

API keys use prefixes plus stored hashes rather than retaining reusable plaintext keys. API usage is recorded in canonical `api_requests`.

**Status: good baseline.**

API keys must only be displayed in full at creation time and should be revocable.

## Payment and webhook verification

Paystack checkout verification is performed server-to-server. Returned metadata is checked against the authenticated organization and the transaction reference is checked. Paystack webhook HMAC-SHA512 is verified over the exact request body. Stripe webhook verification uses Stripe’s signature verification before synchronization.

**Status: strong baseline.**

Payment redirect data alone is never authoritative. Payment records and entitlement activation are idempotent around provider reference identifiers.

## Secrets / environment variables

Payment secrets, SMTP credentials, database URLs and admin controls are configuration/environment concerns. They must remain outside source control.

**Status: no hard-coded live payment credential introduced by the commercial branch.**

Any credential previously exposed outside the secret store should be rotated independently of this code review.

## Logging and privacy

The Commercial Revenue Completion branch intentionally stops new pilot submissions from storing IP address and user-agent metadata and introduces server-side `commercial_events` without device/fingerprint tracking.

Payment secrets must never be logged. SMTP service logging should be operational only and must not include credentials.

**Status: privacy posture improved.**

## Export authorization

Exports containing paid/private organization material must resolve entitlement and organization context server-side. Public evidence exports can remain public only where the evidence itself is published/public.

**Status: must remain covered by entitlement tests.**

## Admin routes

Commercial lead listing/mutation and commercial analytics require the admin dependency and are not ordinary customer endpoints.

**Status: correct boundary in reviewed routes.**

Admin keys must remain secrets and should be rotated if ever disclosed.

## Signup abuse and account recovery

**Finding: residual verification item.**

Before declaring institutional production readiness, explicitly test signup throttling, duplicate-email behavior, password reset token lifetime/single-use behavior (if enabled), invite expiry/single use and account-recovery enumeration resistance.

## Dependency security

The CI install currently reports npm audit findings. That output is not automatically proof that the production bundle is exploitable, but high-severity dependency advisories must be triaged before the final release document marks the branch production-ready.

## Commercial analytics privacy

Commercial metrics are first-party and computed from persisted Gaia records. New pilot intake does not intentionally retain network/device metadata for analytics. No third-party tracker is required for the commercial funnel.

## Security release checklist

- [ ] Full API unit/integration suite green on exact head.
- [ ] Horizontal privilege tests green for Decision Rooms, receipts, monitoring and private exports.
- [ ] Paystack/Stripe signature tests green.
- [ ] Login/signup/recovery abuse controls verified.
- [ ] Admin endpoints reject ordinary customers.
- [ ] Customer proxy CSRF assumptions reviewed for all state-changing routes.
- [ ] No secrets in repository/log output.
- [ ] High-severity dependency findings triaged.
- [ ] Playwright has no high-severity console errors or unexpected 5xx requests on critical journeys.

Until those gates are evidenced on the final head, the correct status is **release candidate / not yet declared production ready**.
