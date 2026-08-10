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
import { getFiscalWatch } from '@/lib/fiscal-watch-api'
import { formatNaira } from '@/lib/format'

export const metadata: Metadata = { title: 'Fiscal Watch' }
export const dynamic = 'force-dynamic'

function eventTone(severity: string): 'demo' | 'neutral' {
  return severity === 'elevated' ? 'demo' : 'neutral'
}

export default async function FiscalWatchPage() {
  const year = new Date().getUTCFullYear()
  const result = await getFiscalWatch(year)
  const data = result.data

  if (!data) {
    return (
      <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
        <PageHeader
          eyebrow="Fiscal Watch"
          title="Evidence-linked monitoring for Nigerian state allocations"
          description="Deterministic alerts over published, human-approved GaiaFAAC records."
        />
        <div className="mt-10">
          <DataUnavailable
            message={result.error ?? 'Fiscal Watch is unavailable.'}
          />
        </div>
      </div>
    )
  }

  const elevated = data.events.filter(
    (event) => event.severity === 'elevated',
  ).length
  const monthlyMoves = data.events.filter(
    (event) => event.kind === 'large_monthly_move',
  ).length
  const deductionEvents = data.events.filter(
    (event) => event.kind === 'high_deduction_burden',
  ).length

  return (
    <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
      <PageHeader
        eyebrow={`GaiaFAAC Fiscal Watch · ${data.year}`}
        title="What changed in the latest published FAAC data?"
        description="Fiscal Watch turns verified monthly allocations into evidence-linked monitoring signals. Every event points back to a Fiscal Proof."
      />

      <div className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="Watch events"
          value={String(data.event_count)}
          detail={
            data.latest_revenue_month
              ? `Latest published month: ${data.latest_revenue_month}`
              : 'No published month available'
          }
        />
        <MetricCard
          label="Elevated events"
          value={String(elevated)}
          detail="Currently reserved for source-reported negative net allocations."
        />
        <MetricCard
          label="Large monthly moves"
          value={String(monthlyMoves)}
          detail="Absolute month-over-month net allocation change of at least 25%."
        />
        <MetricCard
          label="High deduction burden"
          value={String(deductionEvents)}
          detail="Deductions at or above 50% of gross allocation in the latest month."
        />
      </div>

      <Card className="mt-8">
        <CardHeader>
          <CardTitle>Latest evidence-linked events</CardTitle>
          <CardDescription>
            Signals are deterministic and derived only from published, non-demo
            records. They do not infer cause or fiscal health.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {data.events.length === 0 ? (
            <p className="text-muted-foreground text-sm leading-6">
              No Fiscal Watch thresholds were triggered in the latest published
              month.
            </p>
          ) : (
            <div className="space-y-4">
              {data.events.map((event, index) => (
                <div
                  key={`${event.state_code}-${event.kind}-${index}`}
                  className="border-border rounded-lg border p-5"
                >
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <Link
                          href={`/states/${event.state_slug}`}
                          className="font-semibold hover:underline"
                        >
                          {event.state_name}
                        </Link>
                        <StatusPill tone={eventTone(event.severity)}>
                          {event.severity === 'elevated' ? 'Elevated' : 'Watch'}
                        </StatusPill>
                      </div>
                      <p className="mt-2 font-medium">{event.headline}</p>
                      <p className="text-muted-foreground mt-1 max-w-3xl text-sm leading-6">
                        {event.detail}
                      </p>
                    </div>
                    <span className="text-muted-foreground font-mono text-xs">
                      {event.revenue_month}
                    </span>
                  </div>

                  <div className="mt-4 flex flex-wrap gap-x-6 gap-y-2 text-sm">
                    {event.current_net !== null ? (
                      <span>
                        Current net:{' '}
                        <strong className="font-mono">
                          {formatNaira(event.current_net)}
                        </strong>
                      </span>
                    ) : null}
                    {event.change_pct !== null ? (
                      <span>
                        Monthly change:{' '}
                        <strong>{event.change_pct.toFixed(2)}%</strong>
                      </span>
                    ) : null}
                    {event.deduction_burden_pct !== null ? (
                      <span>
                        Deduction burden:{' '}
                        <strong>
                          {event.deduction_burden_pct.toFixed(2)}%
                        </strong>
                      </span>
                    ) : null}
                  </div>

                  <Link
                    href={event.proof_path}
                    className="text-primary mt-4 inline-block text-sm font-medium hover:underline"
                  >
                    Verify with Fiscal Proof →
                  </Link>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <p className="text-muted-foreground mt-8 text-xs leading-5">
        {data.note}
      </p>
    </div>
  )
}
