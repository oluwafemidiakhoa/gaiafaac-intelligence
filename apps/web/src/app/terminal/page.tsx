import type { Metadata } from 'next'
import Link from 'next/link'
import {
  ArrowUpRight,
  BarChart3,
  FileCheck2,
  Landmark,
  ShieldCheck,
} from 'lucide-react'

import { DataUnavailable } from '@/components/data-unavailable'
import { GaiaTerminalSearch } from '@/components/gaia-terminal-search'
import { StatusPill } from '@/components/status-pill'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { getEvidenceNetworkStatus } from '@/lib/evidence-network-api'
import { formatDate, formatNaira } from '@/lib/format'
import { getPublishedOverview } from '@/lib/published-api'

export const metadata: Metadata = {
  title: 'Gaia Fiscal Intelligence',
  description:
    'Evidence-led public-finance intelligence for Nigeria: source-linked allocation, revenue and debt research for institutional decisions.',
}
export const dynamic = 'force-dynamic'

const workflows = [
  {
    href: '/gaia-analyst',
    title: 'Ask Gaia',
    description: 'Ask a fiscal question and inspect the evidence used.',
  },
  {
    href: '/fiscal-watch',
    title: 'Fiscal Watch',
    description: 'Monitor changes that need institutional attention.',
  },
  {
    href: '/decision-packets',
    title: 'Decision Packets',
    description: 'Turn verified evidence into a review-ready brief.',
  },
] as const

function compactNaira(value: string | null) {
  if (!value) return '—'
  const amount = Number(value)
  if (!Number.isFinite(amount)) return formatNaira(value)
  if (Math.abs(amount) >= 1_000_000_000_000)
    return `₦${(amount / 1_000_000_000_000).toFixed(2)}T`
  if (Math.abs(amount) >= 1_000_000_000)
    return `₦${(amount / 1_000_000_000).toFixed(2)}B`
  return formatNaira(value)
}

export default async function GaiaTerminalPage() {
  const overview = await getPublishedOverview()
  const data = overview.data
  const evidenceNetwork = await getEvidenceNetworkStatus({
    oagfLive: data !== null,
    oagfPeriod: data?.period.reporting_label ?? null,
  })
  const evidenceLanes = evidenceNetwork.data

  return (
    <main className="mx-auto max-w-7xl px-5 py-10 lg:px-8 lg:py-14">
      <section className="grid gap-8 border-b border-teal-900/10 pb-10 lg:grid-cols-[1.3fr_0.7fr] lg:items-end">
        <div className="max-w-3xl">
          <p className="text-xs font-semibold tracking-[0.2em] text-teal-900 uppercase">
            Gaia Fiscal Intelligence
          </p>
          <h1
            className="mt-5 text-4xl font-semibold tracking-[-0.045em] text-teal-950 sm:text-5xl lg:text-6xl"
            style={{ fontFamily: 'Georgia, serif' }}
          >
            Know what changed before it becomes a problem.
          </h1>
          <p className="mt-6 max-w-2xl text-base leading-8 text-teal-700 sm:text-lg">
            Evidence-led public-finance intelligence for Nigeria. Gaia keeps
            official allocation, revenue, debt and macro evidence separate,
            traceable and ready for a real decision.
          </p>
          <div className="mt-7 flex flex-wrap gap-3">
            <Link
              href="/gaia-analyst"
              className="inline-flex items-center gap-2 rounded-md bg-teal-900 px-5 py-3 text-sm font-semibold text-white transition-opacity hover:opacity-90"
            >
              Ask Gaia <ArrowUpRight className="size-4" aria-hidden="true" />
            </Link>
            <Link
              href="/sources"
              className="inline-flex items-center gap-2 rounded-md border border-teal-900 bg-white px-5 py-3 text-sm font-semibold text-teal-900 transition-colors hover:bg-teal-50"
            >
              Inspect the evidence
            </Link>
          </div>
        </div>
        <aside className="rounded-2xl bg-teal-900 p-6 text-white shadow-xl shadow-teal-900/20 sm:p-7">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-xs font-semibold tracking-[0.18em] text-amber-200 uppercase">
                Live evidence
              </p>
              <h2 className="mt-3 text-xl font-semibold">
                OAGF / FAAC allocation ledger
              </h2>
            </div>
            <ShieldCheck className="size-6 text-amber-300" aria-hidden="true" />
          </div>
          <p className="mt-5 text-sm leading-6 text-teal-50/80">
            Every public figure is tied to a retained source document and its
            SHA-256 fingerprint. Missing evidence stays unavailable.
          </p>
          <div className="mt-6 border-t border-white/15 pt-5">
            <p className="font-mono text-2xl font-semibold">
              {data ? `${data.covered_states}/${data.expected_states}` : '—'}
            </p>
            <p className="mt-1 text-xs text-amber-200/75">
              jurisdictions in the latest published allocation
            </p>
          </div>
        </aside>
      </section>

      {data ? (
        <>
          <section className="grid divide-y border-b border-teal-900/10 sm:grid-cols-3 sm:divide-x sm:divide-y-0">
            <div className="py-6 sm:pr-6">
              <p className="text-xs font-medium tracking-wide text-teal-600 uppercase">
                Latest verified allocation
              </p>
              <p className="mt-2 text-2xl font-semibold tracking-tight text-teal-950">
                {formatDate(data.period.revenue_month)}
              </p>
              <p className="mt-2 text-sm leading-6 text-teal-600">
                {data.period.reporting_label}
              </p>
            </div>
            <div className="py-6 sm:px-6">
              <p className="text-xs font-medium tracking-wide text-teal-600 uppercase">
                State ledger total
              </p>
              <p className="mt-2 text-2xl font-semibold tracking-tight text-teal-950">
                {compactNaira(data.total_net)}
              </p>
              <p className="mt-2 text-sm leading-6 text-teal-600">
                Published state and FCT net allocations
              </p>
            </div>
            <div className="py-6 sm:pl-6">
              <p className="text-xs font-medium tracking-wide text-teal-600 uppercase">
                Evidence status
              </p>
              <div className="mt-2 flex items-center gap-2">
                <FileCheck2
                  className="size-5 text-teal-900"
                  aria-hidden="true"
                />
                <p className="text-2xl font-semibold tracking-tight text-teal-950">
                  Source-linked
                </p>
              </div>
              <Link
                href="/sources"
                className="mt-2 inline-flex items-center gap-1 text-sm font-medium text-teal-900 hover:underline"
              >
                Verify fingerprint{' '}
                <ArrowUpRight className="size-3.5" aria-hidden="true" />
              </Link>
            </div>
          </section>

          <section className="mt-10">
            <div className="flex flex-wrap items-end justify-between gap-4">
              <div>
                <p className="text-xs font-semibold tracking-[0.18em] text-teal-900 uppercase">
                  Evidence network
                </p>
                <h2
                  className="mt-2 text-2xl font-semibold tracking-tight text-teal-950"
                  style={{ fontFamily: 'Georgia, serif' }}
                >
                  A fiscal picture built source by source.
                </h2>
              </div>
              <p className="max-w-md text-sm leading-6 text-teal-700">
                Status is derived from governed published records. If Gaia
                cannot verify a lane, it says so instead of guessing.
              </p>
            </div>
            {evidenceLanes ? (
              <div className="mt-5 grid gap-px overflow-hidden rounded-xl border border-teal-900/10 bg-teal-900/5 sm:grid-cols-2 lg:grid-cols-5">
                {evidenceLanes.map((lane) => (
                  <article key={lane.authority} className="bg-white p-5">
                    <div className="flex items-center justify-between gap-2">
                      <Landmark
                        className="size-4 text-teal-900"
                        aria-hidden="true"
                      />
                      <StatusPill
                        tone={lane.state === 'Live' ? 'success' : 'neutral'}
                      >
                        {lane.state}
                      </StatusPill>
                    </div>
                    <p className="mt-5 text-base font-semibold text-teal-950">
                      {lane.authority}
                    </p>
                    <p className="mt-1 text-sm font-medium text-teal-700">
                      {lane.label}
                    </p>
                    <p className="mt-3 text-sm leading-6 text-teal-600">
                      {lane.description}
                    </p>
                    <div className="mt-4 border-t border-slate-100 pt-3 font-mono text-[0.68rem] leading-5 text-slate-500 uppercase">
                      <p>{lane.publishedRecordCount} verified records</p>
                      {lane.latestPeriod ? (
                        <p>Latest: {lane.latestPeriod}</p>
                      ) : null}
                    </div>
                  </article>
                ))}
              </div>
            ) : (
              <div className="mt-5">
                <DataUnavailable
                  message={
                    evidenceNetwork.error ??
                    'The evidence-status service is unavailable.'
                  }
                />
              </div>
            )}
          </section>

          <section className="mt-10 rounded-2xl bg-teal-900 p-5 text-white sm:p-7">
            <div className="flex flex-wrap items-end justify-between gap-4">
              <div>
                <p className="text-xs font-semibold tracking-[0.18em] text-amber-300 uppercase">
                  Research workspace
                </p>
                <h2
                  className="mt-2 text-2xl font-semibold tracking-tight"
                  style={{ fontFamily: 'Georgia, serif' }}
                >
                  Find the evidence. Then decide.
                </h2>
              </div>
              <BarChart3 className="size-6 text-amber-300" aria-hidden="true" />
            </div>
            <div className="mt-6 rounded-xl bg-white p-1.5 text-slate-950">
              <GaiaTerminalSearch
                jurisdictions={data.allocations}
                periodLabel={data.period.reporting_label}
              />
            </div>
          </section>
        </>
      ) : (
        <div className="mt-10">
          <DataUnavailable
            message={
              overview.error ??
              'No governed published jurisdiction ledger is available for Gaia Terminal.'
            }
          />
        </div>
      )}

      <section className="mt-12 border-t border-teal-900/10 pt-10">
        <p className="text-xs font-semibold tracking-[0.18em] text-teal-900 uppercase">
          Decision workflow
        </p>
        <h2
          className="mt-2 text-2xl font-semibold tracking-tight text-teal-950"
          style={{ fontFamily: 'Georgia, serif' }}
        >
          From a fiscal signal to an evidence-backed action.
        </h2>
        <div className="mt-6 grid gap-4 md:grid-cols-3">
          {workflows.map((workflow, index) => (
            <Link key={workflow.href} href={workflow.href} className="group">
              <Card className="h-full border-teal-900/10 shadow-none transition-colors group-hover:border-teal-700">
                <CardHeader>
                  <p className="font-mono text-xs text-teal-900">
                    0{index + 1}
                  </p>
                  <CardTitle className="pt-3 text-lg">
                    {workflow.title}
                  </CardTitle>
                  <CardDescription className="leading-6">
                    {workflow.description}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <span className="inline-flex items-center gap-1 text-sm font-semibold text-teal-900">
                    Open workflow{' '}
                    <ArrowUpRight className="size-3.5" aria-hidden="true" />
                  </span>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      </section>
    </main>
  )
}
