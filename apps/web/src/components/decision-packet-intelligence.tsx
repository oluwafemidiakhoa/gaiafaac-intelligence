import Link from 'next/link'

import { StatusPill } from '@/components/status-pill'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import type { DecisionPacket } from '@/lib/decision-packet-api'
import { formatDate, formatNaira } from '@/lib/format'

function asNumber(value: string | null) {
  if (value === null) return null
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : null
}

function percent(value: number | null) {
  return value === null ? 'Unavailable' : `${value.toFixed(2)}%`
}

function shortMoney(value: string | null) {
  const number = asNumber(value)
  if (number === null) return 'Unavailable'
  const billion = number / 1_000_000_000
  return `₦${billion.toLocaleString('en-NG', {
    maximumFractionDigits: 2,
  })}bn`
}

function monthLabel(value: string) {
  return new Intl.DateTimeFormat('en-NG', {
    month: 'short',
    timeZone: 'UTC',
  }).format(new Date(`${value}T00:00:00Z`))
}

function SignalCard({
  label,
  value,
  detail,
}: {
  label: string
  value: string
  detail: string
}) {
  return (
    <Card className="bg-background/80">
      <CardHeader className="pb-3">
        <CardDescription>{label}</CardDescription>
        <CardTitle className="text-2xl tracking-[-0.03em]">{value}</CardTitle>
      </CardHeader>
      <CardContent className="text-muted-foreground text-xs leading-5">
        {detail}
      </CardContent>
    </Card>
  )
}

function FlowChart({ packet }: { packet: DecisionPacket }) {
  const series = packet.months
    .map((month) => ({
      month,
      gross: asNumber(month.gross_total),
      net: asNumber(month.net_allocation),
    }))
    .filter((row) => row.gross !== null || row.net !== null)
  const max = Math.max(
    1,
    ...series.flatMap((row) => [row.gross ?? 0, row.net ?? 0]),
  )

  return (
    <Card>
      <CardHeader>
        <CardTitle>Monthly gross vs net allocation</CardTitle>
        <CardDescription>
          Published FAAC periods only. Select any month below to inspect the
          underlying Fiscal Proof.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid min-h-64 grid-cols-6 items-end gap-3 border-b border-l px-3 pt-5">
          {series.map(({ month, gross, net }) => {
            const grossHeight = Math.max(4, ((gross ?? 0) / max) * 190)
            const netHeight = Math.max(4, ((net ?? 0) / max) * 190)
            return (
              <Link
                key={month.proof_id}
                href={month.proof_path}
                className="group flex min-w-0 flex-col items-center gap-2"
                title={`${monthLabel(month.revenue_month)}: gross ${formatNaira(month.gross_total)}, net ${formatNaira(month.net_allocation)}`}
              >
                <div className="flex h-52 items-end gap-1">
                  <span
                    className="bg-amber-300/80 group-hover:bg-amber-300 block w-4 rounded-t-sm transition-colors"
                    style={{ height: `${grossHeight}px` }}
                    aria-label={`${monthLabel(month.revenue_month)} gross allocation ${formatNaira(month.gross_total)}`}
                  />
                  <span
                    className="bg-primary/85 group-hover:bg-primary block w-4 rounded-t-sm transition-colors"
                    style={{ height: `${netHeight}px` }}
                    aria-label={`${monthLabel(month.revenue_month)} net allocation ${formatNaira(month.net_allocation)}`}
                  />
                </div>
                <span className="text-muted-foreground group-hover:text-primary text-xs font-medium">
                  {monthLabel(month.revenue_month)}
                </span>
              </Link>
            )
          })}
        </div>
        <div className="mt-4 flex flex-wrap gap-4 text-xs">
          <span className="flex items-center gap-2">
            <span className="size-2.5 rounded-sm bg-amber-300" /> Gross
          </span>
          <span className="flex items-center gap-2">
            <span className="bg-primary size-2.5 rounded-sm" /> Net
          </span>
        </div>
      </CardContent>
    </Card>
  )
}

function DeductionChart({ packet }: { packet: DecisionPacket }) {
  const series = packet.months.map((month) => {
    const gross = asNumber(month.gross_total)
    const deductions = asNumber(month.total_deductions)
    const burden =
      gross !== null && gross !== 0 && deductions !== null
        ? (deductions / gross) * 100
        : null
    return { month, burden }
  })
  const max = Math.max(
    10,
    ...series.map((row) => row.burden ?? 0),
  )

  return (
    <Card>
      <CardHeader>
        <CardTitle>Deduction pressure</CardTitle>
        <CardDescription>
          Deductions as a share of published gross allocation by period.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {series.map(({ month, burden }) => (
            <Link
              href={month.proof_path}
              key={month.proof_id}
              className="group grid grid-cols-[4rem_1fr_4.5rem] items-center gap-3"
            >
              <span className="text-muted-foreground group-hover:text-primary text-xs font-medium">
                {monthLabel(month.revenue_month)}
              </span>
              <span className="bg-muted relative h-3 overflow-hidden rounded-full">
                <span
                  className="bg-primary absolute inset-y-0 left-0 rounded-full transition-opacity group-hover:opacity-80"
                  style={{
                    width: `${Math.min(100, ((burden ?? 0) / max) * 100)}%`,
                  }}
                />
              </span>
              <span className="text-right font-mono text-xs font-semibold">
                {burden === null ? 'N/A' : `${burden.toFixed(2)}%`}
              </span>
            </Link>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

export function DecisionPacketIntelligence({
  packet,
}: {
  packet: DecisionPacket
}) {
  const first = packet.months[0]
  const last = packet.months.at(-1)
  const firstNet = asNumber(first?.net_allocation ?? null)
  const lastNet = asNumber(last?.net_allocation ?? null)
  const firstToLast =
    firstNet !== null && firstNet !== 0 && lastNet !== null
      ? ((lastNet - firstNet) / Math.abs(firstNet)) * 100
      : null
  const verifiedMonths = packet.months.filter(
    (month) => month.human_verified,
  ).length
  const sourceCount = new Set(
    packet.months.map((month) => month.source_sha256).filter(Boolean),
  ).size

  return (
    <section className="mt-8 space-y-6" aria-labelledby="live-fiscal-intelligence">
      <div className="border-primary/20 bg-primary/[0.035] rounded-xl border p-5 sm:p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="max-w-3xl">
            <p className="text-primary font-mono text-xs font-semibold tracking-[0.16em] uppercase">
              Live Fiscal Intelligence
            </p>
            <h2
              id="live-fiscal-intelligence"
              className="mt-2 text-2xl font-semibold tracking-[-0.03em]"
            >
              What the governed evidence says now
            </h2>
            <p className="text-muted-foreground mt-2 text-sm leading-6">
              Deterministic analysis over published, governed evidence. Every
              plotted month remains clickable back to its Fiscal Proof and
              source fingerprint. No missing period is filled and no forecast is
              introduced.
            </p>
          </div>
          <div className="flex flex-wrap gap-2 print:hidden">
            <Button asChild variant="outline" size="sm">
              <Link href={`/watchlist?state=${packet.state_slug}`}>
                Monitor jurisdiction
              </Link>
            </Button>
            <Button asChild variant="outline" size="sm">
              <a
                href={`/api/customer-proxy/api/v1/published/samples/decision-pack/${packet.state_slug}.xlsx?year=${packet.year}`}
              >
                Sample Excel
              </a>
            </Button>
            <Button asChild variant="outline" size="sm">
              <a
                href={`/api/customer-proxy/api/v1/published/samples/decision-pack/${packet.state_slug}.pdf?year=${packet.year}`}
              >
                Sample PDF
              </a>
            </Button>
          </div>
        </div>

        <div className="mt-5 flex flex-wrap items-center gap-2">
          <StatusPill tone="success">{packet.evidence_status}</StatusPill>
          <StatusPill tone="neutral">
            {packet.months_published}/12 published periods
          </StatusPill>
          <StatusPill tone="neutral">
            {verifiedMonths}/{packet.months.length} human verified
          </StatusPill>
          <StatusPill tone="neutral">{sourceCount} source fingerprints</StatusPill>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <SignalCard
          label="Net allocation"
          value={shortMoney(packet.annual_net)}
          detail="Published-period net fiscal flow in the current evidence boundary."
        />
        <SignalCard
          label="Deduction burden"
          value={percent(packet.deduction_burden_pct)}
          detail="Recorded deductions as a share of governed gross allocation."
        />
        <SignalCard
          label="Flow momentum"
          value={`${packet.momentum}${packet.momentum_pct === null ? '' : ` · ${packet.momentum_pct.toFixed(2)}%`}`}
          detail="Observed direction across published periods; this is not a forecast."
        />
        <SignalCard
          label="First-to-latest net change"
          value={firstToLast === null ? 'Unavailable' : `${firstToLast >= 0 ? '+' : ''}${firstToLast.toFixed(2)}%`}
          detail="Direct comparison of the first and latest published net-allocation observations."
        />
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <FlowChart packet={packet} />
        <DeductionChart packet={packet} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Evidence drill-down</CardTitle>
          <CardDescription>
            The visual layer never replaces provenance. Open any row to verify
            the exact source-linked observation.
          </CardDescription>
        </CardHeader>
        <CardContent className="divide-border divide-y">
          {packet.months.map((month) => (
            <Link
              key={month.proof_id}
              href={month.proof_path}
              className="hover:bg-muted/40 grid gap-3 py-4 transition-colors md:grid-cols-[8rem_1fr_1fr_auto] md:items-center"
            >
              <div>
                <p className="font-medium">{formatDate(month.revenue_month)}</p>
                <p className="text-muted-foreground mt-1 text-xs">
                  {month.reconciliation_status}
                </p>
              </div>
              <div>
                <p className="text-muted-foreground text-xs">Net allocation</p>
                <p className="mt-1 font-mono text-sm font-semibold">
                  {formatNaira(month.net_allocation)}
                </p>
              </div>
              <div className="min-w-0">
                <p className="text-muted-foreground text-xs">
                  Source fingerprint
                </p>
                <p className="mt-1 truncate font-mono text-xs">
                  {month.source_sha256}
                </p>
              </div>
              <span className="text-primary text-sm font-medium">
                Verify proof →
              </span>
            </Link>
          ))}
        </CardContent>
      </Card>

      <p className="text-muted-foreground text-xs leading-5">
        Current published window: {first ? formatDate(first.revenue_month) : 'Unavailable'}
        {' → '}
        {last ? formatDate(last.revenue_month) : 'Unavailable'}. Peer ranking,
        debt conclusions and unpublished IGR estimates are intentionally outside
        this single-jurisdiction Decision Packet.
      </p>
    </section>
  )
}
