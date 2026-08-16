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

export function ResearchCommandCenter({
  overview,
  analytics,
}: {
  overview: PublishedOverview
  analytics: PublishedAnalytics | null
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
              human-reviewed records. Every research path remains linked to
              source evidence.
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

        {trend.length > 1 ? (
          <div className="border-border bg-card mt-5 rounded-xl border p-5 shadow-sm sm:p-6">
            <div className="flex flex-wrap items-end justify-between gap-3">
              <div>
                <p className="font-semibold">Published national trend</p>
                <p className="text-muted-foreground mt-1 text-sm">
                  Monthly state net allocations across available published
                  periods
                </p>
              </div>
              <Link
                href="/fiscal-pulse"
                className="text-primary text-sm font-medium hover:underline"
              >
                Open Fiscal Pulse →
              </Link>
            </div>
            <div className="mt-7 flex h-48 items-end gap-2 overflow-x-auto pb-2">
              {trend.map((point) => {
                const value = Number(point.total_net)
                const height = Math.max((value / maxTrend) * 100, 6)
                return (
                  <div
                    key={point.revenue_month}
                    className="group flex min-w-12 flex-1 flex-col items-center justify-end gap-2"
                    title={`${point.reporting_label}: ${formatNaira(point.total_net)}`}
                  >
                    <span className="text-muted-foreground hidden text-[0.65rem] group-hover:block">
                      {shortNaira(point.total_net)}
                    </span>
                    <div
                      className="bg-primary/80 hover:bg-primary w-full max-w-14 rounded-t-md transition-colors"
                      style={{ height: `${height}%` }}
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
          </div>
        ) : null}
      </div>
    </section>
  )
}
