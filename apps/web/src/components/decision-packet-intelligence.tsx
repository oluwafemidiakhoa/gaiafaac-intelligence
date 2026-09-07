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
import {
  analyzeFiscalEvidence,
  fromKobo,
  monthName,
  proofHref,
  toKobo,
  type FiscalAnalysis,
  type FiscalRow,
} from '@/lib/decision-packet-analysis'
import type { DecisionPacket } from '@/lib/decision-packet-api'
import { formatNaira } from '@/lib/format'

function percent(value: number | null, signed = false) {
  if (value === null || !Number.isFinite(value)) return 'Unavailable'
  return `${signed && value > 0 ? '+' : ''}${value.toFixed(2)}%`
}

function money(value: bigint | null) {
  return value === null ? 'Unavailable' : formatNaira(fromKobo(value))
}

function spanLabel(rows: FiscalRow[]) {
  return rows.map((row) => monthName(row.month.revenue_month)).join(', ')
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
    <Card>
      <CardHeader>
        <CardDescription>{label}</CardDescription>
        <CardTitle className="text-xl">{value}</CardTitle>
      </CardHeader>
      <CardContent className="text-muted-foreground text-xs leading-5">
        {detail}
      </CardContent>
    </Card>
  )
}

/** Floating point is used only for pixel placement, never for money arithmetic. */
function Bar({
  value,
  max,
  label,
}: {
  value: bigint | null
  max: bigint
  label: string
}) {
  if (value === null) {
    return (
      <span
        className="text-muted-foreground text-xs"
        aria-label={`${label}: not reported`}
      >
        N/A
      </span>
    )
  }
  if (value < BigInt(0)) {
    return (
      <span
        className="text-xs"
        aria-label={`${label}: signed adjustment ${money(value)}`}
      >
        Adjustment
      </span>
    )
  }
  const height =
    max > BigInt(0) ? Number((value * BigInt(18000)) / max) / 100 : 0
  return (
    <span
      className="flex h-48 w-5 items-end"
      aria-label={`${label}: ${money(value)}`}
    >
      <span
        className="block w-full rounded-t-sm bg-current"
        data-testid="fiscal-bar"
        style={{ height: `${height}px` }}
      />
    </span>
  )
}

function FlowChart({ analysis }: { analysis: FiscalAnalysis }) {
  const max = analysis.rows.reduce<bigint>(
    (largest, row) =>
      [row.gross, row.net].reduce<bigint>(
        (n, amount) => (amount !== null && amount > n ? amount : n),
        largest,
      ),
    BigInt(0),
  )
  // Keep calendar gaps visible between the first and last published observations.
  const firstPeriod = analysis.rows[0]?.month.revenue_month
  const lastPeriod = analysis.rows.at(-1)?.month.revenue_month
  const slots = analysis.slots.filter(
    (slot) =>
      firstPeriod &&
      lastPeriod &&
      slot.period >= firstPeriod &&
      slot.period <= lastPeriod,
  )
  return (
    <Card className="min-w-0">
      <CardHeader>
        <CardTitle>Monthly gross vs net allocation</CardTitle>
        <CardDescription>
          Common zero baseline. Exact amounts are available on each proof. N/A
          is not zero.
        </CardDescription>
      </CardHeader>
      <CardContent>
        {!slots.length ? (
          <p>No published FAAC observations to plot.</p>
        ) : (
          <>
            <p className="text-muted-foreground mb-3 text-xs">
              Scale: 0 to {money(max)}
            </p>
            <div className="overflow-x-auto">
              <div
                className="flex items-end gap-4 border-b pb-3"
                data-testid="fiscal-flow-chart"
              >
                {slots.map(({ period, row, conflict }) => {
                  const href = row ? proofHref(row.month) : null
                  const content = (
                    <>
                      <div className="flex h-52 items-end justify-center gap-2">
                        {!row || conflict ? (
                          <span className="text-xs">
                            {conflict ? 'Conflict' : 'No record'}
                          </span>
                        ) : (
                          <>
                            <span className="text-amber-500">
                              <Bar
                                value={row.gross}
                                max={max}
                                label={`${monthName(period)} gross`}
                              />
                            </span>
                            <span className="text-primary">
                              <Bar
                                value={row.net}
                                max={max}
                                label={`${monthName(period)} net`}
                              />
                            </span>
                          </>
                        )}
                      </div>
                      <span className="text-xs">{monthName(period)}</span>
                    </>
                  )
                  return href ? (
                    <Link
                      className="min-w-20 text-center"
                      key={period}
                      href={href}
                      aria-label={`${monthName(period)} fiscal proof`}
                    >
                      {content}
                    </Link>
                  ) : (
                    <div className="min-w-20 text-center" key={period}>
                      {content}
                    </div>
                  )
                })}
              </div>
            </div>
            <p className="mt-3 text-xs">
              <span className="text-amber-500">Gross</span> /{' '}
              <span className="text-primary">Net</span>. Negative adjustments
              are labelled, not drawn as positive bars.
            </p>
          </>
        )}
      </CardContent>
    </Card>
  )
}

function DeductionChart({ analysis }: { analysis: FiscalAnalysis }) {
  // A labelled 0-100% reference avoids making 20% look like 100% of gross.
  return (
    <Card>
      <CardHeader>
        <CardTitle>Deduction pressure</CardTitle>
        <CardDescription>
          Deductions / gross allocation. Scale: 0-100%.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {!analysis.rows.length ? (
          <p>No published observations to analyze.</p>
        ) : null}
        {analysis.rows.map(({ month, burden }) => (
          <div
            key={month.revenue_month}
            className="grid grid-cols-[6rem_1fr_5rem] items-center gap-3"
          >
            <span className="text-xs">{monthName(month.revenue_month)}</span>
            <span className="bg-muted relative h-3 rounded-full">
              {burden !== null && burden >= 0 && burden <= 100 ? (
                <span
                  className="bg-primary absolute inset-y-0 left-0 rounded-full"
                  style={{ width: `${burden}%` }}
                />
              ) : null}
            </span>
            <span className="text-right font-mono text-xs">
              {percent(burden)}
            </span>
            {burden !== null && (burden < 0 || burden > 100) ? (
              <span className="col-span-3 text-xs">
                Outside chart scale; inspect the reported adjustment.
              </span>
            ) : null}
          </div>
        ))}
      </CardContent>
    </Card>
  )
}

export function DecisionPacketIntelligence({
  packet,
}: {
  packet: DecisionPacket
}) {
  const analysis = analyzeFiscalEvidence(packet.months, packet.year)
  const totals = [
    ['Gross', analysis.totals.gross, packet.annual_gross],
    ['Deductions', analysis.totals.deductions, packet.annual_deductions],
    ['Net', analysis.totals.net, packet.annual_net],
  ] as const
  const mismatchedTotals = totals.filter(
    ([, reconstructed, published]) =>
      reconstructed !== null &&
      toKobo(published) !== null &&
      reconstructed !== toKobo(published),
  )
  const momentumMismatch =
    analysis.momentum !== null &&
    packet.momentum_pct !== null &&
    Math.abs(analysis.momentum - packet.momentum_pct) > 0.011
  const needsReview =
    !analysis.structurallyValid ||
    analysis.invalidMoney ||
    analysis.residuals.length > 0 ||
    mismatchedTotals.length > 0 ||
    momentumMismatch
  const first = analysis.first?.month.revenue_month
  const latest = analysis.latest?.month.revenue_month

  return (
    <section
      className="mt-8 space-y-6"
      aria-labelledby="live-fiscal-intelligence"
    >
      <div className="border-primary/20 bg-primary/[0.035] rounded-xl border p-5 sm:p-6">
        <div className="flex flex-wrap justify-between gap-4">
          <div>
            <p className="text-primary text-xs font-semibold uppercase">
              Published fiscal intelligence
            </p>
            <h2
              id="live-fiscal-intelligence"
              className="mt-2 text-2xl font-semibold"
            >
              What the governed evidence says now
            </h2>
            <p className="text-muted-foreground mt-2 max-w-3xl text-sm leading-6">
              Read the result, inspect the calculation, then open its proof.
              This is the selected published evidence window, not a real-time
              feed or a forecast.
            </p>
          </div>
          <div className="flex flex-wrap gap-2 print:hidden">
            <Button asChild size="sm" variant="outline">
              <Link href="/watchlist">Monitor jurisdiction</Link>
            </Button>
            <Button asChild size="sm" variant="outline">
              <Link href="/projects">Get governed intelligence package</Link>
            </Button>
          </div>
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          <StatusPill tone="neutral">
            Gaia evidence status: {packet.evidence_status}
          </StatusPill>
          <StatusPill tone="neutral">
            {analysis.rows.length}/12 unique periods
          </StatusPill>
          <StatusPill tone="neutral">
            {analysis.verifiedCount}/{analysis.rows.length} human verified
          </StatusPill>
          <StatusPill tone="neutral">
            {analysis.sourceCount} valid source fingerprints
          </StatusPill>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <SignalCard
          label="Net allocation"
          value={formatNaira(packet.annual_net)}
          detail="Published-window total, not an estimate of the full year."
        />
        <SignalCard
          label="Deduction burden"
          value={percent(packet.deduction_burden_pct)}
          detail="Published deductions divided by published gross allocation."
        />
        <SignalCard
          label="Flow momentum"
          value={`${packet.momentum} / ${percent(packet.momentum_pct)}`}
          detail="Latest three available net observations versus the preceding three."
        />
        <SignalCard
          label="First-to-latest net change"
          value={percent(analysis.firstToLatest, true)}
          detail={
            first && latest
              ? `${monthName(first)} compared with ${monthName(latest)}; a different comparison from momentum.`
              : 'At least two usable published net observations are required.'
          }
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Two comparisons, not two contradictory answers</CardTitle>
          <CardDescription>
            Different time windows can legitimately point in different
            directions.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <p>
            First-to-latest change compares two observations: (latest net -
            first net) / absolute first net.
          </p>
          {analysis.prior.length ? (
            <>
              <p>
                <strong>Momentum baseline:</strong> {spanLabel(analysis.prior)}.
              </p>
              <p>
                <strong>Momentum recent window:</strong>{' '}
                {spanLabel(analysis.recent)}.
              </p>
              <p>
                Momentum compares the mean of these two three-observation
                windows. Reconstructed change:{' '}
                <strong>{percent(analysis.momentum)}</strong>. These are
                published observations, not necessarily consecutive calendar
                quarters.
              </p>
            </>
          ) : (
            <p>
              There are not six usable net observations here to independently
              reconstruct momentum.
            </p>
          )}
          {momentumMismatch ? (
            <p role="alert">
              Reported and reconstructed momentum differ. Review the evidence
              boundary; neither result has been silently replaced.
            </p>
          ) : null}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>
            {needsReview
              ? 'Evidence checks need review'
              : 'Arithmetic and coverage checks'}
          </CardTitle>
          <CardDescription>
            These are consistency checks, not independent certification of an
            official source.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <p>
            {analysis.checkedCount - analysis.residuals.length}/
            {analysis.checkedCount} checkable periods satisfy gross - deductions
            = net exactly to the kobo.{' '}
            {analysis.rows.length - analysis.checkedCount} periods lack a
            complete numeric triple.
          </p>
          {analysis.residuals.map((row) => (
            <p role="alert" key={row.month.revenue_month}>
              {monthName(row.month.revenue_month)} arithmetic residual:{' '}
              {money(row.residual)}. Inspect the proof; values are unchanged.
            </p>
          ))}
          {mismatchedTotals.map(([label]) => (
            <p role="alert" key={label}>
              {label} total differs from the sum of the displayed evidence rows.
            </p>
          ))}
          {analysis.invalidMoney ? (
            <p role="alert">
              An amount is malformed or has unsupported precision. It is not
              converted to zero.
            </p>
          ) : null}
          {!analysis.structurallyValid ? (
            <p role="alert">
              Duplicate or out-of-year periods detected. Ambiguous periods are
              excluded from derived comparisons, which remain unavailable until
              reviewed.
            </p>
          ) : null}
          <div
            className="grid grid-cols-3 gap-2 sm:grid-cols-6"
            aria-label="Evidence coverage calendar"
          >
            {analysis.slots.map((slot) => (
              <div className="rounded border p-2 text-xs" key={slot.period}>
                <strong>{monthName(slot.period)}</strong>
                <p>
                  {slot.conflict
                    ? 'Duplicate - review'
                    : slot.row
                      ? 'Published record'
                      : 'No record in this pack'}
                </p>
              </div>
            ))}
          </div>
          <p className="text-muted-foreground text-xs">
            No record does not mean zero. Coverage does not assert that every
            absent month is overdue.
          </p>
        </CardContent>
      </Card>

      <div className="grid gap-4 xl:grid-cols-2">
        <FlowChart analysis={analysis} />
        <DeductionChart analysis={analysis} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Evidence drill-down</CardTitle>
          <CardDescription>
            Open the calculation inputs and source details before following the
            proof link.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {analysis.rows.map((row) => {
            const href = proofHref(row.month)
            return (
              <details
                className="rounded border p-4"
                key={row.month.revenue_month}
              >
                <summary className="cursor-pointer text-sm font-semibold">
                  {monthName(row.month.revenue_month)} / Net {money(row.net)}
                </summary>
                <dl className="mt-3 grid gap-3 text-sm sm:grid-cols-3">
                  <div>
                    <dt>Gross allocation</dt>
                    <dd>{money(row.gross)}</dd>
                  </div>
                  <div>
                    <dt>Deductions</dt>
                    <dd>{money(row.deductions)}</dd>
                  </div>
                  <div>
                    <dt>Arithmetic residual</dt>
                    <dd>{money(row.residual)}</dd>
                  </div>
                </dl>
                <p className="mt-3 text-sm">
                  {row.month.source_organization} /{' '}
                  {row.month.reconciliation_status} /{' '}
                  {row.month.human_verified
                    ? 'Human verified'
                    : 'Verification incomplete'}
                </p>
                <p className="mt-2 font-mono text-xs break-all">
                  {row.month.proof_id}
                  <br />
                  SHA-256 {row.month.source_sha256}
                </p>
                {href ? (
                  <Link
                    className="text-primary mt-3 inline-block text-sm"
                    href={href}
                  >
                    Verify proof &#8594;
                  </Link>
                ) : (
                  <p>Proof link unavailable.</p>
                )}
              </details>
            )
          })}
        </CardContent>
      </Card>
      <p className="text-muted-foreground text-xs leading-5">
        No interpolation, unpublished IGR estimate, peer ranking or debt
        conclusion is introduced by this view. Monitoring opens the existing
        watchlist workflow; it does not silently subscribe a customer or alter a
        paid artifact.
      </p>
    </section>
  )
}
