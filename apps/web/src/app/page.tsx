import {
  ArrowRight,
  DatabaseZap,
  FileCheck2,
  GitCompareArrows,
  History,
  ShieldCheck,
} from 'lucide-react'
import type { Metadata } from 'next'
import Link from 'next/link'

import { ResearchCommandCenter } from '@/components/research-command-center'
import { StatusPill } from '@/components/status-pill'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { getPublishedAnalytics } from '@/lib/analytics-api'
import { formatDate, formatNaira } from '@/lib/format'
import { getPublishedOverview } from '@/lib/published-api'

export const metadata: Metadata = {
  title: 'GaiaFAAC — Evidence-grade fiscal intelligence for Nigeria',
  description:
    'Research-grade Nigerian fiscal intelligence with source fingerprints, human review, versioned evidence and independently verifiable records.',
}
export const dynamic = 'force-dynamic'

const principles = [
  {
    icon: FileCheck2,
    title: 'Source-backed',
    description:
      'Published records retain the source organization, document identity and SHA-256 fingerprint.',
  },
  {
    icon: ShieldCheck,
    title: 'Human-reviewed',
    description:
      'Automated validation happens first. Publication still requires explicit human verification.',
  },
  {
    icon: History,
    title: 'Version-aware',
    description:
      'Revisions, superseded claims and evidence history are modeled instead of silently overwritten.',
  },
]

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
    <>
      <section className="relative overflow-hidden border-b border-emerald-900/20 bg-[radial-gradient(circle_at_top_left,rgba(16,185,129,0.22),transparent_34%),linear-gradient(135deg,#081b15_0%,#0b2a20_55%,#10271f_100%)] text-white">
        <div className="pointer-events-none absolute inset-0 [background-image:linear-gradient(rgba(255,255,255,.08)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,.08)_1px,transparent_1px)] [background-size:42px_42px] opacity-20" />
        <div className="relative mx-auto max-w-7xl px-5 py-20 lg:px-8 lg:py-28">
          <div className="grid gap-10 lg:grid-cols-[1.1fr_0.9fr] lg:items-end">
            <div className="max-w-4xl">
              <div className="mb-6 flex flex-wrap items-center gap-3">
                <span className="rounded-full border border-emerald-300/25 bg-emerald-300/10 px-3 py-1 font-mono text-xs font-semibold tracking-[0.16em] text-emerald-100 uppercase">
                  Evidence-grade fiscal intelligence
                </span>
                {data ? (
                  <span className="rounded-full border border-white/15 bg-white/5 px-3 py-1 text-xs text-white/75">
                    Latest verified {formatDate(data.period.revenue_month)}
                  </span>
                ) : null}
              </div>
              <h1 className="max-w-5xl text-5xl font-semibold tracking-[-0.055em] text-balance sm:text-6xl lg:text-7xl">
                Nigeria’s fiscal numbers, with the evidence attached.
              </h1>
              <p className="mt-7 max-w-3xl text-lg leading-8 text-pretty text-emerald-50/75">
                GaiaFAAC is a research ledger for public-finance evidence:
                sourced, reconciled, human-reviewed, version-aware and designed
                so a serious analyst can trace the number back to the document.
              </p>
              <div className="mt-9 flex flex-wrap gap-3">
                <Button
                  asChild
                  size="lg"
                  className="bg-white text-emerald-950 hover:bg-emerald-50"
                >
                  <Link href="/live">
                    Open research workspace
                    <ArrowRight className="size-4" aria-hidden="true" />
                  </Link>
                </Button>
                <Button
                  asChild
                  size="lg"
                  variant="outline"
                  className="border-white/25 bg-white/5 text-white hover:bg-white/10"
                >
                  <Link href="/sources">Inspect the evidence</Link>
                </Button>
              </div>
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              <div className="rounded-xl border border-white/15 bg-white/8 p-5 backdrop-blur-md sm:col-span-2">
                <p className="text-xs font-medium tracking-[0.16em] text-emerald-100/70 uppercase">
                  Latest published state allocation total
                </p>
                <p className="mt-3 text-4xl font-semibold tracking-tight">
                  {data ? compactNaira(data.total_net) : 'Awaiting publication'}
                </p>
                {data ? (
                  <p className="mt-3 text-sm text-white/60">
                    {data.period.reporting_label} · {data.covered_states}/
                    {data.expected_states} jurisdictions ·{' '}
                    {data.source.source_organization}
                  </p>
                ) : null}
              </div>
              <div className="rounded-xl border border-white/15 bg-white/8 p-5 backdrop-blur-md">
                <p className="text-xs text-white/55">Coverage</p>
                <p className="mt-2 text-2xl font-semibold">
                  {data
                    ? `${data.covered_states}/${data.expected_states}`
                    : '—'}
                </p>
              </div>
              <div className="rounded-xl border border-white/15 bg-white/8 p-5 backdrop-blur-md">
                <p className="text-xs text-white/55">Published periods</p>
                <p className="mt-2 text-2xl font-semibold">
                  {analytics?.months_published ?? '—'}
                </p>
              </div>
              {data ? (
                <div className="rounded-xl border border-white/15 bg-white/8 p-5 backdrop-blur-md sm:col-span-2">
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-xs text-white/55">
                      Evidence fingerprint
                    </span>
                    <StatusPill tone="success">Verified</StatusPill>
                  </div>
                  <p className="mt-3 font-mono text-xs leading-5 break-all text-white/75">
                    {data.source.sha256}
                  </p>
                </div>
              ) : null}
            </div>
          </div>
        </div>
      </section>

      <section className="border-border/80 border-b">
        <div className="mx-auto max-w-7xl px-5 py-14 lg:px-8">
          <div className="grid gap-4 md:grid-cols-3">
            {principles.map(({ icon: Icon, title, description }) => (
              <Card key={title}>
                <CardHeader>
                  <Icon className="text-primary size-5" aria-hidden="true" />
                  <CardTitle className="pt-3">{title}</CardTitle>
                  <CardDescription>{description}</CardDescription>
                </CardHeader>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {data ? (
        <ResearchCommandCenter
          overview={data}
          analytics={analytics}
          analyticsError={analyticsResult.error}
        />
      ) : (
        <section className="border-border/80 border-b">
          <div className="mx-auto max-w-7xl px-5 py-16 lg:px-8">
            <Card>
              <CardHeader>
                <StatusPill tone="neutral">Awaiting governed data</StatusPill>
                <CardTitle className="pt-3">
                  Research workspace unavailable
                </CardTitle>
                <CardDescription>
                  GaiaFAAC does not synthesize replacement values when no
                  governed publication is available.
                </CardDescription>
              </CardHeader>
            </Card>
          </div>
        </section>
      )}

      <section className="border-border/80 border-b">
        <div className="mx-auto max-w-7xl px-5 py-16 lg:px-8">
          <div className="grid gap-5 lg:grid-cols-3">
            <Card className="lg:col-span-2">
              <CardHeader>
                <DatabaseZap
                  className="text-primary size-5"
                  aria-hidden="true"
                />
                <CardTitle className="pt-3 text-2xl">
                  Follow the evidence chain
                </CardTitle>
                <CardDescription>
                  Start with a published figure, inspect its source fingerprint,
                  compare jurisdictions, then export the governed record for
                  your own research workflow.
                </CardDescription>
                <div className="flex flex-wrap gap-2 pt-4">
                  <Button asChild size="sm">
                    <Link href="/account#exports">Export CSV / XLSX</Link>
                  </Button>
                  <Button asChild size="sm" variant="outline">
                    <Link href="/compare">
                      <GitCompareArrows className="size-4" aria-hidden="true" />
                      Compare jurisdictions
                    </Link>
                  </Button>
                  <Button asChild size="sm" variant="outline">
                    <Link href="/fiscal-design/verify">Verify a manifest</Link>
                  </Button>
                </div>
              </CardHeader>
            </Card>
            <Card className="bg-muted/30">
              <CardHeader>
                <CardTitle>Commercial access</CardTitle>
                <CardDescription>
                  Paid accounts unlock governed historical downloads, team
                  workflows and API access according to entitlement.
                </CardDescription>
                <div className="pt-4">
                  <Button asChild size="sm" className="w-full">
                    <Link href="/pricing">View access plans</Link>
                  </Button>
                </div>
              </CardHeader>
            </Card>
          </div>
        </div>
      </section>
    </>
  )
}
