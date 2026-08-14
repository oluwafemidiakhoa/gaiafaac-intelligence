import {
  ArrowRight,
  BarChart3,
  FileCheck2,
  GitCompareArrows,
  History,
  Map,
  Radio,
  ShieldCheck,
} from 'lucide-react'
import type { Metadata } from 'next'
import Link from 'next/link'

import { MetricCard } from '@/components/metric-card'
import { StatusPill } from '@/components/status-pill'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { formatDate, formatNaira } from '@/lib/format'
import { getFiscalEvents } from '@/lib/fiscal-ledger-api'
import { getPublishedOverview } from '@/lib/published-api'

export const metadata: Metadata = {
  title: 'GaiaFAAC — The verifiable fiscal ledger for Nigeria',
}
export const dynamic = 'force-dynamic'

const destinations = [
  {
    href: '/fiscal-pulse',
    icon: BarChart3,
    title: 'Fiscal Pulse',
    description:
      'Annual allocations, deduction burden, net retention, momentum and volatility with evidence status.',
  },
  {
    href: '/live',
    icon: Radio,
    title: 'Latest verified data',
    description:
      'The most recent human-approved FAAC month, with every figure traced to its OAGF source.',
  },
  {
    href: '/states',
    icon: Map,
    title: 'State directory',
    description:
      'All 36 states and the FCT. Unavailable values are left blank — never inferred.',
  },
  {
    href: '/compare',
    icon: GitCompareArrows,
    title: 'Compare states',
    description:
      'Put two to six jurisdictions side by side on verified figures.',
  },
]

const audiences = [
  [
    'Banks & financial institutions',
    'Understand historical state allocation patterns and cash-flow variability without treating FAAC alone as a credit rating.',
  ],
  [
    'Newsrooms',
    'Find state fiscal movements and source evidence faster for reporting and investigations.',
  ],
  [
    'Consultancies & researchers',
    'Compare states without rebuilding government tables manually every month.',
  ],
  [
    'Governance organizations',
    'Track allocations and deductions with traceable evidence and explicit data limitations.',
  ],
]

const ledgerPrinciples = [
  {
    icon: FileCheck2,
    title: 'Evidence',
    description:
      'Every published fiscal value traces to a retained source document and SHA-256 fingerprint.',
  },
  {
    icon: ShieldCheck,
    title: 'Verification',
    description:
      'Portable proof objects and canonical manifests can be recomputed independently.',
  },
  {
    icon: History,
    title: 'History',
    description:
      'Fiscal States and claims are versioned and superseded without silently rewriting prior evidence.',
  },
]

export default async function Home() {
  const [result, eventResult] = await Promise.all([
    getPublishedOverview(),
    getFiscalEvents(),
  ])
  const data = result.data
  const latestEvents = eventResult.data?.data.slice(0, 4) ?? []
  const recentProofIds = Array.from(
    new Set(
      latestEvents
        .flatMap((event) => event.evidence_ids)
        .filter(
          (identifier) =>
            identifier.startsWith('GF-') && !identifier.startsWith('GFC-'),
        ),
    ),
  ).slice(0, 4)
  const ranked = data
    ? [...data.allocations]
        .filter((a) => a.net_allocation)
        .sort((a, b) => Number(b.net_allocation) - Number(a.net_allocation))
        .slice(0, 6)
    : []

  return (
    <>
      <section className="border-border/80 border-b">
        <div className="mx-auto grid max-w-7xl gap-12 px-5 py-20 lg:grid-cols-[1.3fr_0.7fr] lg:px-8 lg:py-28">
          <div className="max-w-3xl">
            <p className="text-primary mb-5 font-mono text-xs font-semibold tracking-[0.18em] uppercase">
              GaiaFAAC · public fiscal evidence infrastructure
            </p>
            <h1 className="text-5xl font-semibold tracking-[-0.045em] text-balance sm:text-6xl lg:text-7xl">
              The verifiable fiscal ledger for Nigeria.
            </h1>
            <p className="text-muted-foreground mt-7 max-w-2xl text-lg leading-8 text-pretty">
              Verified public-finance evidence for every Nigerian jurisdiction —
              sourced, reconciled, versioned, and independently verifiable.
              Missing values remain unavailable rather than inferred.
            </p>
            <div className="mt-9 flex flex-col gap-3 sm:flex-row">
              <Button asChild size="lg">
                <Link href="/states">
                  Explore jurisdictions
                  <ArrowRight className="size-4" aria-hidden="true" />
                </Link>
              </Button>
              <Button asChild size="lg" variant="outline">
                <Link href="/fiscal-design/verify">Verify a manifest</Link>
              </Button>
            </div>
          </div>

          <Card className="bg-muted/30 self-end">
            <CardHeader>
              {data ? (
                <>
                  <StatusPill tone="success">Verified · published</StatusPill>
                  <CardTitle className="pt-3 text-2xl">
                    {formatNaira(data.total_net)}
                  </CardTitle>
                  <CardDescription>
                    Latest total net allocation ·{' '}
                    {formatDate(data.period.revenue_month)} · coverage{' '}
                    {data.covered_states}/{data.expected_states} · source:{' '}
                    {data.source.source_organization}
                  </CardDescription>
                </>
              ) : (
                <>
                  <StatusPill tone="neutral">Awaiting publication</StatusPill>
                  <CardTitle className="pt-3 text-2xl">
                    Verified data coming online
                  </CardTitle>
                  <CardDescription>
                    Reports are ingested, validated, and human-approved before
                    they appear. Nothing is published automatically.
                  </CardDescription>
                </>
              )}
            </CardHeader>
          </Card>
        </div>
      </section>

      <section className="border-border/80 border-b">
        <div className="mx-auto max-w-7xl px-5 py-14 lg:px-8">
          <div className="grid gap-4 md:grid-cols-3">
            {ledgerPrinciples.map(({ icon: Icon, title, description }) => (
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

      <section className="border-border/80 border-b">
        <div className="mx-auto max-w-7xl px-5 py-14 lg:px-8">
          <p className="text-primary font-mono text-xs font-semibold tracking-[0.18em] uppercase">
            Built for real research workflows
          </p>
          <div className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {audiences.map(([title, description]) => (
              <Card key={title}>
                <CardHeader>
                  <CardTitle className="text-base">{title}</CardTitle>
                  <CardDescription>{description}</CardDescription>
                </CardHeader>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {data ? (
        <section className="border-border/80 mx-auto max-w-7xl border-b px-5 py-16 lg:px-8">
          <div className="flex flex-wrap items-end justify-between gap-4">
            <div>
              <p className="text-primary font-mono text-xs font-semibold tracking-[0.18em] uppercase">
                Latest verified month
              </p>
              <h2 className="mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">
                {data.period.reporting_label}
              </h2>
            </div>
            <Button asChild variant="outline" size="sm">
              <Link href="/live">
                Full breakdown
                <ArrowRight className="size-4" aria-hidden="true" />
              </Link>
            </Button>
          </div>

          <div className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            <MetricCard
              label="Total net allocation"
              value={formatNaira(data.total_net)}
              detail={`Across ${data.covered_states} of ${data.expected_states} jurisdictions.`}
            />
            <MetricCard
              label="Coverage"
              value={`${data.covered_states} / ${data.expected_states}`}
              detail="Jurisdictions verified and published."
            />
            <MetricCard
              label="Source"
              value="OAGF"
              detail="Office of the Accountant-General of the Federation."
            />
          </div>

          <h3 className="mt-12 text-lg font-semibold">
            Largest net allocations
          </h3>
          <div className="mt-4 overflow-x-auto">
            <table className="w-full min-w-2xl border-collapse text-left text-sm">
              <thead>
                <tr className="border-border text-muted-foreground border-b">
                  <th className="py-3 pr-5 font-medium">#</th>
                  <th className="py-3 pr-5 font-medium">Jurisdiction</th>
                  <th className="py-3 font-medium">Net allocation</th>
                </tr>
              </thead>
              <tbody>
                {ranked.map((a, i) => (
                  <tr
                    key={a.state_code}
                    className="border-border border-b last:border-0"
                  >
                    <td className="text-muted-foreground py-3 pr-5 font-mono">
                      {i + 1}
                    </td>
                    <td className="py-3 pr-5">
                      <Link
                        href={`/states/${a.state_slug}`}
                        className="hover:text-primary font-medium transition-colors"
                      >
                        {a.state_name}
                      </Link>
                      <span className="text-muted-foreground ml-2 text-xs">
                        {a.geopolitical_zone}
                      </span>
                    </td>
                    <td className="py-3 font-mono font-semibold">
                      {formatNaira(a.net_allocation)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      ) : null}

      <section className="border-border/80 border-b">
        <div className="mx-auto grid max-w-7xl gap-8 px-5 py-16 lg:grid-cols-2 lg:px-8">
          <div>
            <div className="flex items-end justify-between gap-4">
              <div>
                <p className="text-primary font-mono text-xs font-semibold tracking-[0.18em] uppercase">
                  Latest fiscal events
                </p>
                <h2 className="mt-2 text-2xl font-semibold">Ledger changes</h2>
              </div>
              <Link
                href="/events"
                className="text-primary text-sm hover:underline"
              >
                Full stream
              </Link>
            </div>
            <div className="mt-5 space-y-3">
              {latestEvents.length ? (
                latestEvents.map((event) => (
                  <Card key={event.event_id}>
                    <CardHeader>
                      <CardTitle className="font-mono text-sm">
                        {event.jurisdiction.code} ·{' '}
                        {formatDate(event.detected_at.slice(0, 10))}
                      </CardTitle>
                      <CardDescription>{event.explanation}</CardDescription>
                    </CardHeader>
                  </Card>
                ))
              ) : (
                <p className="text-muted-foreground text-sm">
                  No evidence lifecycle events are currently published.
                </p>
              )}
            </div>
          </div>

          <div>
            <p className="text-primary font-mono text-xs font-semibold tracking-[0.18em] uppercase">
              Recent verified proofs
            </p>
            <h2 className="mt-2 text-2xl font-semibold">Portable evidence</h2>
            <div className="mt-5 space-y-3">
              {recentProofIds.length ? (
                recentProofIds.map((proofId) => (
                  <Link
                    key={proofId}
                    href={`/proofs/${encodeURIComponent(proofId)}`}
                    className="border-border hover:border-primary block rounded-lg border p-4 font-mono text-sm break-all transition-colors"
                  >
                    {proofId}
                  </Link>
                ))
              ) : (
                <p className="text-muted-foreground text-sm">
                  No proof objects are currently present in the event stream.
                </p>
              )}
            </div>
            <div className="mt-5 flex flex-wrap gap-3">
              <Button asChild variant="outline" size="sm">
                <Link href="/sources">Source registry</Link>
              </Button>
              <Button asChild variant="outline" size="sm">
                <Link href="/fiscal-design/verify">Verification interface</Link>
              </Button>
              <Button asChild variant="outline" size="sm">
                <a href="/api/v1/openapi.json">API schema</a>
              </Button>
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-5 py-16 lg:px-8">
        <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
          {destinations.map(({ href, icon: Icon, title, description }) => (
            <Link key={href} href={href} className="group">
              <Card className="group-hover:border-primary/40 h-full transition-colors">
                <CardHeader>
                  <Icon className="text-primary size-5" aria-hidden="true" />
                  <CardTitle className="pt-3">{title}</CardTitle>
                  <CardDescription>{description}</CardDescription>
                </CardHeader>
              </Card>
            </Link>
          ))}
        </div>
        <div className="mt-10 flex flex-wrap items-center gap-3">
          <Button asChild>
            <Link href="/pilot?plan=analyst">
              Request licensed intelligence
            </Link>
          </Button>
          <span className="text-muted-foreground text-sm">
            gaiafacc@gailabai.com
          </span>
        </div>
        <p className="text-muted-foreground mt-8 text-sm">
          Every published figure is extracted from an official source and
          human-approved before it appears. Fiscal Pulse signals are descriptive
          allocation analytics, not credit ratings.{' '}
          <Link href="/methodology" className="hover:text-foreground underline">
            Read the methodology
          </Link>
          .
        </p>
      </section>
    </>
  )
}
