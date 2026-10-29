import { ArrowRight, FileCheck2, GitCompareArrows, Search, ShieldCheck } from 'lucide-react'
import type { Metadata } from 'next'
import Link from 'next/link'

import { getPublishedAnalytics } from '@/lib/analytics-api'
import { getPublishedOverview } from '@/lib/published-api'

export const metadata: Metadata = {
  title: 'Gaia Fiscal Intelligence — Investigate Nigerian public finance',
  description:
    'Explore published Nigerian fiscal allocations, compare jurisdictions, inspect evidence and prepare decision-ready research.',
}

export const dynamic = 'force-dynamic'

const researchPaths = [
  {
    href: '/compare',
    title: 'Compare jurisdictions',
    description: 'Examine differences between states using comparable published records.',
    icon: GitCompareArrows,
  },
  {
    href: '/sources',
    title: 'Verify the evidence',
    description: 'Inspect original sources, reporting periods and document fingerprints.',
    icon: ShieldCheck,
  },
  {
    href: '/decision-packets',
    title: 'Prepare a decision report',
    description: 'Turn a jurisdiction investigation into an evidence-backed dossier.',
    icon: FileCheck2,
  },
] as const

export default async function Home() {
  const [overviewResult, analyticsResult] = await Promise.all([
    getPublishedOverview(),
    getPublishedAnalytics(),
  ])
  const overview = overviewResult.data
  const analytics = analyticsResult.data
  const states = overview
    ? [...overview.allocations].sort((a, b) =>
        a.state_name.localeCompare(b.state_name),
      )
    : []

  return (
    <main className="bg-[#f7f9f7] text-slate-950 dark:bg-[#061410] dark:text-white">
      <section className="border-b border-emerald-950/10 bg-[#06231c] text-white">
        <div className="mx-auto max-w-6xl px-5 py-16 lg:px-8 lg:py-24">
          <p className="text-xs font-semibold tracking-[0.18em] text-emerald-300 uppercase">
            Gaia Fiscal Intelligence
          </p>
          <h1 className="mt-6 max-w-3xl text-4xl leading-tight font-semibold tracking-tight text-balance sm:text-5xl lg:text-6xl">
            Understand public finances. Verify every number.
          </h1>
          <p className="mt-6 max-w-2xl text-base leading-7 text-emerald-50/75 sm:text-lg">
            Investigate Nigerian state allocations, compare published evidence,
            and build research you can defend.
          </p>
          <div className="mt-9 flex flex-wrap gap-3">
            <Link
              href="/terminal"
              className="inline-flex items-center gap-2 rounded-lg bg-emerald-300 px-5 py-3 text-sm font-semibold text-emerald-950 transition hover:bg-emerald-200"
            >
              Open research terminal <ArrowRight className="size-4" />
            </Link>
            <Link
              href="/pilot"
              className="inline-flex items-center rounded-lg border border-white/25 px-5 py-3 text-sm font-semibold text-white transition hover:bg-white/10"
            >
              Request institutional access
            </Link>
          </div>
          <div className="mt-12 grid gap-4 rounded-xl border border-white/15 bg-white/5 p-5 sm:grid-cols-3">
            <div>
              <p className="text-xs text-emerald-50/60">Published jurisdiction coverage</p>
              <p className="mt-2 text-2xl font-semibold tabular-nums">
                {overview
                  ? `${overview.covered_states}/${overview.expected_states}`
                  : 'Unavailable'}
              </p>
            </div>
            <div>
              <p className="text-xs text-emerald-50/60">Published periods</p>
              <p className="mt-2 text-2xl font-semibold tabular-nums">
                {analytics?.months_published ?? 'Unavailable'}
              </p>
            </div>
            <div>
              <p className="text-xs text-emerald-50/60">Latest available reporting period</p>
              <p className="mt-2 text-lg font-semibold">
                {overview?.period.reporting_label ?? 'Awaiting verified publication'}
              </p>
            </div>
          </div>
          <p className="mt-3 text-xs text-emerald-50/60">
            Coverage reflects published evidence, not a claim of current-month
            completeness.
          </p>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-5 py-14 lg:px-8 lg:py-18">
        <div className="max-w-2xl">
          <p className="text-xs font-semibold tracking-widest text-emerald-700 uppercase dark:text-emerald-300">
            Start with a jurisdiction
          </p>
          <h2 className="mt-3 text-3xl font-semibold tracking-tight">
            Go from a state to its evidence.
          </h2>
          <p className="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">
            Select a jurisdiction from the latest published ledger. Missing
            evidence is never substituted with estimates.
          </p>
        </div>
        {states.length ? (
          <form
            action="/terminal"
            method="get"
            className="mt-7 flex max-w-2xl flex-col gap-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm sm:flex-row dark:border-white/10 dark:bg-white/5"
          >
            <label className="flex flex-1 flex-col gap-2 text-sm font-medium">
              Jurisdiction
              <select
                name="q"
                required
                defaultValue=""
                className="h-11 rounded-lg border border-slate-300 bg-white px-3 text-slate-950 dark:border-white/20"
              >
                <option value="" disabled>
                  Choose a state or the FCT
                </option>
                {states.map((state) => (
                  <option key={state.state_code} value={state.state_name}>
                    {state.state_name}
                  </option>
                ))}
              </select>
            </label>
            <button
              type="submit"
              className="inline-flex h-11 items-center justify-center gap-2 self-end rounded-lg bg-emerald-800 px-5 text-sm font-semibold text-white hover:bg-emerald-700"
            >
              <Search className="size-4" /> Investigate
            </button>
          </form>
        ) : (
          <div className="mt-7 max-w-2xl rounded-xl border border-amber-300/40 p-5 text-sm">
            Published jurisdiction data is currently unavailable.{' '}
            <Link href="/sources" className="font-semibold underline">
              View the evidence registry
            </Link>
            .
          </div>
        )}
      </section>

      <section className="border-y border-slate-200 bg-white py-14 dark:border-white/10 dark:bg-[#0a1c17]">
        <div className="mx-auto max-w-6xl px-5 lg:px-8">
          <div className="grid gap-7 md:grid-cols-3">
            {researchPaths.map(({ href, title, description, icon: Icon }) => (
              <Link
                key={href}
                href={href}
                className="group rounded-xl border border-slate-200 p-6 transition hover:border-emerald-600 dark:border-white/10"
              >
                <Icon className="size-6 text-emerald-700 dark:text-emerald-300" />
                <h3 className="mt-5 text-lg font-semibold">{title}</h3>
                <p className="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">
                  {description}
                </p>
                <span className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-emerald-700 dark:text-emerald-300">
                  Explore <ArrowRight className="size-4" />
                </span>
              </Link>
            ))}
          </div>
        </div>
      </section>

      <section className="mx-auto flex max-w-6xl flex-col items-start justify-between gap-5 px-5 py-14 lg:flex-row lg:items-center lg:px-8">
        <div>
          <h2 className="text-2xl font-semibold">Research for consequential decisions.</h2>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600 dark:text-slate-300">
            Need a reviewed, source-backed institutional dossier or ongoing monitoring?
            Agree on scope and evidence coverage before commissioning work.
          </p>
        </div>
        <Link
          href="/pilot"
          className="inline-flex shrink-0 items-center gap-2 rounded-lg bg-emerald-800 px-5 py-3 text-sm font-semibold text-white hover:bg-emerald-700"
        >
          Request a pilot <ArrowRight className="size-4" />
        </Link>
      </section>
    </main>
  )
}
