import { ArrowUpRight } from 'lucide-react'
import type { Metadata } from 'next'
import Link from 'next/link'

import { DataUnavailable } from '@/components/data-unavailable'
import { DemoBanner } from '@/components/demo-banner'
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
import { getDemoOverview } from '@/lib/demo-api'
import { formatDate, formatNaira, humanize } from '@/lib/format'

export const metadata: Metadata = { title: 'Demo national overview' }
export const dynamic = 'force-dynamic'

export default async function OverviewPage() {
  const result = await getDemoOverview()

  return (
    <>
      <DemoBanner note="This dashboard summarizes a three-state synthetic sample, not Nigeria as a whole." />
      <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
        <PageHeader
          eyebrow="Demo national dashboard"
          title="A partial sample that shows its limits"
          description="The cards below total only the labelled demo rows. They are intentionally not presented as national distribution figures."
        />

        {result.data === null ? (
          <div className="mt-10">
            <DataUnavailable
              message={result.error ?? 'The labelled demo dataset is unavailable.'}
            />
          </div>
        ) : (
          <>
            <div className="mt-8 flex flex-wrap items-center gap-3">
              <StatusPill tone="demo">Demo data</StatusPill>
              <StatusPill>
                {humanize(result.data.period.verification_status)}
              </StatusPill>
              <span className="text-muted-foreground text-sm">
                Revenue month {formatDate(result.data.period.revenue_month)}
              </span>
              <Link
                href="/sources"
                className="text-primary text-sm font-medium hover:underline"
              >
                View demo source lineage
              </Link>
            </div>

            <div className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
              <MetricCard
                label="Demo sample net"
                value={formatNaira(result.data.sample_net_total)}
                detail="Sum of three synthetic net allocations."
              />
              <MetricCard
                label="Demo sample gross"
                value={formatNaira(result.data.sample_gross_total)}
                detail="Not a national gross distribution."
              />
              <MetricCard
                label="Demo deductions"
                value={formatNaira(result.data.sample_deductions_total)}
                detail="Synthetic deductions across the sample."
              />
              <MetricCard
                label="Coverage"
                value={`${result.data.covered_states} / ${result.data.expected_states}`}
                detail="Jurisdictions with a labelled demo allocation."
              />
            </div>

            <Card className="mt-8">
              <CardHeader>
                <CardTitle>Demo state allocation sample</CardTitle>
                <CardDescription>{result.data.scope_note}</CardDescription>
              </CardHeader>
              <CardContent className="overflow-x-auto">
                <table className="w-full min-w-3xl border-collapse text-left text-sm">
                  <thead>
                    <tr className="border-border border-b">
                      <th className="py-3 pr-5 font-medium">State</th>
                      <th className="py-3 pr-5 font-medium">Gross</th>
                      <th className="py-3 pr-5 font-medium">Deductions</th>
                      <th className="py-3 pr-5 font-medium">Net</th>
                      <th className="py-3 font-medium">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.data.allocations.map((allocation) => (
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
                        <td className="py-4 pr-5 font-mono font-semibold">
                          {formatNaira(allocation.net_allocation)}
                        </td>
                        <td className="py-4">
                          <StatusPill>
                            {humanize(allocation.verification_status)}
                          </StatusPill>
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
    </>
  )
}
