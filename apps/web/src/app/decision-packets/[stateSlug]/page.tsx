import type { Metadata } from 'next'
import Link from 'next/link'

import { DataUnavailable } from '@/components/data-unavailable'
import { PageHeader } from '@/components/page-header'
import { PrintButton } from '@/components/print-button'
import { StatusPill } from '@/components/status-pill'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { formatDate, formatNaira, humanize } from '@/lib/format'
import { getDecisionPacket } from '@/lib/decision-packet-api'

export const dynamic = 'force-dynamic'

interface DecisionPacketPageProps {
  params: Promise<{ stateSlug: string }>
  searchParams: Promise<{ year?: string }>
}

export async function generateMetadata({
  params,
  searchParams,
}: DecisionPacketPageProps): Promise<Metadata> {
  const { stateSlug } = await params
  const query = await searchParams
  const year = Number(query.year ?? new Date().getUTCFullYear())
  return { title: `${humanize(stateSlug)} ${year} Decision Packet` }
}

export default async function DecisionPacketPage({
  params,
  searchParams,
}: DecisionPacketPageProps) {
  const { stateSlug } = await params
  const query = await searchParams
  const currentYear = new Date().getUTCFullYear()
  const parsedYear = Number(query.year ?? currentYear)
  const year = Number.isInteger(parsedYear) ? parsedYear : currentYear
  const result = await getDecisionPacket(stateSlug, year)
  const data = result.data

  if (!data) {
    return (
      <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
        <PageHeader
          eyebrow="Decision Packet"
          title={`${humanize(stateSlug)} · ${year}`}
          description="Evidence-backed state fiscal brief over published GaiaFAAC records."
        />
        <div className="mt-8">
          <DataUnavailable message={result.error ?? 'Decision Packet is unavailable.'} />
        </div>
      </div>
    )
  }

  return (
    <article className="mx-auto max-w-5xl px-5 py-12 print:max-w-none print:px-0 print:py-0 lg:px-8 lg:py-16">
      <div className="flex flex-wrap items-start justify-between gap-4 print:block">
        <PageHeader
          eyebrow={`GaiaFAAC Decision Packet · v${data.packet_version}`}
          title={`${data.state_name} · ${data.year}`}
          description={data.coverage_label}
        />
        <PrintButton />
      </div>

      <div className="mt-6 flex flex-wrap gap-3">
        <StatusPill tone="success">{data.evidence_status}</StatusPill>
        <span className="text-muted-foreground text-sm">
          {data.state_code} · {data.geopolitical_zone} · {data.months_published} published months
        </span>
      </div>

      <section className="mt-8 grid gap-4 md:grid-cols-3 print:grid-cols-3">
        <Card>
          <CardHeader>
            <CardDescription>Published-period net</CardDescription>
            <CardTitle>{formatNaira(data.annual_net)}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader>
            <CardDescription>Deduction burden</CardDescription>
            <CardTitle>
              {data.deduction_burden_pct === null
                ? 'Unavailable'
                : `${data.deduction_burden_pct.toFixed(2)}%`}
            </CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader>
            <CardDescription>Allocation volatility</CardDescription>
            <CardTitle>{data.volatility}</CardTitle>
          </CardHeader>
          <CardContent className="text-muted-foreground text-sm">
            {data.volatility_cv_pct === null
              ? 'Coefficient unavailable'
              : `CV ${data.volatility_cv_pct.toFixed(2)}%`}
          </CardContent>
        </Card>
      </section>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Fiscal signal summary</CardTitle>
          <CardDescription>
            Deterministic Fiscal Pulse measures over the published period.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 text-sm md:grid-cols-2">
          <div>
            <p className="text-muted-foreground">Gross allocation</p>
            <p className="mt-1 font-medium">{formatNaira(data.annual_gross)}</p>
          </div>
          <div>
            <p className="text-muted-foreground">Deductions</p>
            <p className="mt-1 font-medium">{formatNaira(data.annual_deductions)}</p>
          </div>
          <div>
            <p className="text-muted-foreground">Net retention</p>
            <p className="mt-1 font-medium">
              {data.net_retention_pct === null
                ? 'Unavailable'
                : `${data.net_retention_pct.toFixed(2)}%`}
            </p>
          </div>
          <div>
            <p className="text-muted-foreground">Momentum</p>
            <p className="mt-1 font-medium">
              {data.momentum}
              {data.momentum_pct === null ? '' : ` · ${data.momentum_pct.toFixed(2)}%`}
            </p>
          </div>
        </CardContent>
      </Card>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Current watch events</CardTitle>
          <CardDescription>
            Latest threshold events for this jurisdiction. No cause is inferred.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {data.watch_events.length === 0 ? (
            <p className="text-muted-foreground text-sm">
              No Fiscal Watch threshold is currently triggered for this state.
            </p>
          ) : (
            <div className="space-y-3">
              {data.watch_events.map((event) => (
                <div key={`${event.kind}-${event.proof_path}`} className="border-border rounded-lg border p-4">
                  <p className="font-medium">{event.headline}</p>
                  <p className="text-muted-foreground mt-1 text-sm">{event.detail}</p>
                  <Link
                    href={event.proof_path}
                    className="text-primary mt-2 inline-block text-sm font-medium hover:underline print:hidden"
                  >
                    Verify with Fiscal Proof →
                  </Link>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Monthly evidence chain</CardTitle>
          <CardDescription>
            Every available month is tied to a deterministic Fiscal Proof and source hash.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {data.months.map((month) => (
            <div
              key={month.proof_id}
              className="border-border grid gap-3 rounded-lg border p-4 md:grid-cols-[10rem_1fr_auto] print:grid-cols-[8rem_1fr]"
            >
              <div>
                <p className="font-medium">{formatDate(month.revenue_month)}</p>
                <p className="text-muted-foreground mt-1 font-mono text-xs">{month.proof_id}</p>
              </div>
              <div className="text-sm">
                <p>Net: {formatNaira(month.net_allocation)}</p>
                <p className="text-muted-foreground mt-1">
                  {month.source_organization} · {month.reconciliation_status} ·{' '}
                  {month.human_verified ? 'human verified' : 'verification incomplete'}
                </p>
                <p className="text-muted-foreground mt-1 break-all font-mono text-xs">
                  SHA-256 {month.source_sha256}
                </p>
              </div>
              <Link
                href={month.proof_path}
                className="text-primary self-start text-sm font-medium hover:underline print:hidden"
              >
                Open proof →
              </Link>
            </div>
          ))}
        </CardContent>
      </Card>

      <p className="text-muted-foreground mt-8 text-xs leading-5">{data.disclaimer}</p>
    </article>
  )
}
