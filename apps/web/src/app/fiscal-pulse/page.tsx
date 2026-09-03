import {
  Activity,
  ArrowRight,
  BarChart3,
  BrainCircuit,
  ShieldCheck,
  TrendingUp,
} from 'lucide-react'
import type { Metadata } from 'next'
import Link from 'next/link'

import { DataUnavailable } from '@/components/data-unavailable'
import { MetricCard } from '@/components/metric-card'
import { PageHeader } from '@/components/page-header'
import { StatusPill } from '@/components/status-pill'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { getFiscalPulse } from '@/lib/fiscal-pulse-api'
import { formatNaira } from '@/lib/format'

export const metadata: Metadata = { title: 'Fiscal Intelligence' }
export const dynamic = 'force-dynamic'

function percent(value: number | null): string {
  return value === null ? 'Unavailable' : `${value.toFixed(1)}%`
}

function signalTone(value: string): 'success' | 'neutral' | 'demo' {
  if (value === 'Improving' || value === 'Verified' || value === 'Low')
    return 'success'
  if (value === 'Weakening' || value === 'Review required' || value === 'High')
    return 'demo'
  return 'neutral'
}

export default async function FiscalPulsePage() {
  const result = await getFiscalPulse(2024)
  const data = result.data

  if (!data || data.months_published === 0) {
    return (
      <div className="gaia-shell gaia-section">
        <PageHeader
          eyebrow="Intelligence / Fiscal Pulse"
          title="Verified fiscal intelligence for Nigerian states"
          description="Gaia derives signals only from published, human-approved evidence. When the evidence layer is unavailable, intelligence stays unavailable too."
        />
        <div className="mt-10">
          <DataUnavailable
            message={result.error ?? 'No verified 2024 data is available.'}
          />
        </div>
      </div>
    )
  }

  const completeYear = data.coverage_status === 'complete_year'
  const completeStates = data.states.filter(
    (state) => state.evidence_status === 'Verified',
  ).length
  const improving = data.states.filter(
    (state) => state.momentum === 'Improving',
  ).length
  const highVolatility = data.states.filter(
    (state) => state.volatility === 'High',
  ).length
  const periodLabel = completeYear
    ? 'Annual 2024'
    : `Partial 2024 (${data.months_published}/12 months)`

  return (
    <div className="pb-8">
      <section className="border-b border-white/8 bg-[#061d19] text-white">
        <div className="gaia-shell grid gap-10 py-14 lg:grid-cols-[1.05fr_.95fr] lg:items-end lg:py-20">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-emerald-300/15 bg-emerald-300/[0.07] px-3 py-1.5">
              <BrainCircuit className="size-3.5 text-emerald-300" />
              <span className="font-mono text-[0.65rem] font-bold tracking-[0.18em] text-emerald-100 uppercase">
                Intelligence / {periodLabel}
              </span>
            </div>
            <h1 className="mt-6 max-w-[13ch] text-5xl leading-[0.98] font-semibold tracking-[-0.055em] text-balance sm:text-6xl lg:text-7xl">
              See the fiscal signal. Keep the evidence attached.
            </h1>
            <p className="mt-6 max-w-2xl text-lg leading-8 text-emerald-50/65">
              Compare allocation momentum, deduction burden, retention and
              volatility across Nigerian states without separating the signal
              from its publication status.
            </p>
          </div>

          <div className="gaia-panel-dark overflow-hidden p-6 sm:p-7">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-mono text-[0.65rem] font-semibold tracking-[0.16em] text-white/40 uppercase">
                  Intelligence confidence
                </p>
                <p className="mt-2 text-xl font-semibold">Published-evidence scope</p>
              </div>
              <div className="flex size-11 items-center justify-center rounded-2xl border border-emerald-300/15 bg-emerald-300/[0.08]">
                <ShieldCheck className="size-5 text-emerald-300" />
              </div>
            </div>
            <div className="mt-7 grid grid-cols-3 divide-x divide-white/10 rounded-2xl border border-white/10 bg-white/[0.035]">
              <div className="p-4">
                <p className="font-mono text-[0.58rem] tracking-[0.14em] text-white/35 uppercase">Months</p>
                <p className="mt-2 font-mono text-xl font-semibold">{data.months_published}/{data.expected_months}</p>
              </div>
              <div className="p-4">
                <p className="font-mono text-[0.58rem] tracking-[0.14em] text-white/35 uppercase">Verified</p>
                <p className="mt-2 font-mono text-xl font-semibold">{completeStates}</p>
              </div>
              <div className="p-4">
                <p className="font-mono text-[0.58rem] tracking-[0.14em] text-white/35 uppercase">Mode</p>
                <p className="mt-2 text-sm font-semibold text-emerald-200">Evidence bound</p>
              </div>
            </div>
            <p className="mt-5 text-xs leading-5 text-white/45">
              Descriptive intelligence only. Missing inputs remain unavailable;
              Gaia does not synthesize credit-risk or governance judgments.
            </p>
          </div>
        </div>
      </section>

      <div className="gaia-shell gaia-section">
        {!completeYear ? (
          <div className="mb-8 flex gap-4 rounded-2xl border border-amber-300/35 bg-amber-100/45 p-5 text-sm leading-6 dark:bg-amber-300/[0.07]">
            <Activity className="mt-0.5 size-5 shrink-0 text-amber-700 dark:text-amber-300" />
            <div>
              <p className="font-semibold">Partial-year intelligence boundary</p>
              <p className="text-muted-foreground mt-1">
                {data.coverage_label}. Every total below represents only the
                published months and is not a complete annual 2024 total.
              </p>
            </div>
          </div>
        ) : null}

        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <MetricCard
            label="Published months"
            value={`${data.months_published}/${data.expected_months}`}
            detail={data.latest_period_label ?? '2024 verified series'}
          />
          <MetricCard
            label="Verified profiles"
            value={String(completeStates)}
            detail="Complete gross, deductions and net across each published month."
          />
          <MetricCard
            label="Improving momentum"
            value={String(improving)}
            detail="Latest 3-month average >5% above the preceding 3 months."
          />
          <MetricCard
            label="High volatility"
            value={String(highVolatility)}
            detail="Descriptive allocation variability, not a credit-risk rating."
          />
        </div>

        <div className="mt-8 grid gap-5 xl:grid-cols-[1fr_300px]">
          <Card className="overflow-hidden">
            <CardHeader className="border-border/70 border-b bg-muted/20">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <BarChart3 className="text-primary size-5" />
                    <CardTitle className="text-xl">State intelligence matrix</CardTitle>
                  </div>
                  <CardDescription className="mt-2 max-w-2xl">
                    {periodLabel} signals derived only from governed published
                    records, with evidence status preserved per jurisdiction.
                  </CardDescription>
                </div>
                <Button asChild variant="outline" size="sm">
                  <Link href="/live">Open live board</Link>
                </Button>
              </div>
            </CardHeader>
            <CardContent className="overflow-x-auto pt-2">
              <table className="w-full min-w-[1050px] border-collapse text-left text-sm">
                <thead>
                  <tr className="border-border text-muted-foreground border-b">
                    <th className="py-4 pr-4 font-medium">Jurisdiction</th>
                    <th className="py-4 pr-4 text-right font-medium">Published-period net</th>
                    <th className="py-4 pr-4 text-right font-medium">Deduction burden</th>
                    <th className="py-4 pr-4 text-right font-medium">Net retention</th>
                    <th className="py-4 pr-4 font-medium">Momentum</th>
                    <th className="py-4 pr-4 font-medium">Volatility</th>
                    <th className="py-4 font-medium">Evidence</th>
                  </tr>
                </thead>
                <tbody>
                  {data.states.map((state) => (
                    <tr
                      key={state.state_slug}
                      className="border-border/70 group border-b transition-colors last:border-0 hover:bg-primary/[0.025]"
                    >
                      <td className="py-4 pr-4">
                        <Link
                          href={`/states/${state.state_slug}`}
                          className="font-semibold tracking-tight hover:text-primary"
                        >
                          {state.state_name}
                        </Link>
                        <span className="text-muted-foreground ml-2 text-xs">
                          {state.geopolitical_zone}
                        </span>
                      </td>
                      <td className="py-4 pr-4 text-right font-mono font-semibold">
                        {formatNaira(state.annual_net)}
                      </td>
                      <td className="py-4 pr-4 text-right font-mono">
                        {percent(state.deduction_burden_pct)}
                      </td>
                      <td className="py-4 pr-4 text-right font-mono">
                        {percent(state.net_retention_pct)}
                      </td>
                      <td className="py-4 pr-4">
                        <StatusPill tone={signalTone(state.momentum)}>
                          {state.momentum}
                        </StatusPill>
                      </td>
                      <td className="py-4 pr-4">
                        <StatusPill tone={signalTone(state.volatility)}>
                          {state.volatility}
                        </StatusPill>
                      </td>
                      <td className="py-4">
                        <StatusPill tone={signalTone(state.evidence_status)}>
                          {state.evidence_status}
                        </StatusPill>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CardContent>
          </Card>

          <div className="space-y-5">
            <Card>
              <CardHeader>
                <TrendingUp className="text-primary size-5" />
                <CardTitle className="mt-4 text-lg">Signal interpretation</CardTitle>
                <CardDescription>
                  Momentum compares the latest three available monthly net
                  allocations with the preceding three. Volatility uses
                  coefficient of variation.
                </CardDescription>
              </CardHeader>
              <CardContent className="text-muted-foreground space-y-3 text-sm leading-6">
                <p>
                  These metrics do not measure creditworthiness, solvency,
                  corruption, governance quality or default risk.
                </p>
                <Link href="/methodology" className="text-foreground inline-flex items-center gap-1.5 font-semibold">
                  Read methodology <ArrowRight className="size-3.5" />
                </Link>
              </CardContent>
            </Card>

            <div className="gaia-panel-dark p-6">
              <BrainCircuit className="size-5 text-amber-300" />
              <p className="mt-5 font-mono text-[0.62rem] font-semibold tracking-[0.16em] text-amber-200/55 uppercase">
                Institutional intelligence
              </p>
              <h2 className="mt-2 text-xl font-semibold tracking-tight">
                Move from signal to governed decision.
              </h2>
              <p className="mt-3 text-sm leading-6 text-white/55">
                Historical intelligence, controlled exports, organization
                analysis and API access are available through commercial plans.
              </p>
              <Button asChild className="mt-5 w-full bg-amber-300 font-bold text-teal-950 hover:bg-amber-200">
                <Link href="/pricing">Explore access</Link>
              </Button>
            </div>
          </div>
        </div>

        <p className="text-muted-foreground mt-8 text-xs leading-5">{data.note}</p>
      </div>
    </div>
  )
}
