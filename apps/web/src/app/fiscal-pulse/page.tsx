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

export const metadata: Metadata = { title: 'Fiscal Pulse' }
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
      <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
        <PageHeader
          eyebrow="Fiscal Pulse"
          title="Verified fiscal intelligence for Nigerian states"
          description="Derived only from published, human-approved allocation records."
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
  const periodLabel = completeYear ? 'Annual 2024' : `Partial 2024 (${data.months_published}/12 months)`

  return (
    <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
      <PageHeader
        eyebrow={`GaiaFAAC Fiscal Pulse · ${periodLabel}`}
        title="Verified fiscal intelligence for every Nigerian state"
        description="Compare published-period allocations, deduction burden, net retention, momentum and allocation volatility—with evidence status attached to every signal."
      />

      {!completeYear ? (
        <div className="border-primary/30 bg-primary/5 mt-8 rounded-lg border p-5 text-sm leading-6">
          <p className="font-semibold">Partial-year coverage</p>
          <p className="text-muted-foreground mt-1">
            {data.coverage_label}. Every total below represents only the published months and must not be interpreted as a complete annual 2024 total.
          </p>
        </div>
      ) : null}

      <div className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          label="Published months"
          value={`${data.months_published}/${data.expected_months}`}
          detail={data.latest_period_label ?? '2024 verified series'}
        />
        <MetricCard
          label="Verified state profiles"
          value={String(completeStates)}
          detail="Complete gross, deductions and net across every currently published month."
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

      <Card className="mt-8">
        <CardHeader>
          <CardTitle>State Fiscal Pulse</CardTitle>
          <CardDescription>
            {periodLabel} signals derived only from published, non-demo records. Missing inputs remain unavailable.
          </CardDescription>
        </CardHeader>
        <CardContent className="overflow-x-auto">
          <table className="w-full min-w-[1050px] border-collapse text-left text-sm">
            <thead>
              <tr className="border-border text-muted-foreground border-b">
                <th className="py-3 pr-4 font-medium">State</th>
                <th className="py-3 pr-4 text-right font-medium">Published-period net</th>
                <th className="py-3 pr-4 text-right font-medium">Deduction burden</th>
                <th className="py-3 pr-4 text-right font-medium">Net retention</th>
                <th className="py-3 pr-4 font-medium">Momentum</th>
                <th className="py-3 pr-4 font-medium">Volatility</th>
                <th className="py-3 font-medium">Evidence</th>
              </tr>
            </thead>
            <tbody>
              {data.states.map((state) => (
                <tr key={state.state_slug} className="border-border border-b last:border-0">
                  <td className="py-3 pr-4">
                    <Link href={`/states/${state.state_slug}`} className="hover:text-primary font-medium">
                      {state.state_name}
                    </Link>
                    <span className="text-muted-foreground ml-2 text-xs">{state.geopolitical_zone}</span>
                  </td>
                  <td className="py-3 pr-4 text-right font-mono font-semibold">{formatNaira(state.annual_net)}</td>
                  <td className="py-3 pr-4 text-right font-mono">{percent(state.deduction_burden_pct)}</td>
                  <td className="py-3 pr-4 text-right font-mono">{percent(state.net_retention_pct)}</td>
                  <td className="py-3 pr-4">
                    <StatusPill tone={signalTone(state.momentum)}>{state.momentum}</StatusPill>
                  </td>
                  <td className="py-3 pr-4">
                    <StatusPill tone={signalTone(state.volatility)}>{state.volatility}</StatusPill>
                  </td>
                  <td className="py-3">
                    <StatusPill tone={signalTone(state.evidence_status)}>{state.evidence_status}</StatusPill>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>

      <div className="mt-8 grid gap-5 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>How to interpret the signals</CardTitle>
            <CardDescription>
              Momentum compares the latest three available monthly net allocations with the preceding three. Volatility uses coefficient of variation.
            </CardDescription>
          </CardHeader>
          <CardContent className="text-muted-foreground space-y-3 text-sm leading-6">
            <p>These metrics describe allocation patterns only. They do not measure creditworthiness, solvency, corruption, governance quality or default risk.</p>
            <p>Broader fiscal-risk analysis would require additional evidence such as IGR, debt service, debt stock, expenditure and liabilities.</p>
            <Link href="/methodology" className="text-foreground font-medium hover:underline">Read the methodology →</Link>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Need the complete historical intelligence?</CardTitle>
            <CardDescription>Request licensed historical data, organization analysis or controlled API access.</CardDescription>
          </CardHeader>
          <CardContent>
            <Button asChild><Link href="/pilot?plan=analyst">Request pilot access</Link></Button>
            <p className="text-muted-foreground mt-4 text-sm">Commercial enquiries: gaiafacc@gailabai.com</p>
          </CardContent>
        </Card>
      </div>

      <p className="text-muted-foreground mt-8 text-xs leading-5">{data.note}</p>
    </div>
  )
}
