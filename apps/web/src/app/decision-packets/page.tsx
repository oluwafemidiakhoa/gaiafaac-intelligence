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
      <div style={{ fontFamily: 'Georgia, serif' }}>
        <PageHeader
          eyebrow="Decision Packets"
          title="Print-Ready Evidence Dossiers"
          description="Generate institutional decision briefs from verified Fiscal Pulse metrics, Fiscal Watch signals, and monthly Fiscal Proofs for each jurisdiction."
        />
      </div>

      <div className="mt-8 rounded-lg bg-teal-50 border border-teal-200 p-6">
        <h3 className="font-semibold text-teal-950 mb-4">Select Report Year</h3>
        <form method="get" className="flex flex-wrap items-end gap-3">
          <label className="grid gap-2">
            <span className="text-sm font-medium text-teal-900">Year</span>
            <input
              name="year"
              type="number"
              min="2000"
              max="2100"
              defaultValue={year}
              className="border-teal-300 bg-white h-10 w-32 rounded-lg border px-3 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
            />
          </label>
          <button
            type="submit"
            className="bg-teal-900 text-white h-10 rounded-lg px-6 text-sm font-semibold hover:bg-teal-800 transition-colors"
          >
            Load packets
          </button>
        </form>
      </div>

      {data === null ? (
        <div className="mt-8">
          <DataUnavailable
            message={result.error ?? 'Decision Packets are unavailable.'}
          />
        </div>
      ) : (
        <>
          <div className="mt-8 rounded-lg bg-white border border-slate-200 p-5">
            <h2 className="font-semibold text-slate-950 mb-2" style={{ fontFamily: 'Georgia, serif' }}>
              {year} Jurisdiction Packets
            </h2>
            <p className="text-slate-600 text-sm">{data.coverage_label}</p>
          </div>

          <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {states.map((state) => (
              <Link
                key={state.state_code}
                href={`/decision-packets/${state.state_slug}?year=${year}`}
                className="group rounded-lg border-2 border-teal-200 bg-white p-5 transition-all hover:border-teal-500 hover:shadow-lg"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1">
                    <p className="font-semibold text-teal-950 group-hover:text-teal-700">
                      {state.state_name}
                    </p>
                    <p className="text-slate-600 mt-1 text-xs">
                      {state.geopolitical_zone}
                    </p>
                  </div>
                  <span className="text-slate-500 font-mono text-xs bg-slate-100 px-2 py-1 rounded">
                    {state.state_code}
                  </span>
                </div>

                <div className="border-t border-slate-200 mt-4 pt-4">
                  <p className="text-xs uppercase tracking-wide text-slate-600 font-medium">
                    Published-Period Net
                  </p>
                  <p className="font-mono text-lg font-bold text-teal-950 mt-1">
                    {formatNaira(state.annual_net)}
                  </p>
                </div>

                <div className="mt-4 flex items-center justify-between">
                  <StatusPill tone="success">
                    {state.evidence_status}
                  </StatusPill>
                  <span className="text-teal-700 text-sm font-medium group-hover:underline">
                    Open →
                  </span>
                </div>
              </Link>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
