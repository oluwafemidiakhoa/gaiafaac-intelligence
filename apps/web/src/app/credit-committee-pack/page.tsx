import type { Metadata } from 'next'
import Link from 'next/link'

import { DataUnavailable } from '@/components/data-unavailable'
import { PageHeader } from '@/components/page-header'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { getDecisionPacket } from '@/lib/decision-packet-api'
import { formatNaira } from '@/lib/format'

export const metadata: Metadata = {
  title: 'Credit Committee Evidence Pack',
  description:
    'A governed underwriting evidence pack that keeps fiscal facts, missing evidence, monitoring triggers and source provenance explicit.',
}
export const dynamic = 'force-dynamic'

interface PageProps {
  searchParams: Promise<{ state?: string; year?: string }>
}

function pct(value: number | null) {
  return value === null ? 'Unavailable' : `${value.toFixed(2)}%`
}

export default async function CreditCommitteePackPage({ searchParams }: PageProps) {
  const params = await searchParams
  const currentYear = new Date().getUTCFullYear()
  const yearValue = Number(params.year ?? currentYear)
  const year = Number.isInteger(yearValue) ? yearValue : currentYear
  const state = (params.state ?? '').trim().toLowerCase()
  const result = state ? await getDecisionPacket(state, year) : null
  const packet = result?.data ?? null

  return (
    <div className="gaia-shell py-12 lg:py-16">
      <PageHeader
        eyebrow="Institutional underwriting workflow"
        title="Credit Committee Evidence Pack"
        description="A reusable evidence dossier for underwriting, investment review and diligence. It reports governed fiscal evidence and explicit gaps; it does not issue a credit rating, default probability or solvency opinion."
      />

      <Card className="mt-8">
        <CardHeader>
          <CardTitle>Build an evidence pack</CardTitle>
          <CardDescription>
            Enter a Gaia state slug and evidence year. The pack uses the same published Decision Packet source of truth rather than duplicating calculations.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form method="get" className="grid gap-4 sm:grid-cols-[1fr_9rem_auto]">
            <label className="grid gap-2 text-sm font-medium">
              State slug
              <input
                name="state"
                defaultValue={state}
                placeholder="lagos"
                className="border-input bg-background h-11 rounded-md border px-3 text-sm"
                required
              />
            </label>
            <label className="grid gap-2 text-sm font-medium">
              Year
              <input
                name="year"
                type="number"
                min="2000"
                max="2100"
                defaultValue={year}
                className="border-input bg-background h-11 rounded-md border px-3 text-sm"
              />
            </label>
            <div className="flex items-end">
              <Button type="submit" className="h-11 w-full">
                Generate pack
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {state && !packet ? (
        <div className="mt-8">
          <DataUnavailable message={result?.error ?? 'No governed evidence pack is available for this selection.'} />
        </div>
      ) : null}

      {packet ? (
        <div className="mt-8 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>
                {packet.state_name} · {packet.year}
              </CardTitle>
              <CardDescription>
                Evidence status: {packet.evidence_status} · {packet.coverage_label}
              </CardDescription>
            </CardHeader>
            <CardContent className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
              <div>
                <p className="text-muted-foreground text-xs uppercase">FAAC net</p>
                <p className="mt-1 font-mono font-semibold">
                  {packet.annual_net ? formatNaira(packet.annual_net) : 'Unavailable'}
                </p>
              </div>
              <div>
                <p className="text-muted-foreground text-xs uppercase">Deduction burden</p>
                <p className="mt-1 font-mono font-semibold">{pct(packet.deduction_burden_pct)}</p>
              </div>
              <div>
                <p className="text-muted-foreground text-xs uppercase">Net retention</p>
                <p className="mt-1 font-mono font-semibold">{pct(packet.net_retention_pct)}</p>
              </div>
              <div>
                <p className="text-muted-foreground text-xs uppercase">FAAC months</p>
                <p className="mt-1 font-mono font-semibold">{packet.months_published}/12</p>
              </div>
            </CardContent>
          </Card>

          <div className="grid gap-5 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>FAAC exposure and trend</CardTitle>
                <CardDescription>Published allocation evidence only.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                <p>Momentum: <strong>{packet.momentum}</strong>{packet.momentum_pct === null ? '' : ` · ${pct(packet.momentum_pct)}`}</p>
                <p>Volatility: <strong>{packet.volatility}</strong>{packet.volatility_cv_pct === null ? '' : ` · CV ${pct(packet.volatility_cv_pct)}`}</p>
                <p className="text-muted-foreground">No missing month is inferred or annualized.</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>IGR evidence</CardTitle>
                <CardDescription>Kept separate from FAAC to avoid mixing evidence domains.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                {packet.igr_records.length ? (
                  packet.igr_records.map((record) => (
                    <div key={`${record.fiscal_year}-${record.period_type}-${record.quarter ?? 'annual'}`} className="border-border rounded-lg border p-3">
                      <p className="font-medium">{record.period_type} {record.quarter ? `Q${record.quarter}` : ''}</p>
                      <p className="mt-1 font-mono">{formatNaira(record.igr_amount)}</p>
                      <p className="text-muted-foreground mt-1 text-xs">{record.source_organization}</p>
                    </div>
                  ))
                ) : (
                  <p className="text-muted-foreground">{packet.igr_note}</p>
                )}
              </CardContent>
            </Card>
          </div>

          <div className="grid gap-5 lg:grid-cols-3">
            {[
              ['Debt & debt service', 'Not asserted unless a comparable governed debt lane is available for this jurisdiction and period.'],
              ['Budget & expenditure', 'Not asserted unless published governed budget/expenditure evidence is available for the same review boundary.'],
              ['Peer comparison', 'Use Gaia Compare for a declared peer set; the pack does not choose peers or manufacture a benchmark automatically.'],
            ].map(([title, body]) => (
              <Card key={title}>
                <CardHeader><CardTitle className="text-lg">{title}</CardTitle></CardHeader>
                <CardContent className="text-muted-foreground text-sm leading-6">{body}</CardContent>
              </Card>
            ))}
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Monitoring triggers</CardTitle>
              <CardDescription>Observed fiscal-watch events for this evidence year.</CardDescription>
            </CardHeader>
            <CardContent>
              {packet.watch_events.length ? (
                <div className="space-y-3">
                  {packet.watch_events.map((event, index) => (
                    <div key={`${event.kind}-${index}`} className="border-border rounded-lg border p-4 text-sm">
                      <p className="font-semibold">{event.headline}</p>
                      <p className="text-muted-foreground mt-1 leading-6">{event.detail}</p>
                      <Link href={event.proof_path} className="mt-2 inline-block font-medium text-teal-800 hover:underline">Inspect proof →</Link>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-muted-foreground text-sm">No governed watch event is recorded for this selection.</p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Sources, gaps and review boundary</CardTitle>
              <CardDescription>The pack makes unavailable evidence visible instead of filling it.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 text-sm">
              <p>{packet.disclaimer}</p>
              <p className="text-muted-foreground">Analyst interpretation and reviewer sign-off belong in a Decision Room, separate from the evidence objects above.</p>
              <div className="flex flex-wrap gap-3">
                <Button asChild><Link href="/decision-rooms">Save review in a Decision Room</Link></Button>
                <Button asChild variant="outline"><Link href={`/compare?states=${encodeURIComponent(packet.state_slug)}`}>Open peer comparison</Link></Button>
                <Button asChild variant="outline"><Link href="/watch-contracts">Configure monitoring</Link></Button>
              </div>
            </CardContent>
          </Card>
        </div>
      ) : null}
    </div>
  )
}
