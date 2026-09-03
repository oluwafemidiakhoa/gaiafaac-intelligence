import type { Metadata } from 'next'
import Link from 'next/link'
import { getPublishedAnalytics } from '@/lib/analytics-api'
import { formatNaira } from '@/lib/format'
import { getPublishedOverview } from '@/lib/published-api'

export const metadata: Metadata = {
  title: 'Gaia Fiscal Intelligence',
  description:
    'Verified public-finance evidence for Nigeria. Every fiscal number traced to source with complete provenance.',
}
export const dynamic = 'force-dynamic'

function compactNaira(value: string | null) {
  if (!value) return 'Unavailable'
  const amount = Number(value)
  if (!Number.isFinite(amount)) return formatNaira(value)
  if (Math.abs(amount) >= 1_000_000_000_000)
    return `₦${(amount / 1_000_000_000_000).toFixed(2)}T`
  if (Math.abs(amount) >= 1_000_000_000)
    return `₦${(amount / 1_000_000_000).toFixed(2)}B`
  return formatNaira(value)
}

export default async function Home() {
  const [overviewResult, analyticsResult] = await Promise.all([
    getPublishedOverview(),
    getPublishedAnalytics(),
  ])
  const data = overviewResult.data
  const analytics = analyticsResult.data

  return (
    <div className="min-h-screen bg-stone-50 text-stone-900">
      <style>{`
        :root {
          --teal-900: #1B4A5C;
          --teal-800: #2B5F74;
          --teal-50: #EDF5F8;
          --gold-600: #D4A574;
          --stone-50: #F5F3F0;
          --stone-200: #E8E5E1;
          --stone-400: #C4BEBD;
          --stone-600: #8B7F7D;
          --stone-900: #3A3531;
          --sage: #7A8D7E;
        }
        @media (prefers-color-scheme: dark) {
          :root {
            --text-dark: #F9F8F7;
            --stone-50: #2A2520;
            --stone-200: #3F3A36;
            --stone-400: #6B6560;
            --stone-900: #E8E5E1;
            --teal-50: #1B4A5C;
          }
        }
        h1, h2, h3 { font-family: Georgia, serif; }
        h1 { font-size: 3.5rem; line-height: 1.1; }
        h2 { font-size: 2.25rem; line-height: 1.2; }
        h3 { font-size: 1.5rem; line-height: 1.3; }
        p { max-width: 65ch; line-height: 1.6; }
      `}</style>

      {/* Hero / Thesis */}
      <section className="border-b border-stone-200 bg-teal-50 py-16">
        <div className="mx-auto max-w-6xl px-6 lg:px-8">
          <div className="grid gap-12 lg:grid-cols-2">
            <div>
              <h1 className="mb-6 text-teal-900">
                Every fiscal number, traced to source
              </h1>
              <p className="mb-4 text-lg text-stone-900">
                Nigeria&apos;s public finance data verified at the point of
                entry, with complete provenance. For institutions that need to
                know where every number came from.
              </p>
              <p className="text-lg font-semibold text-stone-600">
                No interpolation. No inference. No guesswork.
              </p>
            </div>
            <div className="space-y-3 rounded-lg border border-stone-200 bg-white p-8">
              <div className="flex gap-3">
                <div className="bg-gold-600 mt-1 h-2 w-2 flex-shrink-0 rounded-full" />
                <div>
                  <div className="text-sm font-semibold tracking-wide text-teal-900 uppercase">
                    Source
                  </div>
                  <div className="text-sm text-stone-600">
                    Official government document (OAGF, FAAC, CBN)
                  </div>
                </div>
              </div>
              <div className="flex gap-3">
                <div className="bg-gold-600 mt-1 h-2 w-2 flex-shrink-0 rounded-full" />
                <div>
                  <div className="text-sm font-semibold tracking-wide text-teal-900 uppercase">
                    Fingerprint
                  </div>
                  <div className="text-sm text-stone-600">
                    SHA-256 hash of retained bytes
                  </div>
                </div>
              </div>
              <div className="flex gap-3">
                <div className="bg-gold-600 mt-1 h-2 w-2 flex-shrink-0 rounded-full" />
                <div>
                  <div className="text-sm font-semibold tracking-wide text-teal-900 uppercase">
                    Extraction
                  </div>
                  <div className="text-sm text-stone-600">
                    Deterministic parsing and validation
                  </div>
                </div>
              </div>
              <div className="flex gap-3">
                <div className="bg-gold-600 mt-1 h-2 w-2 flex-shrink-0 rounded-full" />
                <div>
                  <div className="text-sm font-semibold tracking-wide text-teal-900 uppercase">
                    Review
                  </div>
                  <div className="text-sm text-stone-600">
                    Human verification by qualified auditor
                  </div>
                </div>
              </div>
              <div className="flex gap-3">
                <div className="bg-gold-600 mt-1 h-2 w-2 flex-shrink-0 rounded-full" />
                <div>
                  <div className="text-sm font-semibold tracking-wide text-teal-900 uppercase">
                    Approval
                  </div>
                  <div className="text-sm text-stone-600">
                    Separate publisher signs off (four-eyes control)
                  </div>
                </div>
              </div>
              <div className="flex gap-3">
                <div className="bg-gold-600 mt-1 h-2 w-2 flex-shrink-0 rounded-full" />
                <div>
                  <div className="text-sm font-semibold tracking-wide text-teal-900 uppercase">
                    Published
                  </div>
                  <div className="text-sm text-stone-600">
                    Immutable record with full audit trail
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {!data && (
        <section className="border-b border-stone-200 bg-amber-50 py-16">
          <div className="mx-auto max-w-6xl px-6 lg:px-8">
            <h2 className="mb-4 text-teal-900">
              Research workspace unavailable
            </h2>
            <p className="mb-4 text-stone-700">
              Gaia Fiscal Intelligence does not synthesize replacement values.
              Evidence is published only when data has been verified by
              qualified reviewers and approved by separate publishers using
              four-eyes control.
            </p>
            <p className="text-sm text-stone-600">
              Check back soon as jurisdictions submit and review their fiscal
              evidence.
            </p>
          </div>
        </section>
      )}

      {/* Key Metrics */}
      <section className="py-16">
        <div className="mx-auto max-w-6xl px-6 lg:px-8">
          <div className="grid gap-6 lg:grid-cols-3">
            <div className="border-gold-600 rounded border-l-4 bg-white p-6 shadow-sm">
              <div className="text-gold-600 font-mono text-3xl font-bold">
                {data ? compactNaira(data.total_net) : '—'}
              </div>
              <div className="text-sm tracking-wide text-stone-600 uppercase">
                Latest Published Total
              </div>
              <div className="mt-2 text-xs text-stone-500">
                {data
                  ? `${data.covered_states}/37 jurisdictions • ${data.period?.reporting_label}`
                  : 'Awaiting publication'}
              </div>
            </div>
            <div className="border-gold-600 rounded border-l-4 bg-white p-6 shadow-sm">
              <div className="text-gold-600 font-mono text-3xl font-bold">
                37/37
              </div>
              <div className="text-sm tracking-wide text-stone-600 uppercase">
                Coverage
              </div>
              <div className="mt-2 text-xs text-stone-500">
                All Nigerian states and FCT
              </div>
            </div>
            <div className="border-gold-600 rounded border-l-4 bg-white p-6 shadow-sm">
              <div className="text-gold-600 font-mono text-3xl font-bold">
                {analytics?.months_published ?? '—'}
              </div>
              <div className="text-sm tracking-wide text-stone-600 uppercase">
                Published Periods
              </div>
              <div className="mt-2 text-xs text-stone-500">
                Consecutive months with verified data
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Values Section */}
      <section className="border-t border-stone-200 bg-white py-16">
        <div className="mx-auto max-w-6xl px-6 lg:px-8">
          <h2 className="mb-12 text-center text-teal-900">
            Built for institutional confidence
          </h2>
          <div className="grid gap-8 lg:grid-cols-3">
            <div>
              <div className="mb-4 text-3xl">🔗</div>
              <h3 className="mb-2 text-teal-900">Unbroken Chain</h3>
              <p className="text-stone-600">
                Every figure remains linked to its source document and
                cryptographic proof. No intermediate guesses or backfills.
              </p>
            </div>
            <div>
              <div className="mb-4 text-3xl">🔍</div>
              <h3 className="mb-2 text-teal-900">Anomaly Intelligence</h3>
              <p className="text-stone-600">
                AI detects unusual movements and peer deviations, flagged for
                review before publication. Findings are always annotated.
              </p>
            </div>
            <div>
              <div className="mb-4 text-3xl">✓</div>
              <h3 className="mb-2 text-teal-900">Four-Eyes Control</h3>
              <p className="text-stone-600">
                Separate reviewer and publisher roles ensure no single person
                can make data public. Full audit trail recorded.
              </p>
            </div>
            <div>
              <div className="mb-4 text-3xl">📜</div>
              <h3 className="mb-2 text-teal-900">Revision History</h3>
              <p className="text-stone-600">
                Every update preserves prior values and reason codes. You can
                see what changed, when, and by whom.
              </p>
            </div>
            <div>
              <div className="mb-4 text-3xl">⚖️</div>
              <h3 className="mb-2 text-teal-900">Conflict Resolution</h3>
              <p className="text-stone-600">
                When sources disagree, we keep both values and flag the
                conflict. No silent rewrites to make numbers clean.
              </p>
            </div>
            <div>
              <div className="mb-4 text-3xl">📊</div>
              <h3 className="mb-2 text-teal-900">Peer Benchmarking</h3>
              <p className="text-stone-600">
                Compare metrics across jurisdictions using verified data. Rank
                by actual performance, not narrative.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Institutions Section */}
      <section className="border-y border-stone-200 bg-stone-50 py-16">
        <div className="mx-auto max-w-6xl px-6 lg:px-8">
          <h2 className="mb-12 text-center text-teal-900">
            Tailored for every stakeholder
          </h2>
          <div className="grid gap-6 lg:grid-cols-4">
            <div className="border-sage rounded-lg border-t-4 bg-white p-6">
              <h3 className="mb-4 text-teal-900">Loan Committees</h3>
              <ul className="space-y-2 text-sm text-stone-600">
                <li>→ Sustainability assessment</li>
                <li>→ FAAC dependence ratio</li>
                <li>→ Revenue trend analysis</li>
                <li>→ Peer comparison</li>
              </ul>
            </div>
            <div className="border-sage rounded-lg border-t-4 bg-white p-6">
              <h3 className="mb-4 text-teal-900">Investors</h3>
              <ul className="space-y-2 text-sm text-stone-600">
                <li>→ Growth trajectory</li>
                <li>→ Anomaly detection</li>
                <li>→ Risk positioning</li>
                <li>→ Fiscal health score</li>
              </ul>
            </div>
            <div className="border-sage rounded-lg border-t-4 bg-white p-6">
              <h3 className="mb-4 text-teal-900">Auditors</h3>
              <ul className="space-y-2 text-sm text-stone-600">
                <li>→ Conflict resolution</li>
                <li>→ Audit trail review</li>
                <li>→ Period reconciliation</li>
                <li>→ Coverage gaps</li>
              </ul>
            </div>
            <div className="border-sage rounded-lg border-t-4 bg-white p-6">
              <h3 className="mb-4 text-teal-900">Policymakers</h3>
              <ul className="space-y-2 text-sm text-stone-600">
                <li>→ Peer benchmarking</li>
                <li>→ Fiscal support need</li>
                <li>→ Policy impact modeling</li>
                <li>→ Jurisdictional ranking</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* Tech Section */}
      <section className="py-16">
        <div className="mx-auto max-w-6xl px-6 lg:px-8">
          <div className="grid gap-12 lg:grid-cols-2">
            <div>
              <h2 className="mb-4 text-teal-900">
                API-First. Built for Integration.
              </h2>
              <p className="mb-4 text-stone-600">
                Gaia is accessible to your systems through versioned REST APIs.
                Request access for your institution, auditor, or development
                team.
              </p>
              <p className="text-sage text-xs font-semibold tracking-widest uppercase">
                Available endpoints:
              </p>
            </div>
            <div className="space-y-2 rounded bg-teal-900 p-6 font-mono text-sm text-white">
              <div className="text-gold-600">GET</div>
              <div className="text-stone-300">
                /api/v1/published/readiness-matrix
              </div>

              <div className="text-gold-600 mt-4">GET</div>
              <div className="text-stone-300">
                /api/v1/jurisdictions/{'{code}'}/metrics
              </div>

              <div className="text-gold-600 mt-4">GET</div>
              <div className="text-stone-300">
                /api/v1/evidence/provenance/{'{gaia_id}'}
              </div>

              <div className="text-gold-600 mt-4">POST</div>
              <div className="text-stone-300">
                /api/v1/decisions/packet/{'{jurisdiction}'}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="bg-teal-900 py-16 text-center text-white">
        <div className="mx-auto max-w-6xl px-6 lg:px-8">
          <h2 className="mb-4">Ready to trust your fiscal data?</h2>
          <p className="mb-8 text-lg text-stone-200">
            Request institutional access for your bank, audit firm, government
            agency, or development institution.
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <Link
              href="/pricing"
              className="bg-gold-600 rounded px-8 py-3 font-semibold text-teal-900 hover:bg-yellow-100"
            >
              Request Access
            </Link>
            <Link
              href="/evidence"
              className="border-gold-600 rounded border-2 px-8 py-3 font-semibold text-white hover:bg-teal-800"
            >
              View Evidence Registry
            </Link>
          </div>
        </div>
      </section>
    </div>
  )
}
