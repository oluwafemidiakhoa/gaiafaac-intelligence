import { ArrowUpRight } from 'lucide-react'
import type { Metadata } from 'next'
import Link from 'next/link'

import { DataUnavailable } from '@/components/data-unavailable'
import { MetricCard } from '@/components/metric-card'
import { PageHeader } from '@/components/page-header'
import { StatusPill } from '@/components/status-pill'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { formatDate, formatNaira } from '@/lib/format'
import { getPublishedOverview } from '@/lib/published-api'

export const metadata: Metadata = { title: 'National overview' }
export const dynamic = 'force-dynamic'

export default async function OverviewPage() {
  const result = await getPublishedOverview()
  const data = result.data

  return (
    <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
      <PageHeader
        eyebrow="National overview"
        title="Latest verified FAAC distribution"
        description="The most recent human-approved allocation month. Every figure traces to the official OAGF source; unavailable values are left blank, never inferred."
      />

      {data === null ? (
        <div className="mt-10">
          <DataUnavailable
            message={result.error ?? 'No verified month is published yet.'}
          />
        </div>
      ) : (
        <>
          <div className="mt-8 flex flex-wrap items-center gap-3">
            <StatusPill tone="success">Verified · published</StatusPill>
            <span className="text-muted-foreground text-sm">
              Revenue month {formatDate(data.period.revenue_month)}
            </span>
            <Link
              href="/sources"
              className="text-primary text-sm font-medium hover:underline"
            >
              Source lineage
            </Link>
          </div>

          <div className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <MetricCard
              label="Total net allocation"
              value={formatNaira(data.total_net)}
              detail={data.period.reporting_label}
            />
            <MetricCard
              label="Total gross"
              value={formatNaira(data.total_gross)}
              detail="Unavailable where a jurisdiction's gross is not published."
            />
            <MetricCard
              label="Total deductions"
              value={formatNaira(data.total_deductions)}
              detail="Applied at source."
            />
            <MetricCard
              label="Coverage"
              value={`${data.covered_states} / ${data.expected_states}`}
              detail="Jurisdictions verified and published."
            />
          </div>

          <Card className="mt-8">
            <CardHeader>
              <CardTitle>State allocations</CardTitle>
              <CardDescription>{data.period.reporting_label}</CardDescription>
            </CardHeader>
            <CardContent className="overflow-x-auto">
              <table className="w-full min-w-3xl border-collapse text-left text-sm">
                <thead>
                  <tr className="border-border border-b">
                    <th className="py-3 pr-5 font-medium">State</th>
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
                          className="hover:text-primary inline-flex items-center gap-1 font-medium"
                          href={`/states/${allocation.state_slug}`}
                        >
                          {allocation.state_name}
                          <ArrowUpRight
                            className="size-3.5"
                            aria-hidden="true"
                          />
                        </Link>
                        <span className="text-muted-foreground mt-1 block text-xs">
                          {allocation.geopolitical_zone}
                        </span>
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
        </>
      )}
    </div>
  )
}
