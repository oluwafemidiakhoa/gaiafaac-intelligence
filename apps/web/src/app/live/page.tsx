import {
  Activity,
  ArrowRight,
  FileCheck2,
  GitCompareArrows,
  Radar,
  ShieldCheck,
  Sparkles,
  TrendingDown,
  TrendingUp,
} from 'lucide-react'
import type { Metadata } from 'next'
import Link from 'next/link'

import { DataUnavailable } from '@/components/data-unavailable'
import { GaiaTerminalSearch } from '@/components/gaia-terminal-search'
import { StatusPill } from '@/components/status-pill'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { getPublishedAnalytics } from '@/lib/analytics-api'
import { formatDate, formatNaira } from '@/lib/format'
import { getLatestNationalDistribution } from '@/lib/national-distribution-api'
import { getPublishedOverview } from '@/lib/published-api'

export const metadata: Metadata = {
  title: 'Live Fiscal Board',
  description:
    'Live governed Nigerian fiscal intelligence with source evidence, jurisdiction movements and national reconciliation status.',
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
  if (Math.abs(amount) >= 1_000_000)
    return `₦${(amount / 1_000_000).toFixed(1)}M`
  return formatNaira(value)
}

function reconciliationClass(status: string) {
  if (status === 'reconciled')
    return 'border-emerald-300/30 bg-emerald-300/10 text-emerald-100'
  if (status === 'conflicted')
    return 'border-red-300/30 bg-red-300/10 text-red-100'
  return 'border-amber-300/30 bg-amber-300/10 text-amber-100'
}

export default async function LivePage() {
  const [overviewResult, analyticsResult, nationalResult] = await Promise.all([
    getPublishedOverview(),
    getPublishedAnalytics(),
    getLatestNationalDistribution(),
  ])
  const data = overviewResult.data
  const analytics = analyticsResult.data
  const national = nationalResult.data

  if (!data) {
    return (
      <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
        <p className="text-primary font-mono text-xs font-semibold tracking-[0.18em] uppercase">
          Live fiscal board
        </p>
        <h1 className="mt-4 max-w-4xl text-4xl font-semibold tracking-[-0.04em] text-balance sm:text-5xl">
          Governed intelligence appears only after publication.
        </h1>
        <div className="mt-10">
          <DataUnavailable
            message={
              overviewResult.error ?? 'No published FAAC data is available yet.'
            }
          />
        </div>
      </div>
    )
  }

  const latestTrend = analytics?.national_trend.at(-1) ?? null
  const previousTrend = analytics?.national_trend.at(-2) ?? null
  const nationalChange =
    latestTrend && previousTrend && Number(previousTrend.total_net) !== 0
      ? ((Number(latestTrend.total_net) - Number(previousTrend.total_net)) /
          Number(previousTrend.total_net)) *
        100
      : null
  const biggestMovers = analytics?.biggest_movers.slice(0, 4) ?? []
  const topStates =
    analytics?.top_states.slice(0, 5) ??
    [...data.allocations]
      .filter((item) => item.net_allocation)
      .sort(
        (left, right) =>
          Number(right.net_allocation ?? 0) - Number(left.net_allocation ?? 0),
      )
      .slice(0, 5)

  return (
    <div>
      <section className="relative overflow-hidden border-b border-emerald-900/25 bg-[radial-gradient(circle_at_top_left,rgba(16,185,129,0.18),transparent_32%),linear-gradient(135deg,#06110d_0%,#081b14_52%,#0a1712_100%)] text-white">
        <div className="pointer-events-none absolute inset-0 [background-image:linear-gradient(rgba(255,255,255,.045)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,.045)_1px,transparent_1px)] [background-size:40px_40px]" />
        <div className="relative mx-auto max-w-7xl px-5 py-14 lg:px-8 lg:py-16">
          <div className="flex flex-wrap items-center gap-3">
            <span className="rounded-full border border-emerald-300/25 bg-emerald-300/10 px-3 py-1 font-mono text-xs font-semibold tracking-[0.16em] text-emerald-100 uppercase">
              Live · source verified
            </span>
            <StatusPill tone="success">Verified · published</StatusPill>
            <span className="text-sm text-white/60">
              Revenue month {formatDate(data.period.revenue_month)}
            </span>
          </div>

          <div className="mt-7 grid gap-10 xl:grid-cols-[1fr_23rem] xl:items-end">
            <div>
              <p className="font-mono text-xs tracking-[0.16em] text-emerald-200/75 uppercase">
                Nigeria fiscal intelligence
              </p>
              <h1 className="mt-3 max-w-5xl text-4xl font-semibold tracking-[-0.05em] text-balance sm:text-5xl lg:text-6xl">
                Know what changed. Trace exactly why.
              </h1>
              <p className="mt-5 max-w-3xl text-base leading-7 text-emerald-50/70 sm:text-lg">
                Governed Federation Account evidence, jurisdiction movement and
                reconciliation signals in one research board. Missing figures
                remain missing; every published number stays attached to its
                source.
              </p>
            </div>

            <div className="rounded-2xl border border-white/15 bg-white/7 p-5 backdrop-blur-sm">
              <p className="text-xs font-medium tracking-[0.14em] text-white/55 uppercase">
                Published state-ledger net total
              </p>
              <p className="mt-3 text-4xl font-semibold tracking-tight">
                {compactNaira(data.total_net)}
              </p>
              <div className="mt-4 flex flex-wrap items-center gap-2 text-xs">
                <span className="rounded-full border border-white/15 bg-white/5 px-2.5 py-1 text-white/70">
                  {data.covered_states}/{data.expected_states} jurisdictions
                </span>
                {nationalChange !== null ? (
                  <span
                    className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-1 ${
                      nationalChange >= 0
                        ? 'border-emerald-300/25 bg-emerald-300/10 text-emerald-100'
                        : 'border-red-300/25 bg-red-300/10 text-red-100'
                    }`}
                  >
                    {nationalChange >= 0 ? (
                      <TrendingUp className="size-3" aria-hidden="true" />
                    ) : (
                      <TrendingDown className="size-3" aria-hidden="true" />
                    )}
                    {nationalChange >= 0 ? '+' : ''}
                    {nationalChange.toFixed(1)}% vs prior published period
                  </span>
                ) : null}
              </div>
            </div>
          </div>

          <div className="mt-8 grid gap-3 md:grid-cols-3">
            <div className="rounded-xl border border-white/12 bg-white/5 p-4">
              <p className="text-xs text-white/45">Source organization</p>
              <p className="mt-2 font-medium">{data.source.source_organization}</p>
              <p className="mt-1 truncate font-mono text-xs text-white/50">
                {data.source.original_filename}
              </p>
            </div>
            <div className="rounded-xl border border-white/12 bg-white/5 p-4">
              <p className="text-xs text-white/45">National reconciliation</p>
              {national ? (
                <span
                  className={`mt-2 inline-flex rounded-full border px-2.5 py-1 font-mono text-xs font-semibold uppercase ${reconciliationClass(
                    national.jurisdiction_reconciliation.status,
                  )}`}
                >
                  {national.jurisdiction_reconciliation.status}
                </span>
              ) : (
                <p className="mt-2 font-medium text-white/70">Awaiting evidence</p>
              )}
            </div>
            <div className="rounded-xl border border-white/12 bg-white/5 p-4">
              <p className="text-xs text-white/45">Evidence fingerprint</p>
              <p className="mt-2 truncate font-mono text-xs text-white/70">
                {data.source.sha256}
              </p>
              <Link
                href="/sources"
                className="mt-2 inline-block text-xs font-medium text-emerald-200 hover:underline"
              >
                Inspect evidence →
              </Link>
            </div>
          </div>
        </div>
      </section>

      <section className="border-border/80 border-b">
        <div className="mx-auto max-w-7xl px-5 py-10 lg:px-8">
          <GaiaTerminalSearch
            jurisdictions={data.allocations}
            periodLabel={data.period.reporting_label}
            compact
          />
        </div>
      </section>

      <section className="border-border/80 border-b">
        <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8">
          <div className="flex flex-wrap items-end justify-between gap-4">
            <div>
              <p className="text-primary font-mono text-xs font-semibold tracking-[0.18em] uppercase">
                What matters now
              </p>
              <h2 className="mt-3 text-3xl font-semibold tracking-tight">
                Movement, leaders and evidence state.
              </h2>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button asChild size="sm" variant="outline">
                <Link href="/fiscal-watch">
                  <Radar className="size-4" aria-hidden="true" />
                  Open Fiscal Watch
                </Link>
              </Button>
              <Button asChild size="sm">
                <Link href="/gaia-analyst">
                  <Sparkles className="size-4" aria-hidden="true" />
                  Ask Gaia
                </Link>
              </Button>
            </div>
          </div>

          <div className="mt-7 grid gap-5 xl:grid-cols-[1.05fr_0.95fr]">
            <Card>
              <CardHeader>
                <CardTitle>Largest latest allocations</CardTitle>
                <CardDescription>
                  Published governed state-ledger values for{' '}
                  {data.period.reporting_label}.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {topStates.map((state, index) => (
                    <div
                      key={state.state_code}
                      className="border-border flex items-center justify-between gap-4 border-b pb-3 last:border-0 last:pb-0"
                    >
                      <div className="min-w-0">
                        <Link
                          href={`/states/${state.state_slug}`}
                          className="font-medium hover:underline"
                        >
                          {index + 1}. {state.state_name}
                        </Link>
                        <p className="text-muted-foreground mt-1 text-xs">
                          {state.geopolitical_zone}
                        </p>
                      </div>
                      <p className="shrink-0 font-mono font-semibold">
                        {compactNaira(state.net_allocation)}
                      </p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Biggest published movements</CardTitle>
                <CardDescription>
                  Deterministic period-over-period changes from governed records.
                </CardDescription>
              </CardHeader>
              <CardContent>
                {biggestMovers.length > 0 ? (
                  <div className="space-y-3">
                    {biggestMovers.map((mover) => (
                      <div
                        key={mover.state_slug}
                        className="border-border flex items-center justify-between gap-4 border-b pb-3 last:border-0 last:pb-0"
                      >
                        <div>
                          <Link
                            href={`/states/${mover.state_slug}`}
                            className="font-medium hover:underline"
                          >
                            {mover.state_name}
                          </Link>
                          <p className="text-muted-foreground mt-1 font-mono text-xs">
                            {compactNaira(mover.previous_net)} →{' '}
                            {compactNaira(mover.current_net)}
                          </p>
                        </div>
                        <span
                          className={`font-mono text-sm font-semibold ${
                            mover.pct_change >= 0
                              ? 'text-emerald-700 dark:text-emerald-300'
                              : 'text-red-700 dark:text-red-300'
                          }`}
                        >
                          {mover.pct_change >= 0 ? '+' : ''}
                          {mover.pct_change.toFixed(1)}%
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-muted-foreground text-sm leading-6">
                    At least two governed periods are required before GaiaFAAC
                    presents movement intelligence. No substitute movement is
                    inferred.
                  </p>
                )}
              </CardContent>
            </Card>
          </div>

          <div className="mt-5 grid gap-5 md:grid-cols-3">
            <Link
              href="/national-reconciliation"
              className="border-border bg-card hover:bg-muted/40 rounded-xl border p-5 transition-colors"
            >
              <ShieldCheck className="text-primary size-5" aria-hidden="true" />
              <p className="mt-4 font-semibold">Reconcile the headline</p>
              <p className="text-muted-foreground mt-2 text-sm leading-6">
                Compare jurisdiction-ledger totals with independently governed
                national evidence.
              </p>
              <span className="text-primary mt-4 inline-flex items-center gap-1 text-sm font-medium">
                Open reconciliation <ArrowRight className="size-3.5" />
              </span>
            </Link>
            <Link
              href="/compare"
              className="border-border bg-card hover:bg-muted/40 rounded-xl border p-5 transition-colors"
            >
              <GitCompareArrows
                className="text-primary size-5"
                aria-hidden="true"
              />
              <p className="mt-4 font-semibold">Compare jurisdictions</p>
              <p className="text-muted-foreground mt-2 text-sm leading-6">
                Put multiple states side by side without filling unavailable
                values.
              </p>
              <span className="text-primary mt-4 inline-flex items-center gap-1 text-sm font-medium">
                Start comparison <ArrowRight className="size-3.5" />
              </span>
            </Link>
            <Link
              href="/events"
              className="border-border bg-card hover:bg-muted/40 rounded-xl border p-5 transition-colors"
            >
              <Activity className="text-primary size-5" aria-hidden="true" />
              <p className="mt-4 font-semibold">Follow fiscal events</p>
              <p className="text-muted-foreground mt-2 text-sm leading-6">
                Inspect evidence lifecycle, publication and revision activity.
              </p>
              <span className="text-primary mt-4 inline-flex items-center gap-1 text-sm font-medium">
                Open event stream <ArrowRight className="size-3.5" />
              </span>
            </Link>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-5 py-12 lg:px-8">
        <Card>
          <CardHeader>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <CardTitle>Published jurisdiction ledger</CardTitle>
                <CardDescription>{data.period.reporting_label}</CardDescription>
              </div>
              <Button asChild size="sm" variant="outline">
                <Link href="/sources">
                  <FileCheck2 className="size-4" aria-hidden="true" />
                  Source registry
                </Link>
              </Button>
            </div>
          </CardHeader>
          <CardContent className="overflow-x-auto">
            <table className="w-full min-w-3xl border-collapse text-left text-sm">
              <thead>
                <tr className="border-border border-b">
                  <th className="py-3 pr-5 font-medium">Jurisdiction</th>
                  <th className="py-3 pr-5 font-medium">Gross</th>
                  <th className="py-3 pr-5 font-medium">Deductions</th>
                  <th className="py-3 font-medium">Net</th>
                </tr>
              </thead>
              <tbody>
                {data.allocations.map((allocation) => (
                  <tr
                    key={allocation.state_code}
                    className="border-border border-b last:border-0"
                  >
                    <td className="py-4 pr-5">
                      <Link
                        href={`/states/${allocation.state_slug}`}
                        className="font-medium hover:underline"
                      >
                        {allocation.state_name}
                      </Link>
                      <p className="text-muted-foreground mt-1 text-xs">
                        {allocation.geopolitical_zone}
                      </p>
                    </td>
                    <td className="py-4 pr-5 font-mono">
                      {formatNaira(allocation.gross_total)}
                    </td>
                    <td className="py-4 pr-5 font-mono">
                      {formatNaira(allocation.total_deductions)}
                    </td>
                    <td className="py-4 font-mono font-semibold">
                      {formatNaira(allocation.net_allocation)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>

        <Card className="mt-5 bg-muted/20">
          <CardHeader>
            <CardTitle className="text-base">Evidence provenance</CardTitle>
            <CardDescription>
              Every value above remains tied to the governed source below.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <dl className="grid gap-5 text-sm md:grid-cols-3">
              <div>
                <dt className="text-muted-foreground">Organization</dt>
                <dd className="mt-1 font-medium">
                  {data.source.source_organization}
                </dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Document</dt>
                <dd className="mt-1 font-mono text-xs break-all">
                  {data.source.original_filename}
                </dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Report published</dt>
                <dd className="mt-1 font-medium">
                  {formatDate(data.source.publication_date)}
                </dd>
              </div>
              <div className="md:col-span-3">
                <dt className="text-muted-foreground">SHA-256</dt>
                <dd className="mt-1 font-mono text-xs break-all">
                  {data.source.sha256}
                </dd>
              </div>
            </dl>
            {data.source.source_url ? (
              <a
                href={data.source.source_url}
                target="_blank"
                rel="noreferrer"
                className="text-primary mt-5 inline-block text-sm font-medium hover:underline"
              >
                View original source →
              </a>
            ) : null}
          </CardContent>
        </Card>
      </section>
    </div>
  )
}
