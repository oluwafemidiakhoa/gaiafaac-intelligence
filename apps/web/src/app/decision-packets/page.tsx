import type { Metadata } from 'next'
import Link from 'next/link'

import { DataUnavailable } from '@/components/data-unavailable'
import { PageHeader } from '@/components/page-header'
import { StatusPill } from '@/components/status-pill'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { getFiscalPulse } from '@/lib/fiscal-pulse-api'
import { formatNaira } from '@/lib/format'

export const metadata: Metadata = { title: 'Decision Packets' }
export const dynamic = 'force-dynamic'

interface DecisionPacketsPageProps {
  searchParams: Promise<{ year?: string }>
}

export default async function DecisionPacketsPage({
  searchParams,
}: DecisionPacketsPageProps) {
  const params = await searchParams
  const currentYear = new Date().getUTCFullYear()
  const parsedYear = Number(params.year ?? currentYear)
  const year = Number.isInteger(parsedYear) ? parsedYear : currentYear
  const result = await getFiscalPulse(year)
  const data = result.data
  const states = data
    ? [...data.states].sort((a, b) => a.state_name.localeCompare(b.state_name))
    : []

  return (
    <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
      <PageHeader
        eyebrow="Decision Packets"
        title="Print-ready fiscal evidence dossiers"
        description="Choose a jurisdiction and year to open a Decision Packet built from published Fiscal Pulse metrics, Fiscal Watch signals, and monthly Fiscal Proofs."
      />

      <Card className="mt-8">
        <CardHeader>
          <CardTitle>Select year</CardTitle>
          <CardDescription>
            Only published, non-demo GaiaFAAC records are included.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form method="get" className="flex flex-wrap items-end gap-3">
            <label className="grid gap-2 text-sm font-medium">
              Year
              <input
                name="year"
                type="number"
                min="2000"
                max="2100"
                defaultValue={year}
                className="border-input bg-background h-10 w-32 rounded-md border px-3 text-sm"
              />
            </label>
            <button
              type="submit"
              className="bg-primary text-primary-foreground h-10 rounded-md px-4 text-sm font-medium"
            >
              Load packets
            </button>
          </form>
        </CardContent>
      </Card>

      {data === null ? (
        <div className="mt-8">
          <DataUnavailable
            message={result.error ?? 'Decision Packets are unavailable.'}
          />
        </div>
      ) : (
        <Card className="mt-8">
          <CardHeader>
            <CardTitle>{year} jurisdiction packets</CardTitle>
            <CardDescription>{data.coverage_label}</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {states.map((state) => (
              <Link
                key={state.state_code}
                href={`/decision-packets/${state.state_slug}?year=${year}`}
                className="border-border hover:border-primary/40 rounded-lg border p-4 transition-colors"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="font-medium">{state.state_name}</p>
                    <p className="text-muted-foreground mt-1 text-xs">
                      {state.geopolitical_zone}
                    </p>
                  </div>
                  <span className="text-muted-foreground font-mono text-xs">
                    {state.state_code}
                  </span>
                </div>

                <div className="mt-4 flex items-end justify-between gap-3">
                  <div>
                    <p className="text-muted-foreground text-xs">
                      Published-period net
                    </p>
                    <p className="mt-1 font-mono text-sm font-semibold">
                      {formatNaira(state.annual_net)}
                    </p>
                  </div>
                  <StatusPill tone="success">{state.evidence_status}</StatusPill>
                </div>

                <p className="text-primary mt-4 text-sm font-medium">
                  Open Decision Packet →
                </p>
              </Link>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  )
}
