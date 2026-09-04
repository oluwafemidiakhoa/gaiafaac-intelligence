# Gaia Control Plane v2 validation

Control Plane v2 is not eligible for merge until the current branch head passes both the repository engineering gate and browser-level validation.

## Engineering gate

- Prettier formatting
- ESLint
- TypeScript typecheck
- Vitest web tests
- Next.js production build
- API Ruff formatting and lint
- API test suite

## Playwright browser gate

Chromium validates the customer-facing Control Plane against the configured API, including:

- desktop primary navigation
- mobile navigation
- Terminal
- Live
- Intelligence
- Evidence
- Review
- Institutions
- Pricing
- preservation of Review and Intelligence as first-class product surfaces
- duplicate-header detection
- route-level 5xx detection
- horizontal-overflow checks on critical desktop surfaces

The branch remains unmerged if either gate fails.
