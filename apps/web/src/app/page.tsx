import {
  ArrowRight,
  BarChart3,
  Building2,
  CheckCircle2,
  Fingerprint,
  Landmark,
  Network,
  ScanSearch,
  ShieldCheck,
  Sparkles,
  TrendingUp,
} from 'lucide-react'
import type { Metadata } from 'next'
import Link from 'next/link'

import { CommercialDecisionChain } from '@/components/commercial-decision-chain'
import { ExpensiveDecisionWorkflows } from '@/components/expensive-decision-workflows'
import { formatNaira } from '@/lib/format'
import { getPublishedAnalytics } from '@/lib/analytics-api'
import { getPublishedOverview } from '@/lib/published-api'

export const metadata: Metadata = {
  title: 'Gaia Fiscal Intelligence | Governed Public-Finance Intelligence',
  description:
    'Institutional public-finance intelligence built on governed, source-linked Nigerian fiscal evidence.',
}

const institutions = [
  {
    title: 'Banks & lenders',
    detail:
      'Preserve the exact fiscal evidence boundary behind credit, risk and exposure decisions.',
    icon: Building2,
  },
  {
    title: 'Investors & DFIs',
    detail:
      'Compare jurisdictions without losing source lineage, revisions or the knowledge available at decision time.',
    icon: TrendingUp,
  },
  {
    title: 'Auditors & governments',
    detail:
      'Move from document collection to reviewable evidence, explicit publication control and verifiable receipts.',
    icon: Landmark,
  },
]

const intelligenceLayers = [
  {
    title: 'Evidence Fabric',
    detail:
      'Official-source documents, claims, review state, revisions and verification artifacts remain linked.',
    icon: Fingerprint,
  },
  {
    title: 'Fiscal Intelligence',
    detail:
      'Governed comparisons, historical views, stress indicators and grounded questions sit above the evidence layer.',
    icon: Network,
  },
  {
    title: 'Decision Rails',
    detail:
      'Decision Rooms, Fiscal Receipts, Watch Contracts and institutional packs preserve the path from evidence to action.',
    icon: ShieldCheck,
  },
]

function compactNaira(value: string | number | null | undefined): string {
  if (value === null || value === undefined) return '—'
  const amount = Number(value)
  if (!Number.isFinite(amount)) return '—'
  if (amount >= 1_000_000_000_000) {
    return `₦${(amount / 1_000_000_000_000).toFixed(2)}T`
  }
  if (amount >= 1_000_000_000) {
    return `₦${(amount / 1_000_000_000).toFixed(2)}B`
  }
  if (amount >= 1_000_000) {
    return `₦${(amount / 1_000_000).toFixed(2)}M`
  }
  return formatNaira(amount)
}

export default async function Home() {
  const [{ data, error }, analyticsResult] = await Promise.all([
    getPublishedOverview(),
    getPublishedAnalytics(),
  ])

  const analytics = analyticsResult.data
  const publishedPeriods = analytics?.months_published ?? 0
  const coverage = data ? `${data.jurisdictions_published}/${data.jurisdictions_expected}` : '—'
  const latestPeriod =
    data?.month_label ?? analytics?.latest_period_label ?? 'No published period'

  return (
    <main className="overflow-hidden">
      <section className="relative border-b border-white/8 bg-[#041a17] px-5 text-white lg:px-8">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_70%_35%,rgba(16,185,129,.16),transparent_36%),radial-gradient(circle_at_15%_80%,rgba(245,158,11,.08),transparent_28%)]" />
        <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(rgba(255,255,255,.025)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,.025)_1px,transparent_1px)] bg-[size:42px_42px] [mask-image:linear-gradient(to_bottom,black,transparent_85%)]" />

        <div className="relative mx-auto grid max-w-7xl gap-16 py-20 lg:grid-cols-[1.02fr_.98fr] lg:items-center lg:py-28 xl:gap-24">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-emerald-300/15 bg-emerald-300/[0.07] px-3 py-1.5">
              <span className="size-1.5 rounded-full bg-emerald-300 shadow-[0_0_18px_rgba(110,231,183,.8)]" />
              <span className="font-mono text-[0.65rem] font-semibold tracking-[0.18em] text-emerald-100/80 uppercase">
                Governed public-finance intelligence
              </span>
            </div>

            <h1 className="mt-7 max-w-[13ch] text-5xl leading-[0.96] font-semibold tracking-[-0.055em] text-balance sm:text-6xl lg:text-7xl xl:text-[5.4rem]">
              Know what changed. Know what evidence supports it. Preserve what
              your institution knew when it made the decision.
            </h1>

            <p className="mt-7 max-w-2xl text-lg leading-8 text-emerald-50/65 sm:text-xl">
              Gaia turns governed Nigerian fiscal evidence into institutional
              intelligence, decision workspaces and verifiable receipts—without
              hiding uncertainty, revisions or missing evidence.
            </p>

            <div className="mt-9 flex flex-wrap gap-3">
              <Link
                href="/terminal"
                className="inline-flex h-12 items-center gap-2 rounded-xl bg-amber-300 px-5 text-sm font-semibold text-slate-950 shadow-[0_12px_35px_rgba(245,158,11,.16)] transition hover:-translate-y-0.5 hover:bg-amber-200"
              >
                Open Fiscal Terminal
                <ArrowRight className="size-4" />
              </Link>
              <Link
                href="/pilot"
                className="inline-flex h-12 items-center gap-2 rounded-xl border border-white/15 bg-white/[0.04] px-5 text-sm font-semibold text-white backdrop-blur transition hover:-translate-y-0.5 hover:bg-white/[0.08]"
              >
                Request Institutional Access
                <Sparkles className="size-4 text-emerald-200" />
              </Link>
            </div>

            <div className="mt-10 grid max-w-2xl grid-cols-2 gap-px overflow-hidden rounded-2xl border border-white/10 bg-white/10 sm:grid-cols-4">
              {[
                ['Capital', data ? compactNaira(data.total_net) : '—'],
                ['Coverage', coverage],
                ['Period', latestPeriod],
                ['Evidence', data ? 'Verified' : 'Review gated'],
              ].map(([label, value]) => (
                <div key={label} className="bg-[#06221d]/90 px-4 py-4">
                  <p className="font-mono text-[0.58rem] tracking-[0.14em] text-emerald-100/35 uppercase">
                    {label}
                  </p>
                  <p className="mt-2 truncate text-sm font-semibold text-white">
                    {value}
                  </p>
                </div>
              ))}
            </div>
          </div>

          <div className="relative mx-auto w-full max-w-xl lg:mx-0 lg:ml-auto">
            <div className="absolute -inset-10 rounded-full bg-emerald-400/10 blur-3xl" />
            <div className="relative overflow-hidden rounded-[2.2rem] border border-emerald-200/15 bg-[#08261f]/90 p-3 shadow-[0_35px_120px_rgba(0,0,0,.38)] backdrop-blur-xl">
              <div className="rounded-[1.75rem] border border-white/10 bg-[#041a17]/85 p-5 sm:p-7">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="font-mono text-[0.62rem] font-semibold tracking-[0.16em] text-emerald-100/45 uppercase">
                      Evidence control plane
                    </p>
                    <p className="mt-2 text-xl font-semibold text-white">
                      Published fiscal signal
                    </p>
                  </div>
                  <div className="flex size-11 items-center justify-center rounded-2xl border border-emerald-200/15 bg-emerald-300/[0.08]">
                    <ScanSearch className="size-5 text-emerald-200" />
                  </div>
                </div>

                <div className="mt-6 grid gap-3 sm:grid-cols-2">
                  <div className="rounded-2xl border border-white/10 bg-white/[0.035] p-4">
                    <p className="text-xs text-emerald-100/45">
                      Published capital signal
                    </p>
                    <p className="mt-2 font-mono text-2xl font-semibold text-white">
                      {data ? compactNaira(data.total_net) : '—'}
                    </p>
                    <p className="mt-2 truncate text-xs text-emerald-100/35">
                      {data?.source_name ?? 'Awaiting governed evidence'}
                    </p>
                  </div>
                  <div className="rounded-2xl border border-white/10 bg-white/[0.035] p-4">
                    <p className="text-xs text-emerald-100/45">
                      Jurisdiction coverage
                    </p>
                    <p className="mt-2 font-mono text-2xl font-semibold text-white">
                      {coverage}
                    </p>
                    <p className="mt-2 text-xs text-emerald-100/35">
                      Published evidence scope
                    </p>
                  </div>
                </div>

                <div className="relative mx-auto my-3 flex size-44 items-center justify-center">
                  <div className="gaia-pulse absolute inset-0 rounded-full border border-emerald-300/20" />
                  <div className="absolute inset-5 rounded-full border border-dashed border-emerald-300/30" />
                  <div className="absolute inset-10 rounded-full border border-emerald-200/20 bg-emerald-300/[0.04]" />
                  <div className="gaia-float relative flex size-20 items-center justify-center rounded-3xl border border-emerald-200/25 bg-emerald-300/10 shadow-[0_0_70px_rgba(52,211,153,.15)] backdrop-blur">
                    <Fingerprint className="size-8 text-emerald-200" />
                  </div>
                  <span className="absolute top-3 left-1/2 -translate-x-1/2 rounded-full border border-white/10 bg-[#06221d] px-2.5 py-1 text-[0.62rem] text-teal-100/70">
                    SOURCE
                  </span>
                  <span className="absolute top-1/2 right-0 -translate-y-1/2 rounded-full border border-white/10 bg-[#06221d] px-2.5 py-1 text-[0.62rem] text-teal-100/70">
                    REVIEW
                  </span>
                  <span className="absolute bottom-3 left-1/2 -translate-x-1/2 rounded-full border border-white/10 bg-[#06221d] px-2.5 py-1 text-[0.62rem] text-teal-100/70">
                    PUBLISH
                  </span>
                  <span className="absolute top-1/2 left-0 -translate-y-1/2 rounded-full border border-white/10 bg-[#06221d] px-2.5 py-1 text-[0.62rem] text-teal-100/70">
                    HASH
                  </span>
                </div>

                <div className="grid grid-cols-3 gap-2 text-center">
                  {[
                    ['Periods', String(publishedPeriods)],
                    ['Pipeline', 'Governed'],
                    ['Output', 'Auditable'],
                  ].map(([label, value]) => (
                    <div
                      key={label}
                      className="rounded-xl border border-white/10 bg-white/[0.04] px-2 py-3"
                    >
                      <p className="text-[0.6rem] tracking-[0.12em] text-teal-100/40 uppercase">
                        {label}
                      </p>
                      <p className="mt-1 text-xs font-semibold text-teal-50">
                        {value}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="gaia-float-delay relative mt-4 ml-auto hidden w-52 rounded-2xl border border-white/10 bg-[#092722]/95 p-4 shadow-2xl backdrop-blur sm:block">
              <p className="text-[0.62rem] font-semibold tracking-[0.14em] text-amber-200/65 uppercase">
                Evidence rule
              </p>
              <p className="mt-2 text-sm leading-5 font-medium text-white">
                No interpolation. No inference. No guesswork.
              </p>
            </div>
          </div>
        </div>
      </section>

      <CommercialDecisionChain />
      <ExpensiveDecisionWorkflows />

      {!data && (
        <section className="border-b border-amber-200/60 bg-amber-50 px-5 py-5 dark:border-amber-300/10 dark:bg-amber-300/[0.06]">
          <div className="mx-auto flex max-w-7xl items-start gap-3 lg:px-3">
            <ShieldCheck className="mt-0.5 size-5 shrink-0 text-amber-700 dark:text-amber-300" />
            <div>
              <p className="font-semibold text-amber-950 dark:text-amber-100">
                Research workspace unavailable
              </p>
              <p className="mt-1 max-w-4xl text-sm leading-6 text-amber-900/70 dark:text-amber-100/65">
                {error ?? 'Published fiscal evidence is temporarily unavailable.'}
                {' '}Gaia Fiscal Intelligence does not synthesize replacement values.
                Evidence appears only after verification and four-eyes
                publication control.
              </p>
            </div>
          </div>
        </section>
      )}

      <section className="border-b border-slate-200/80 bg-white dark:border-white/10 dark:bg-[#071512]">
        <div className="mx-auto grid max-w-7xl grid-cols-2 divide-x divide-y divide-slate-200/80 px-5 sm:grid-cols-4 sm:divide-y-0 lg:px-8 dark:divide-white/10">
          {[
            [
              'Published capital signal',
              data ? compactNaira(data.total_net) : '—',
            ],
            ['Jurisdiction coverage', coverage],
            ['Published periods', String(publishedPeriods)],
            ['Evidence posture', data ? 'Verified' : 'Review gated'],
          ].map(([label, value]) => (
            <div key={label} className="px-4 py-7 sm:px-6 lg:px-8">
              <p className="text-[0.65rem] font-semibold tracking-[0.14em] text-slate-500 uppercase dark:text-emerald-100/45">
                {label}
              </p>
              <p className="mt-2 font-mono text-xl font-semibold tracking-tight text-slate-950 sm:text-2xl dark:text-white">
                {value}
              </p>
            </div>
          ))}
        </div>
      </section>

      <section className="bg-[#f7f8f6] px-5 py-24 lg:px-8 lg:py-32 dark:bg-[#06100f]">
        <div className="mx-auto max-w-7xl">
          <div className="grid gap-12 lg:grid-cols-[.8fr_1.2fr] lg:gap-20">
            <div>
              <p className="text-xs font-bold tracking-[0.18em] text-emerald-700 uppercase dark:text-emerald-300">
                Infrastructure, not a dashboard
              </p>
              <h2 className="mt-5 max-w-[13ch] text-4xl leading-[1.03] font-semibold tracking-[-0.045em] text-slate-950 sm:text-5xl lg:text-6xl dark:text-white">
                From government PDFs to decision infrastructure.
              </h2>
              <p className="mt-6 max-w-xl text-base leading-7 text-slate-600 dark:text-slate-300/75">
                The valuable product is not another chart. It is the governed
                path from primary evidence to an institutional decision—with
                provenance preserved at every step.
              </p>
            </div>

            <div className="grid gap-4">
              {intelligenceLayers.map((layer, index) => {
                const Icon = layer.icon
                return (
                  <article
                    key={layer.title}
                    className="group relative overflow-hidden rounded-[1.7rem] border border-slate-200 bg-white p-6 shadow-[0_20px_70px_rgba(15,23,42,.06)] transition hover:-translate-y-1 hover:border-emerald-200 sm:p-8 dark:border-white/10 dark:bg-white/[0.035] dark:shadow-none dark:hover:border-emerald-300/20"
                  >
                    <div className="absolute top-0 right-0 p-6 font-mono text-5xl font-semibold text-slate-100 transition group-hover:text-emerald-50 sm:text-7xl dark:text-white/[0.035] dark:group-hover:text-emerald-300/[0.06]">
                      0{index + 1}
                    </div>
                    <div className="relative flex gap-5">
                      <div className="border-emerald-200 bg-emerald-50 flex size-11 shrink-0 items-center justify-center rounded-2xl border dark:border-emerald-300/15 dark:bg-emerald-300/[0.07]">
                        <Icon className="size-5 text-emerald-700 dark:text-emerald-200" />
                      </div>
                      <div>
                        <h3 className="text-xl font-semibold tracking-tight text-slate-950 dark:text-white">
                          {layer.title}
                        </h3>
                        <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-600 dark:text-slate-300/70">
                          {layer.detail}
                        </p>
                      </div>
                    </div>
                  </article>
                )
              })}
            </div>
          </div>
        </div>
      </section>

      <section className="border-y border-slate-200/80 bg-white px-5 py-20 lg:px-8 dark:border-white/10 dark:bg-[#071512]">
        <div className="mx-auto max-w-7xl">
          <div className="grid gap-10 lg:grid-cols-[.82fr_1.18fr] lg:items-end">
            <div>
              <p className="text-xs font-bold tracking-[0.18em] text-emerald-700 uppercase dark:text-emerald-300">
                Institutional outcomes
              </p>
              <h2 className="mt-4 max-w-[15ch] text-4xl font-semibold tracking-[-0.04em] text-slate-950 dark:text-white">
                Built for expensive decisions.
              </h2>
              <p className="mt-5 max-w-xl text-base leading-7 text-slate-600 dark:text-slate-300/75">
                The product earns its place when a decision must survive review,
                revision and time—not when another chart is easy to produce.
              </p>
            </div>

            <div className="grid gap-4 md:grid-cols-3">
              {institutions.map((item) => {
                const Icon = item.icon
                return (
                  <article
                    key={item.title}
                    className="rounded-2xl border border-slate-200 bg-[#fafbfa] p-6 dark:border-white/10 dark:bg-white/[0.03]"
                  >
                    <Icon className="size-5 text-emerald-700 dark:text-emerald-300" />
                    <h3 className="mt-5 font-semibold text-slate-950 dark:text-white">
                      {item.title}
                    </h3>
                    <p className="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300/70">
                      {item.detail}
                    </p>
                  </article>
                )
              })}
            </div>
          </div>
        </div>
      </section>

      <section className="bg-[#061d19] px-5 py-20 text-white lg:px-8">
        <div className="mx-auto grid max-w-7xl gap-10 lg:grid-cols-[1fr_auto] lg:items-end">
          <div>
            <p className="font-mono text-[0.65rem] font-semibold tracking-[0.16em] text-emerald-100/45 uppercase">
              Start with governed evidence
            </p>
            <h2 className="mt-4 max-w-3xl text-4xl font-semibold tracking-[-0.04em] sm:text-5xl">
              Build the decision on what can be verified.
            </h2>
            <p className="mt-5 max-w-2xl text-base leading-7 text-emerald-50/60">
              Explore the published evidence layer, ask governed questions, or
              open a conversation about institutional deployment.
            </p>
          </div>
          <div className="flex flex-wrap gap-3 lg:justify-end">
            <Link
              href="/terminal"
              className="inline-flex h-11 items-center gap-2 rounded-xl bg-white px-4 text-sm font-semibold text-slate-950"
            >
              Explore terminal <ArrowRight className="size-4" />
            </Link>
            <Link
              href="/pilot"
              className="inline-flex h-11 items-center gap-2 rounded-xl border border-white/15 px-4 text-sm font-semibold text-white"
            >
              Request pilot <CheckCircle2 className="size-4" />
            </Link>
          </div>
        </div>
      </section>
    </main>
  )
}
