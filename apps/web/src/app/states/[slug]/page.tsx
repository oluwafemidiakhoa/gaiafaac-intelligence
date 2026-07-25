import type { Metadata } from 'next'
import Link from 'next/link'
import { notFound } from 'next/navigation'

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
import { getDemoState } from '@/lib/demo-api'
import { formatDate, formatNaira, humanize } from '@/lib/format'

export const dynamic = 'force-dynamic'

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>
}): Promise<Metadata> {
  const { slug } = await params
  return { title: `${humanize(slug)} state` }
}

export default async function StatePage({
  params,
}: {
  params: Promise<{ slug: string }>
}) {
  const { slug } = await params
  const result = await getDemoState(slug)
  if (result.data === null && result.error?.includes('does not exist')) notFound()

  return (
    <>
      <DemoBanner />
      <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
        {result.data === null ? (
          <>
            <PageHeader
              eyebrow="State detail"
              title={humanize(slug)}
              description="The state page could not retrieve the labelled demo dataset."
            />
            <div className="mt-10">
              <DataUnavailable
                message={result.error ?? 'The state detail is unavailable.'}
              />
            </div>
          </>
        ) : (
          <>
            <PageHeader
              eyebrow={`${result.data.state.code} · ${result.data.state.geopolitical_zone}`}
              title={result.data.state.name}
              description={`Capital: ${result.data.state.capital}. Reporting period: ${result.data.period.reporting_label}.`}
            />
            <div className="mt-8 flex flex-wrap gap-3">
              <StatusPill tone="demo">Demo data</StatusPill>
              <StatusPill>
                {result.data.allocation
                  ? humanize(result.data.allocation.verification_status)
                  : 'unavailable'}
              </StatusPill>
              <span className="text-muted-foreground text-sm">
                Revenue month {formatDate(result.data.period.revenue_month)}
              </span>
            </div>

            {result.data.allocation === null ? (
              <div className="mt-10">
                <DataUnavailable
                  message={
                    result.data.unavailable_note ??
                    'No labelled demo allocation is available.'
                  }
                />
              </div>
            ) : (
              <>
                <div className="mt-8 grid gap-4 md:grid-cols-3">
                  <MetricCard
                    label="Demo net allocation"
                    value={formatNaira(result.data.allocation.net_allocation)}
                    detail="Synthetic and unpublished."
                  />
                  <MetricCard
                    label="Demo gross total"
                    value={formatNaira(result.data.allocation.gross_total)}
                    detail="Original gross, before synthetic deductions."
                  />
                  <MetricCard
                    label="Demo deductions"
                    value={formatNaira(
                      result.data.allocation.total_deductions,
                    )}
                    detail="Synthetic deduction value."
                  />
                </div>

                <Card className="mt-8">
                  <CardHeader>
                    <CardTitle>Allocation components</CardTitle>
                    <CardDescription>
                      Flexible components retained from the labelled demo source.
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {result.data.components.map((component) => (
                      <div
                        key={`${component.component_type}-${component.component_name}`}
                        className="border-border grid gap-3 rounded-lg border p-4 sm:grid-cols-[1fr_auto]"
                      >
                        <div>
                          <p className="font-medium">
                            {component.component_name}
                          </p>
                          <p className="text-muted-foreground mt-1 text-xs">
                            {humanize(component.component_type)}
                          </p>
                        </div>
                        <div className="text-left sm:text-right">
                          <p className="font-mono font-semibold">
                            {formatNaira(component.net_amount)}
                          </p>
                          <p className="text-muted-foreground mt-1 text-xs">
                            Net component
                          </p>
                        </div>
                      </div>
                    ))}
                  </CardContent>
                </Card>
                <p className="text-muted-foreground mt-5 text-xs">
                  Source document{' '}
                  <Link
                    href="/sources"
                    className="text-foreground font-mono hover:underline"
                  >
                    {result.data.allocation.source_document_id}
                  </Link>
                </p>
              </>
            )}

            <Link
              href="/states"
              className="text-primary mt-8 inline-block text-sm font-medium hover:underline"
            >
              ← Back to all states
            </Link>
          </>
        )}
      </div>
    </>
  )
}
