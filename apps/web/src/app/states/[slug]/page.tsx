import type { Metadata } from 'next'
import Link from 'next/link'

import { DataUnavailable } from '@/components/data-unavailable'
import { MetricCard } from '@/components/metric-card'
import { PageHeader } from '@/components/page-header'
import { StatusPill } from '@/components/status-pill'
import { Button } from '@/components/ui/button'
import { formatDate, formatNaira, humanize } from '@/lib/format'
import { getPublishedOverview } from '@/lib/published-api'

export const dynamic = 'force-dynamic'

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>
}): Promise<Metadata> {
  const { slug } = await params
  return { title: `${humanize(slug)} — verified FAAC allocation` }
}

export default async function StatePage({
  params,
}: {
  params: Promise<{ slug: string }>
}) {
  const { slug } = await params
  const result = await getPublishedOverview()
  const data = result.data
  const allocation = data?.allocations.find((a) => a.state_slug === slug) ?? null

  return (
    <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
      {data === null || allocation === null ? (
        <>
          <PageHeader
            eyebrow="State detail"
            title={humanize(slug)}
            description="Verified FAAC allocation for the latest published month."
          />
          <div className="mt-10">
            <DataUnavailable
              message={
                data === null
                  ? (result.error ?? 'No verified month is published yet.')
                  : 'This jurisdiction has no verified allocation in the latest published month.'
              }
            />
          </div>
          <Link
            href="/states"
            className="text-primary mt-8 inline-block text-sm font-medium hover:underline"
          >
            ← Back to all states
          </Link>
        </>
      ) : (
        <>
          <PageHeader
            eyebrow={`${allocation.state_code} · ${allocation.geopolitical_zone}`}
            title={allocation.state_name}
            description={`Reporting period: ${data.period.reporting_label}.`}
          />
          <div className="mt-8 flex flex-wrap gap-3">
            <StatusPill tone="success">Verified · published</StatusPill>
            <span className="text-muted-foreground text-sm">
              Revenue month {formatDate(data.period.revenue_month)}
            </span>
          </div>

          <div className="mt-8 grid gap-4 md:grid-cols-3">
            <MetricCard
              label="Net allocation"
              value={formatNaira(allocation.net_allocation)}
              detail="Total received after deductions."
            />
            <MetricCard
              label="Gross total"
              value={formatNaira(allocation.gross_total)}
              detail="Before deductions."
            />
            <MetricCard
              label="Deductions"
              value={formatNaira(allocation.total_deductions)}
              detail="Applied at source."
            />
          </div>

          <div className="border-border mt-8 rounded-lg border p-5">
            <p className="font-semibold">Fiscal Proof</p>
            <p className="text-muted-foreground mt-2 max-w-2xl text-sm leading-6">
              Open the deterministic evidence record for this published allocation, including source-document SHA-256, reconciliation status, verification chain and reproducible proof digest.
            </p>
            <Button asChild className="mt-4" variant="outline">
              <Link href={`/fiscal-proof/${allocation.state_slug}/${data.period.revenue_month}`}>
                Verify this allocation
              </Link>
            </Button>
          </div>

          <p className="text-muted-foreground mt-6 text-sm">
            Traceable to {data.source.source_organization} ·{' '}
            <Link href="/live" className="text-foreground hover:underline">
              view the full month and source document
            </Link>
            .
          </p>

          <Link
            href="/states"
            className="text-primary mt-8 inline-block text-sm font-medium hover:underline"
          >
            ← Back to all states
          </Link>
        </>
      )}
    </div>
  )
}
