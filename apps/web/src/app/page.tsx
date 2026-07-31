import { ArrowRight, GitCompareArrows, Map, Radio } from 'lucide-react'
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
import { getPublishedOverview } from '@/lib/published-api'

export const metadata: Metadata = {
  title: 'GaiaFAAC Intelligence — source-linked Nigerian public-revenue data',
}
export const dynamic = 'force-dynamic'

const destinations = [
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

export default async function Home() {
  const result = await getPublishedOverview()
  const data = result.data
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
              Source-linked public-revenue intelligence
            </p>
            <h1 className="text-5xl font-semibold tracking-[-0.045em] text-balance sm:text-6xl lg:text-7xl">
              Nigeria’s Federation Account, verified and traceable
            </h1>
            <p className="text-muted-foreground mt-7 max-w-2xl text-lg leading-8 text-pretty">
              Every state’s monthly FAAC allocation — extracted from the
              official OAGF disbursement report, reconciled, and human-approved
              before publication. Every figure traces back to its source
              document by SHA-256.
            </p>
            <div className="mt-9 flex flex-col gap-3 sm:flex-row">
              <Button asChild size="lg">
                <Link href="/live">
                  See the latest verified data
                  <ArrowRight className="size-4" aria-hidden="true" />
                </Link>
              </Button>
              <Button asChild size="lg" variant="outline">
                <Link href="/methodology">How it’s verified</Link>
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
                    Total net allocation ·{' '}
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

      <section className="mx-auto max-w-7xl px-5 py-16 lg:px-8">
        <div className="grid gap-5 md:grid-cols-3">
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
        <p className="text-muted-foreground mt-8 text-sm">
          Every figure is extracted from the official OAGF report and
          human-approved before it appears.{' '}
          <Link href="/methodology" className="hover:text-foreground underline">
            Read the methodology
          </Link>
          .
        </p>
      </section>
    </>
  )
}
