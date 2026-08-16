import {
  BarChart3,
  Download,
  FileCheck2,
  GitCompareArrows,
  ShieldCheck,
} from 'lucide-react'
import Link from 'next/link'

import { Button } from '@/components/ui/button'
import type { PublishedAnalytics } from '@/lib/analytics-api'
import { formatNaira } from '@/lib/format'
import type { NationalDistribution } from '@/lib/national-distribution-api'
import type { PublishedOverview } from '@/lib/published-api'

function shortNaira(value: string | null) {
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

function percentageChange(current: number, previous: number | null) {
  if (previous === null || previous === 0) return null
  return ((current - previous) / previous) * 100
}

function reconciliationTone(status: string) {
  if (status === 'reconciled') return 'text-emerald-700 dark:text-emerald-300'
  if (status === 'conflicted') return 'text-red-700 dark:text-red-300'
  return 'text-amber-700 dark:text-amber-300'
}

export function ResearchCommandCenter({
  overview,
  analytics,
  analyticsError = null,
  nationalHistory = [],
  nationalHistoryError = null,
}: {
  overview: PublishedOverview
  analytics: PublishedAnalytics | null
  analyticsError?: string | null
  nationalHistory?: NationalDistribution[]
  nationalHistoryError?: string | null
}) {
  const ranked = [...overview.allocations]
    .filter((item) => item.net_allocation)
    .sort((a, b) => Number(b.net_allocation) - Number(a.net_allocation))
    .slice(0, 8)
  const maxAllocation = Math.max(
    ...ranked.map((item) => Number(item.net_allocation ?? 0)),
    1,
  )
  const trend = analytics?.national_trend.slice(-12) ?? []
  const maxTrend = Math.max(...trend.map((item) => Number(item.total_net)), 1)
  const hasTrendHistory = trend.length > 1
  const trendUnavailable = analytics === null && analyticsError !== null
  const reconciliationByMonth = new Map(
    nationalHistory.map((item) => [item.revenue_month, item]),
  )
  const reconciliationEvidence = trend.flatMap((point) => {
    const evidence = reconciliationByMonth.get(point.revenue_month)
    return evidence ? [{ point, evidence }] : []
  })
  const missingReconciliationMonths = Math.max(
    trend.length - reconciliationEvidence.length,
    0,
  )

  return (
    <section className="border-border/80 border-b">
      <div className="mx-auto max-w-7xl px-5 py-16 lg:px-8 lg:py-20">
        <div className="flex flex-wrap items-end justify-between gap-5">
          <div className="max-w-3xl">
            <p className="text-primary font-mono text-xs font-semibold tracking-[0.18em] uppercase">
              Research command center
            </p>
            <h2 className="mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">
              Investigate the ledger, not just the headline number.
            </h2>
            <p className="text-muted-foreground mt-4 max-w-2xl text-sm leading-6">
              Rankings and trends below are derived only from published,
              governed records. Every research path remains linked to source
              evidence.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button asChild size="sm">
              <Link href="/account#exports">
                <Download className="size-4" aria-hidden="true" />
                Export data
              </Link>
            </Button>
            <Button asChild size="sm" variant="outline">
              <Link href="/compare">
                <GitCompareArrows className="size-4" aria-hidden="true" />
                Compare states
              </Link>
            </Button>
          </div>
        </div>

        <div className="mt-8 grid gap-5 xl:grid-cols-[1.25fr_0.75fr]">
          <div className="border-border bg-card rounded-xl border p-5 shadow-sm sm:p-6">
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="font-semibold">Largest net allocations</p>
                <p className="text-muted-foreground mt-1 text-sm">
                  {overview.period.reporting_label}
                </p>
              </div>
              <BarChart3 className="text-primary size-5" aria-hidden="true" />
            </div>
            <div className="mt-6 space-y-4">
              {ranked.map((item, index) => {
                const value = Number(item.net_allocation ?? 0)
                return (
                  <div key={item.state_code}>
                    <div className="flex items-center justify-between gap-4 text-sm">
                      <Link
                        href={`/states/${item.state_slug}`}
                        className="font-medium hover:underline"
                      >
                        {index + 1}. {item.state_name}
                      </Link>
                      <span className="font-mono font-semibold">
                        {shortNaira(item.net_allocation)}
                      </span>
                    </div>
                    <div className="bg-muted mt-2 h-2 overflow-hidden rounded-full">
                      <div
                        className="bg-primary h-full rounded-full transition-[width] duration-700"
                        style={{
                          width: `${Math.max((value / maxAllocation) * 100, 2)}%`,
                        }}
                      />
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          <div className="border-border bg-card rounded-xl border p-5 shadow-sm sm:p-6">
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="font-semibold">Evidence integrity</p>
                <p className="text-muted-foreground mt-1 text-sm">
                  Publication controls at a glance
                </p>
              </div>
              <ShieldCheck className="text-primary size-5" aria-hidden="true" />
            </div>
            <dl className="mt-6 grid gap-4 text-sm">
              <div className="border-border flex items-center justify-between border-b pb-4">
                <dt className="text-muted-foreground">Coverage</dt>
                <dd className="font-mono font-semibold">
                  {overview.covered_states}/{overview.expected_states}
                </dd>
              </div>
              <div className="border-border flex items-center justify-between border-b pb-4">
                <dt className="text-muted-foreground">Source organization</dt>
                <dd className="font-medium">
                  {overview.source.source_organization}
                </dd>
              </div>
              <div className="border-border border-b pb-4">
                <dt className="text-muted-foreground">Source SHA-256</dt>
                <dd className="mt-2 font-mono text-xs break-all">
                  {overview.source.sha256}
                </dd>
              </div>
            </dl>
            <div className="mt-5 grid gap-2 sm:grid-cols-2 xl:grid-cols-1">
              <Button asChild variant="outline" size="sm">
                <Link href="/sources">
                  <FileCheck2 className="size-4" aria-hidden="true" />
                  Open evidence registry
                </Link>
              </Button>
              <Button asChild variant="outline" size="sm">
                <Link href="/fiscal-design/verify">Verify a manifest</Link>
              </Button>
            </div>
          </div>
        </div>

        <div className="border-border bg-card mt-5 rounded-xl border p-5 shadow-sm sm:p-6">
          <div className="flex flex-wrap items-end justify-between gap-3">
            <div>
              <p className="font-semibold">Published national trend</p>
              <p className="text-muted-foreground mt-1 text-sm">
                Jurisdiction ledger totals with official national reconciliation
                evidence where a governed communiqué is published
              </p>
            </div>
            <Link
              href="/national-reconciliation"
              className="text-primary text-sm font-medium hover:underline"
            >
              Open National Reconciliation →
            </Link>
          </div>

          {hasTrendHistory ? (
            <>
              <div
                className="mt-7 flex h-64 items-end gap-2 overflow-x-auto pb-2"
                aria-label="Published national allocation trend"
              >
                {trend.map((point, index) => {
                  const value = Number(point.total_net)
                  const previous =
                    index > 0 ? Number(trend[index - 1].total_net) : null
                  const change = percentageChange(value, previous)
                  const height = Math.max((value / maxTrend) * 100, 6)
                  return (
                    <div
                      key={point.revenue_month}
                      className="group flex h-full min-w-16 flex-1 flex-col items-center justify-end gap-2"
                      title={`${point.reporting_label}: ${formatNaira(point.total_net)}`}
                    >
                      <div className="min-h-10 text-center">
                        <span className="block font-mono text-[0.68rem] font-semibold">
                          {shortNaira(point.total_net)}
                        </span>
                        {change !== null ? (
                          <span className="text-muted-foreground mt-0.5 block font-mono text-[0.62rem]">
                            {change >= 0 ? '+' : ''}
                            {change.toFixed(1)}%
                          </span>
                        ) : null}
                      </div>
                      <div
                        className="bg-primary/80 hover:bg-primary w-full max-w-14 rounded-t-md transition-colors"
                        style={{ height: `${height}%` }}
                        aria-hidden="true"
                      />
                      <span className="text-muted-foreground text-[0.65rem] whitespace-nowrap">
                        {new Intl.DateTimeFormat('en-NG', {
                          month: 'short',
                          timeZone: 'UTC',
                        }).format(new Date(`${point.revenue_month}T00:00:00Z`))}
                      </span>
                    </div>
                  )
                })}
              </div>

              <div className="border-border mt-5 border-t pt-5">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold">
                      National reconciliation evidence
                    </p>
                    <p className="text-muted-foreground mt-1 text-xs">
                      {reconciliationEvidence.length}/{trend.length} trend months
                      have independently published national evidence.
                    </p>
                  </div>
                  <span className="bg-muted rounded-full px-3 py-1 font-mono text-xs">
                    {missingReconciliationMonths} awaiting evidence
                  </span>
                </div>

                {nationalHistoryError ? (
                  <div className="border-border bg-muted/20 mt-4 rounded-lg border border-dashed p-5">
                    <p className="font-medium">
                      National reconciliation history unavailable
                    </p>
                    <p className="text-muted-foreground mt-2 text-sm leading-6">
                      The trend remains a governed jurisdiction-ledger series.
                      GaiaFAAC will not infer official national comparison values
                      while the reconciliation service is unavailable.
                    </p>
                  </div>
                ) : reconciliationEvidence.length === 0 ? (
                  <div className="border-border bg-muted/20 mt-4 rounded-lg border border-dashed p-5">
                    <p className="font-medium">
                      No governed national comparison is published for these
                      months yet
                    </p>
                    <p className="text-muted-foreground mt-2 max-w-3xl text-sm leading-6">
                      The bars above are still valid published
                      jurisdiction-ledger totals. National communiqué values
                      appear here only after their independent evidence has
                      passed GaiaFAAC review and publication controls.
                    </p>
                  </div>
                ) : (
                  <>
                    <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                      {reconciliationEvidence.map(({ point, evidence }) => {
                        const reconciliation =
                          evidence.jurisdiction_reconciliation
                        return (
                          <div
                            key={`reconciliation-${point.revenue_month}`}
                            className="border-border bg-muted/20 rounded-lg border p-3"
                          >
                            <p className="text-muted-foreground text-[0.65rem] uppercase">
                              {new Intl.DateTimeFormat('en-NG', {
                                month: 'short',
                                year: 'numeric',
                                timeZone: 'UTC',
                              }).format(
                                new Date(`${point.revenue_month}T00:00:00Z`),
                              )}
                            </p>
                            <p
                              className={`mt-2 text-xs font-semibold uppercase ${reconciliationTone(
                                reconciliation.status,
                              )}`}
                            >
                              {reconciliation.status}
                            </p>
                            <p className="mt-2 font-mono text-xs">
                              Official:{' '}
                              {shortNaira(reconciliation.observed_total)}
                            </p>
                            <p className="text-muted-foreground mt-1 font-mono text-[0.68rem]">
                              Variance: {shortNaira(reconciliation.variance)}
                            </p>
                          </div>
                        )
                      })}
                    </div>
                    {missingReconciliationMonths > 0 ? (
                      <p className="text-muted-foreground mt-3 text-xs leading-5">
                        {missingReconciliationMonths} additional trend months do
                        not yet have governed national comparison evidence. No
                        replacement values are inferred.
                      </p>
                    ) : null}
                  </>
                )}
              </div>
            </>
          ) : (
            <div className="border-border bg-muted/20 mt-7 rounded-lg border border-dashed p-6 sm:p-8">
              <p className="font-medium">
                {trendUnavailable
                  ? 'Trend data unavailable'
                  : 'Insufficient published history'}
              </p>
              <p className="text-muted-foreground mt-2 max-w-2xl text-sm leading-6">
                {trendUnavailable
                  ? 'The governed analytics service could not be read. GaiaFAAC will not substitute placeholder trend values.'
                  : `GaiaFAAC needs at least two governed published periods before it draws a trend. ${
                      trend.length === 1
                        ? 'One period is currently available.'
                        : 'No trend periods are currently available.'
                    }`}
              </p>
            </div>
          )}
        </div>
      </div>
    </section>
  )
}
