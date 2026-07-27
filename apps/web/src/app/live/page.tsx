import type { Metadata } from 'next'

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

export const metadata: Metadata = { title: 'Live FAAC data' }
export const dynamic = 'force-dynamic'

export default async function LivePage() {
  const result = await getPublishedOverview()

  return (
    <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
      <PageHeader
        eyebrow="Live · source-verified"
        title="Real Federation Account allocations"
        description="Official FAAC figures, extracted from source documents, reconciled, and human-approved before publication. Every figure traces back to its report."
      />

      {result.data === null ? (
        <div className="mt-10 space-y-4">
          <DataUnavailable
            message={result.error ?? 'No published FAAC data is available yet.'}
          />
          <p className="text-muted-foreground max-w-2xl text-sm leading-6">
            Real reports are ingested, validated, and explicitly approved by a
            reviewer before appearing here. Nothing is published automatically,
            and no figure is ever inferred.
          </p>
        </div>
      ) : (
        <>
          <div className="mt-8 flex flex-wrap items-center gap-3">
            <StatusPill tone="success">Verified · published</StatusPill>
            <span className="text-muted-foreground text-sm">
              Revenue month {formatDate(result.data.period.revenue_month)}
            </span>
            {result.data.period.published_at ? (
              <span className="text-muted-foreground text-sm">
                Published{' '}
                {formatDate(result.data.period.published_at.slice(0, 10))}
              </span>
            ) : null}
          </div>

          <div className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <MetricCard
              label="Total net allocation"
              value={formatNaira(result.data.total_net)}
              detail={result.data.period.reporting_label}
            />
            <MetricCard
              label="Total gross"
              value={formatNaira(result.data.total_gross)}
              detail="Before deductions."
            />
            <MetricCard
              label="Total deductions"
              value={formatNaira(result.data.total_deductions)}
              detail="Applied at source."
            />
            <MetricCard
              label="Coverage"
              value={`${result.data.covered_states} / ${result.data.expected_states}`}
              detail="Jurisdictions published."
            />
          </div>

          <Card className="mt-8">
            <CardHeader>
              <CardTitle>Source</CardTitle>
              <CardDescription>
                Every published figure traces to this document.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <dl className="grid gap-5 text-sm sm:grid-cols-2 lg:grid-cols-3">
                <div>
                  <dt className="text-muted-foreground">Organization</dt>
                  <dd className="mt-1 font-medium">
                    {result.data.source.source_organization}
                  </dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Document</dt>
                  <dd className="mt-1 font-mono text-xs break-all">
                    {result.data.source.original_filename}
                  </dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Report published</dt>
                  <dd className="mt-1 font-medium">
                    {formatDate(result.data.source.publication_date)}
                  </dd>
                </div>
                <div className="sm:col-span-2 lg:col-span-3">
                  <dt className="text-muted-foreground">SHA-256</dt>
                  <dd className="mt-1 font-mono text-xs break-all">
                    {result.data.source.sha256}
                  </dd>
                </div>
              </dl>
              {result.data.source.source_url ? (
                <a
                  href={result.data.source.source_url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-primary mt-5 inline-block text-sm font-medium hover:underline"
                >
                  View the original source →
                </a>
              ) : null}
            </CardContent>
          </Card>

          <Card className="mt-8">
            <CardHeader>
              <CardTitle>State allocations</CardTitle>
              <CardDescription>
                {result.data.period.reporting_label}
              </CardDescription>
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
                  {result.data.allocations.map((allocation) => (
                    <tr
                      key={allocation.state_code}
                      className="border-border border-b last:border-0"
                    >
                      <td className="py-4 pr-5">
                        <p className="font-medium">{allocation.state_name}</p>
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
        </>
      )}
    </div>
  )
}
