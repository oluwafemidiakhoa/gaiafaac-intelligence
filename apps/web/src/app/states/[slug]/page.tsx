import type { Metadata } from 'next'
import Link from 'next/link'

import { DataUnavailable } from '@/components/data-unavailable'
import { MetricCard } from '@/components/metric-card'
import { PageHeader } from '@/components/page-header'
import { StatusPill } from '@/components/status-pill'
import { Button } from '@/components/ui/button'
import { formatDate, formatNaira, humanize } from '@/lib/format'
import {
  getLatestPublishedIgr,
  getPublishedOverview,
} from '@/lib/published-api'

export const dynamic = 'force-dynamic'

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>
}): Promise<Metadata> {
  const { slug } = await params
  return { title: `${humanize(slug)} — verified state fiscal evidence` }
}

export default async function StatePage({
  params,
}: {
  params: Promise<{ slug: string }>
}) {
  const { slug } = await params
  const [overviewResult, igrResult] = await Promise.all([
    getPublishedOverview(),
    getLatestPublishedIgr(slug),
  ])
  const data = overviewResult.data
  const igr = igrResult.data
  const allocation =
    data?.allocations.find((a) => a.state_slug === slug) ?? null

  return (
    <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
      {data === null || allocation === null ? (
        <>
          <PageHeader
            eyebrow="State detail"
            title={humanize(slug)}
            description="Verified state fiscal evidence from published source records."
          />
          <div className="mt-10">
            <DataUnavailable
              message={
                data === null
                  ? (overviewResult.error ?? 'No verified FAAC month is published yet.')
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
            description={`Latest FAAC reporting period: ${data.period.reporting_label}.`}
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
              detail="Latest published FAAC received after deductions."
            />
            <MetricCard
              label="Gross total"
              value={formatNaira(allocation.gross_total)}
              detail="Latest published FAAC before deductions."
            />
            <MetricCard
              label="Deductions"
              value={formatNaira(allocation.total_deductions)}
              detail="Latest published FAAC deductions applied at source."
            />
          </div>

          <div className="border-border mt-8 rounded-lg border p-5">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="font-semibold">Internally Generated Revenue</p>
                <p className="text-muted-foreground mt-1 max-w-2xl text-sm leading-6">
                  Latest separately published IGR evidence. It is not combined with
                  FAAC and missing fiscal periods are not inferred.
                </p>
              </div>
              {igr ? <StatusPill tone="success">Human verified</StatusPill> : null}
            </div>
            {igr ? (
              <div className="mt-5 grid gap-4 md:grid-cols-3">
                <div>
                  <p className="text-muted-foreground text-sm">IGR amount</p>
                  <p className="mt-1 text-xl font-semibold">
                    {formatNaira(igr.igr_amount)}
                  </p>
                </div>
                <div>
                  <p className="text-muted-foreground text-sm">Fiscal period</p>
                  <p className="mt-1 font-medium">
                    {igr.fiscal_year} · {humanize(igr.period_type)}
                    {igr.quarter === null ? '' : ` · Q${igr.quarter}`}
                  </p>
                </div>
                <div>
                  <p className="text-muted-foreground text-sm">Evidence source</p>
                  <p className="mt-1 font-medium">{igr.source.organization}</p>
                  <p className="text-muted-foreground mt-1 font-mono text-xs break-all">
                    SHA-256 {igr.source.sha256}
                  </p>
                </div>
              </div>
            ) : (
              <p className="text-muted-foreground mt-4 text-sm">
                {igrResult.error ??
                  'No published IGR evidence is available for this state yet.'}
              </p>
            )}
          </div>

          <div className="border-border mt-8 rounded-lg border p-5">
            <p className="font-semibold">Evidence tools</p>
            <p className="text-muted-foreground mt-2 max-w-2xl text-sm leading-6">
              Verify this FAAC month with Fiscal Proof, or open the state Decision
              Packet for a print-ready evidence dossier across the selected year.
            </p>
            <div className="mt-4 flex flex-wrap gap-3">
              <Button asChild variant="outline">
                <Link
                  href={`/fiscal-proof/${allocation.state_slug}/${data.period.revenue_month}`}
                >
                  Verify this allocation
                </Link>
              </Button>
              <Button asChild variant="outline">
                <Link
                  href={`/decision-packets/${allocation.state_slug}?year=${data.period.revenue_month.slice(0, 4)}`}
                >
                  Open Decision Packet
                </Link>
              </Button>
            </div>
          </div>

          <p className="text-muted-foreground mt-6 text-sm">
            Latest FAAC traceable to {data.source.source_organization} ·{' '}
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
