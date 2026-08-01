import type { Metadata } from 'next'
import Link from 'next/link'

import { DataUnavailable } from '@/components/data-unavailable'
import { MetricCard } from '@/components/metric-card'
import { PageHeader } from '@/components/page-header'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { formatNaira } from '@/lib/format'
import { getPublishedAnalytics } from '@/lib/analytics-api'

export const metadata: Metadata = { title: 'Insights' }
export const dynamic = 'force-dynamic'

function compactNaira(value: string): string {
  const n = Number(value)
  if (n >= 1e12) return `₦${(n / 1e12).toFixed(1)}tn`
  if (n >= 1e9) return `₦${(n / 1e9).toFixed(1)}bn`
  if (n >= 1e6) return `₦${(n / 1e6).toFixed(1)}m`
  return `₦${n.toFixed(0)}`
}

function monthLabel(iso: string): string {
  return new Date(iso).toLocaleDateString('en-GB', {
    month: 'short',
    year: '2-digit',
  })
}

export default async function InsightsPage() {
  const result = await getPublishedAnalytics()
  const data = result.data
  const hasData = data && data.months_published > 0
  const maxNet = hasData
    ? Math.max(...data.national_trend.map((t) => Number(t.total_net)))
    : 0

  return (
    <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
      <PageHeader
        eyebrow="Insights"
        title="Verified FAAC allocations over time"
        description="Computed only from published, human-approved records. Movements compare the two most recent published months (which may not be calendar-consecutive)."
      />

      {!hasData ? (
        <div className="mt-10">
          <DataUnavailable
            message={result.error ?? 'No verified months are published yet.'}
          />
        </div>
      ) : (
        <>
          <div className="mt-8 grid gap-4 sm:grid-cols-3">
            <MetricCard
              label="Months published"
              value={String(data.months_published)}
              detail="Verified and human-approved."
            />
            <MetricCard
              label="Latest total net"
              value={formatNaira(
                data.national_trend[data.national_trend.length - 1].total_net,
              )}
              detail={data.latest_period_label ?? ''}
            />
            <MetricCard
              label="Coverage"
              value="37 / 37"
              detail="Jurisdictions per published month."
            />
          </div>

          <Card className="mt-8">
            <CardHeader>
              <CardTitle>National net allocation by month</CardTitle>
              <CardDescription>
                Total net shared across all 37 jurisdictions, per published
                month.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex h-52 items-end gap-3 overflow-x-auto pb-2">
                {data.national_trend.map((t) => (
                  <div
                    key={t.revenue_month}
                    className="flex min-w-14 flex-1 flex-col items-center gap-2"
                  >
                    <span className="text-muted-foreground font-mono text-[0.65rem]">
                      {compactNaira(t.total_net)}
                    </span>
                    <div
                      className="bg-primary/80 hover:bg-primary w-full rounded-t transition-colors"
                      style={{
                        height: `${Math.max(6, (Number(t.total_net) / maxNet) * 100)}%`,
                      }}
                      title={`${t.reporting_label}: ${formatNaira(t.total_net)}`}
                    />
                    <span className="text-muted-foreground text-xs">
                      {monthLabel(t.revenue_month)}
                    </span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <div className="mt-8 grid gap-8 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Largest allocations</CardTitle>
                <CardDescription>{data.latest_period_label}</CardDescription>
              </CardHeader>
              <CardContent className="overflow-x-auto">
                <table className="w-full border-collapse text-left text-sm">
                  <tbody>
                    {data.top_states.map((s, i) => (
                      <tr
                        key={s.state_code}
                        className="border-border border-b last:border-0"
                      >
                        <td className="text-muted-foreground py-3 pr-4 font-mono">
                          {i + 1}
                        </td>
                        <td className="py-3 pr-4">
                          <Link
                            href={`/states/${s.state_slug}`}
                            className="hover:text-primary font-medium"
                          >
                            {s.state_name}
                          </Link>
                        </td>
                        <td className="py-3 text-right font-mono font-semibold">
                          {formatNaira(s.net_allocation)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Biggest movers</CardTitle>
                <CardDescription>
                  Change vs. the previous published month.
                </CardDescription>
              </CardHeader>
              <CardContent className="overflow-x-auto">
                {data.biggest_movers.length === 0 ? (
                  <p className="text-muted-foreground text-sm">
                    At least two published months are needed to compute movers.
                  </p>
                ) : (
                  <table className="w-full border-collapse text-left text-sm">
                    <tbody>
                      {data.biggest_movers.map((m) => (
                        <tr
                          key={m.state_slug}
                          className="border-border border-b last:border-0"
                        >
                          <td className="py-3 pr-4">
                            <Link
                              href={`/states/${m.state_slug}`}
                              className="hover:text-primary font-medium"
                            >
                              {m.state_name}
                            </Link>
                          </td>
                          <td className="py-3 pr-4 text-right font-mono">
                            {formatNaira(m.current_net)}
                          </td>
                          <td
                            className={`py-3 text-right font-mono font-semibold ${
                              m.pct_change >= 0
                                ? 'text-emerald-600'
                                : 'text-red-600'
                            }`}
                          >
                            {m.pct_change >= 0 ? '+' : ''}
                            {m.pct_change.toFixed(1)}%
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </CardContent>
            </Card>
          </div>

          <p className="text-muted-foreground mt-8 text-xs">{data.note}</p>
        </>
      )}
    </div>
  )
}
