import {
  ArrowUpRight,
  BarChart3,
  FileCheck2,
  Landmark,
  Search,
  ShieldCheck,
  Sparkles,
} from 'lucide-react'
import type { Metadata } from 'next'
import Link from 'next/link'

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
  title: 'Gaia Terminal',
  description:
    'Evidence-led public-finance intelligence for Nigeria: source-linked allocation, revenue and debt research for institutional decisions.',
}
export const dynamic = 'force-dynamic'

const workflows = [
  {
    href: '/gaia-analyst',
    title: 'Ask Gaia',
    description:
      'Interrogate governed fiscal evidence and inspect the source trail.',
    icon: Sparkles,
  },
  {
    href: '/fiscal-watch',
    title: 'Fiscal Watch',
    description: 'Monitor governed changes that need institutional attention.',
    icon: Search,
  },
  {
    href: '/decision-packets',
    title: 'Decision Packets',
    description:
      'Turn verified evidence into a review-ready institutional brief.',
    icon: FileCheck2,
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
    <main className="pb-8">
      <section className="relative overflow-hidden border-b border-white/8 bg-[#041915] text-white">
        <div
          className="absolute inset-0 opacity-[0.12]"
          style={{
            backgroundImage:
              'linear-gradient(rgba(110,231,183,.35) 1px, transparent 1px), linear-gradient(90deg, rgba(110,231,183,.35) 1px, transparent 1px)',
            backgroundSize: '42px 42px',
          }}
        />
        <div className="gaia-shell relative grid gap-12 py-14 lg:grid-cols-[1.08fr_.92fr] lg:items-center lg:py-20">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-emerald-300/15 bg-emerald-300/[0.07] px-3 py-1.5">
              <span className="size-1.5 rounded-full bg-emerald-300 shadow-[0_0_12px_rgba(110,231,183,.85)]" />
              <span className="font-mono text-[0.65rem] font-bold tracking-[0.18em] text-emerald-100 uppercase">
                Terminal / Evidence online
              </span>
            </div>
            <h1 className="mt-6 max-w-[12ch] text-5xl leading-[0.95] font-semibold tracking-[-0.06em] text-balance sm:text-6xl lg:text-7xl">
              One command center for Nigerian fiscal evidence.
            </h1>
            <p className="mt-6 max-w-2xl text-lg leading-8 text-emerald-50/65">
              Search the governed ledger, inspect source coverage, ask Gaia, and
              move from a fiscal signal to a review-ready decision without
              losing provenance.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link
                href="/gaia-analyst"
                className="inline-flex items-center gap-2 rounded-full bg-amber-300 px-5 py-3 text-sm font-bold text-teal-950 transition hover:-translate-y-0.5 hover:bg-amber-200"
              >
                <Sparkles className="size-4" /> Ask Gaia
              </Link>
              <Link
                href="/sources"
                className="inline-flex items-center gap-2 rounded-full border border-white/12 bg-white/[0.04] px-5 py-3 text-sm font-semibold text-white transition hover:bg-white/[0.08]"
              >
                <ShieldCheck className="size-4" /> Inspect evidence
              </Link>
            </div>
          </div>

          <div className="gaia-panel-dark relative overflow-hidden p-6 sm:p-7">
            <div className="absolute top-0 right-0 size-48 rounded-full bg-emerald-300/10 blur-3xl" />
            <div className="relative flex items-start justify-between gap-4">
              <div>
                <p className="font-mono text-[0.62rem] font-semibold tracking-[0.16em] text-emerald-200/45 uppercase">
                  Governed ledger
                </p>
                <h2 className="mt-2 text-xl font-semibold">
                  OAGF / FAAC allocation
                </h2>
              </div>
              <ShieldCheck className="size-6 text-amber-300" />
            </div>
            <div className="relative mt-7 grid grid-cols-2 gap-3">
              <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-4">
                <p className="font-mono text-[0.58rem] tracking-[0.14em] text-white/35 uppercase">
                  Coverage
                </p>
                <p className="mt-2 font-mono text-2xl font-semibold">
                  {data
                    ? `${data.covered_states}/${data.expected_states}`
                    : '—'}
                </p>
              </div>
              <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-4">
                <p className="font-mono text-[0.58rem] tracking-[0.14em] text-white/35 uppercase">
                  Published total
                </p>
                <p className="mt-2 font-mono text-2xl font-semibold">
                  {data ? compactNaira(data.total_net) : '—'}
                </p>
              </div>
            </div>
            <div className="relative mt-3 rounded-2xl border border-white/10 bg-black/10 p-4">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="font-mono text-[0.58rem] tracking-[0.14em] text-white/35 uppercase">
                    Publication state
                  </p>
                  <p className="mt-2 text-sm font-semibold text-emerald-200">
                    {data
                      ? 'Source-linked and published'
                      : 'Awaiting governed publication'}
                  </p>
                </div>
                <FileCheck2 className="size-5 text-emerald-300" />
              </div>
            </div>
          </div>
        </div>
      </section>

      <div className="gaia-shell gaia-section">
        {data ? (
          <>
            <section className="grid gap-4 md:grid-cols-3">
              <div className="gaia-panel p-6">
                <p className="gaia-data-label">Latest verified allocation</p>
                <p className="gaia-data-value mt-4">
                  {formatDate(data.period.revenue_month)}
                </p>
                <p className="text-muted-foreground mt-2 text-sm leading-6">
                  {data.period.reporting_label}
                </p>
              </div>
              <div className="gaia-panel p-6">
                <p className="gaia-data-label">State ledger total</p>
                <p className="gaia-data-value mt-4">
                  {compactNaira(data.total_net)}
                </p>
                <p className="text-muted-foreground mt-2 text-sm leading-6">
                  Published state and FCT net allocations
                </p>
              </div>
              <div className="gaia-panel p-6">
                <p className="gaia-data-label">Evidence state</p>
                <div className="mt-4 flex items-center gap-2">
                  <FileCheck2 className="text-primary size-5" />
                  <p className="text-xl font-semibold tracking-tight">
                    Source-linked
                  </p>
                </div>
                <Link
                  href="/sources"
                  className="text-primary mt-3 inline-flex items-center gap-1.5 text-sm font-semibold"
                >
                  Verify fingerprint <ArrowUpRight className="size-3.5" />
                </Link>
              </div>
            </section>

            <section className="mt-8 overflow-hidden rounded-3xl border border-white/8 bg-[#061d19] p-5 text-white shadow-[0_24px_80px_rgba(0,0,0,.15)] sm:p-7">
              <div className="flex flex-wrap items-end justify-between gap-4">
                <div>
                  <p className="font-mono text-[0.64rem] font-semibold tracking-[0.18em] text-amber-200/55 uppercase">
                    Research command bar
                  </p>
                  <h2 className="mt-2 text-2xl font-semibold tracking-[-0.035em]">
                    Find the evidence. Then decide.
                  </h2>
                </div>
                <BarChart3 className="size-6 text-amber-300" />
              </div>
              <div className="mt-6 rounded-2xl bg-white p-1.5 text-slate-950 shadow-inner">
                <GaiaTerminalSearch
                  jurisdictions={data.allocations}
                  periodLabel={data.period.reporting_label}
                />
              </div>
            </section>

            <section className="mt-10">
              <div className="flex flex-wrap items-end justify-between gap-4">
                <div>
                  <p className="gaia-kicker">Evidence network</p>
                  <h2 className="mt-3 text-3xl font-semibold tracking-[-0.04em]">
                    A fiscal picture built source by source.
                  </h2>
                </div>
                <p className="text-muted-foreground max-w-md text-sm leading-6">
                  If Gaia cannot verify a source lane, it remains unavailable
                  instead of being inferred.
                </p>
              </div>

              {evidenceLanes ? (
                <div className="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
                  {evidenceLanes.map((lane) => (
                    <article
                      key={lane.authority}
                      className="gaia-panel group p-5"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <div className="bg-primary/[0.07] flex size-9 items-center justify-center rounded-xl">
                          <Landmark className="text-primary size-4" />
                        </div>
                        <StatusPill
                          tone={lane.state === 'Live' ? 'success' : 'neutral'}
                        >
                          {lane.state}
                        </StatusPill>
                      </div>
                      <p className="mt-5 font-semibold tracking-tight">
                        {lane.authority}
                      </p>
                      <p className="text-primary mt-1 text-sm font-medium">
                        {lane.label}
                      </p>
                      <p className="text-muted-foreground mt-3 text-sm leading-6">
                        {lane.description}
                      </p>
                      <div className="border-border text-muted-foreground mt-5 border-t pt-3 font-mono text-[0.66rem] leading-5 uppercase">
                        <p>{lane.publishedRecordCount} verified records</p>
                        {lane.latestPeriod ? (
                          <p>Latest: {lane.latestPeriod}</p>
                        ) : null}
                      </div>
                    </article>
                  ))}
                </div>
              ) : (
                <div className="mt-6">
                  <DataUnavailable
                    message={
                      evidenceNetwork.error ??
                      'The evidence-status service is unavailable.'
                    }
                  />
                </div>
              )}
            </section>
          </>
        ) : (
          <DataUnavailable
            message={
              overview.error ??
              'No governed published jurisdiction ledger is available for Gaia Terminal.'
            }
          />
        )}

        <section className="mt-12">
          <div className="flex items-end justify-between gap-4">
            <div>
              <p className="gaia-kicker">Decision workflow</p>
              <h2 className="mt-3 text-3xl font-semibold tracking-[-0.04em]">
                From fiscal signal to evidence-backed action.
              </h2>
            </div>
          </div>
          <div className="mt-6 grid gap-4 md:grid-cols-3">
            {workflows.map((workflow, index) => {
              const Icon = workflow.icon
              return (
                <Link
                  key={workflow.href}
                  href={workflow.href}
                  className="group"
                >
                  <Card className="h-full transition group-hover:-translate-y-1">
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <div className="bg-primary/[0.07] flex size-10 items-center justify-center rounded-xl">
                          <Icon className="text-primary size-5" />
                        </div>
                        <p className="text-muted-foreground font-mono text-xs">
                          0{index + 1}
                        </p>
                      </div>
                      <CardTitle className="pt-5 text-lg">
                        {workflow.title}
                      </CardTitle>
                      <CardDescription>{workflow.description}</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <span className="text-primary inline-flex items-center gap-1.5 text-sm font-semibold">
                        Open workflow{' '}
                        <ArrowUpRight className="size-3.5 transition-transform group-hover:translate-x-1" />
                      </span>
                    </CardContent>
                  </Card>
                </Link>
              )
            })}
          </div>
        </section>
      </div>
    </main>
  )
}
