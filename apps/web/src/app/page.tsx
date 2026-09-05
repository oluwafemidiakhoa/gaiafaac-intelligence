import {
  ArrowRight,
  BadgeCheck,
  Building2,
  Database,
  FileCheck2,
  Fingerprint,
  Landmark,
  Search,
  ShieldCheck,
  Sparkles,
  Workflow,
  Zap,
} from 'lucide-react'
import type { Metadata } from 'next'
import Link from 'next/link'

import {
  CommercialDecisionChain,
  ExpensiveDecisionWorkflows,
} from '@/components/commercial-home-sections'
import { getPublishedAnalytics } from '@/lib/analytics-api'
import { formatNaira } from '@/lib/format'
import { getPublishedOverview } from '@/lib/published-api'

export const metadata: Metadata = {
  title: 'Gaia Fiscal Intelligence — Governed fiscal intelligence for Nigeria',
  description:
    'The governed intelligence layer for Nigerian public finance: source-traced evidence, cryptographic provenance, institutional analytics, and auditable AI.',
}

export const dynamic = 'force-dynamic'

function compactNaira(value: string | null) {
  if (!value) return 'Unavailable'
  const amount = Number(value)
  if (!Number.isFinite(amount)) return formatNaira(value)
  if (Math.abs(amount) >= 1_000_000_000_000)
    return `₦${(amount / 1_000_000_000_000).toFixed(2)}T`
  if (Math.abs(amount) >= 1_000_000_000)
    return `₦${(amount / 1_000_000_000).toFixed(2)}B`
  return formatNaira(value)
}

const intelligenceLayers = [
  {
    icon: Fingerprint,
    title: 'Evidence Fabric',
    body: 'Official records are retained, fingerprinted, parsed deterministically, and linked to an immutable provenance trail.',
    detail: 'Source → SHA-256 → extraction → review → publication',
  },
  {
    icon: Sparkles,
    title: 'Fiscal Intelligence',
    body: 'Turn governed records into comparable signals, anomaly context, peer intelligence, and questions institutions can actually act on.',
    detail: 'Published evidence only. No synthetic replacement values.',
  },
  {
    icon: Workflow,
    title: 'Decision Rails',
    body: 'Move from research to repeatable institutional workflows with APIs, decision packets, revision history, and auditable outputs.',
    detail: 'Built for systems, committees, analysts, and reviewers.',
  },
]

const audiences = [
  {
    icon: Building2,
    title: 'Banks & lenders',
    body: 'Assess fiscal capacity, dependence, trajectory, and peer position before capital is committed.',
  },
  {
    icon: Landmark,
    title: 'Investors & DFIs',
    body: 'Interrogate sovereign and subnational fiscal signals from a governed evidence base.',
  },
  {
    icon: FileCheck2,
    title: 'Auditors & governments',
    body: 'Trace every published figure back through the review chain, source bytes, and revision history.',
  },
]

export default async function Home() {
  const [overviewResult, analyticsResult] = await Promise.all([
    getPublishedOverview(),
    getPublishedAnalytics(),
  ])
  const data = overviewResult.data
  const analytics = analyticsResult.data

  const coverage = data ? `${data.covered_states}/${data.expected_states}` : '—'
  const period = data?.period?.reporting_label ?? 'Awaiting publication'
  const publishedPeriods = analytics?.months_published ?? '—'

  return (
    <div className="overflow-hidden bg-[#f7f8f6] text-slate-950 dark:bg-[#06100f] dark:text-white">
      <style>{`
        @keyframes gaia-float {
          0%, 100% { transform: translate3d(0, 0, 0); }
          50% { transform: translate3d(0, -8px, 0); }
        }
        @keyframes gaia-scan {
          0% { transform: translateX(-120%); opacity: 0; }
          15% { opacity: 1; }
          85% { opacity: 1; }
          100% { transform: translateX(220%); opacity: 0; }
        }
        @keyframes gaia-pulse {
          0%, 100% { opacity: .32; transform: scale(.96); }
          50% { opacity: .72; transform: scale(1.04); }
        }
        .gaia-float { animation: gaia-float 7s ease-in-out infinite; }
        .gaia-float-delay { animation: gaia-float 8.5s ease-in-out 1.4s infinite; }
        .gaia-scan { animation: gaia-scan 5.5s ease-in-out infinite; }
        .gaia-pulse { animation: gaia-pulse 4s ease-in-out infinite; }
        @media (prefers-reduced-motion: reduce) {
          .gaia-float, .gaia-float-delay, .gaia-scan, .gaia-pulse { animation: none; }
        }
      `}</style>

      <section className="relative isolate border-b border-teal-950/10 bg-[#041d1a] text-white dark:border-white/10">
        <div
          className="absolute inset-0 -z-20 opacity-40"
          style={{
            backgroundImage:
              'radial-gradient(circle at 15% 15%, rgba(45,212,191,.28), transparent 28%), radial-gradient(circle at 88% 8%, rgba(251,191,36,.18), transparent 25%), radial-gradient(circle at 70% 72%, rgba(16,185,129,.16), transparent 32%)',
          }}
        />
        <div
          className="absolute inset-0 -z-10 opacity-[0.14]"
          style={{
            backgroundImage:
              'linear-gradient(rgba(255,255,255,.16) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.16) 1px, transparent 1px)',
            backgroundSize: '52px 52px',
            maskImage:
              'linear-gradient(to bottom, black 0%, black 65%, transparent 100%)',
          }}
        />

        <div className="mx-auto grid min-h-[740px] max-w-7xl items-center gap-14 px-5 py-20 lg:grid-cols-[1.05fr_.95fr] lg:px-8 lg:py-24">
          <div className="max-w-3xl">
            <div className="mb-7 inline-flex items-center gap-2 rounded-full border border-emerald-300/20 bg-emerald-200/10 px-3 py-1.5 text-xs font-semibold tracking-[0.16em] text-emerald-100 uppercase backdrop-blur">
              <span className="size-1.5 rounded-full bg-emerald-300 shadow-[0_0_18px_rgba(110,231,183,.9)]" />
              Governed fiscal intelligence · Nigeria
            </div>

            <h1 className="max-w-[16ch] text-[clamp(3rem,6vw,6.2rem)] leading-[0.94] font-semibold tracking-[-0.06em] text-balance">
              Know what changed. Know what evidence supports it. Preserve what
              your institution knew when it made the decision.
            </h1>

            <p className="mt-8 max-w-2xl text-lg leading-8 text-teal-50/75 sm:text-xl">
              Gaia turns fragmented Nigerian public-finance records into
              governed evidence, monitoring and decision records for
              institutions allocating capital.
            </p>

            <div className="mt-9 flex flex-wrap gap-3">
              <Link
                href="/terminal"
                className="group inline-flex items-center gap-2 rounded-full bg-amber-300 px-6 py-3.5 text-sm font-bold text-teal-950 shadow-[0_12px_50px_rgba(252,211,77,.2)] transition hover:-translate-y-0.5 hover:bg-amber-200"
              >
                Open Fiscal Terminal
                <ArrowRight className="size-4 transition-transform group-hover:translate-x-0.5" />
              </Link>
              <Link
                href="/decision-rooms"
                className="inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/5 px-6 py-3.5 text-sm font-semibold text-white backdrop-blur transition hover:-translate-y-0.5 hover:bg-white/10"
              >
                Start a Decision Room
              </Link>
              <Link
                href="/pilot"
                className="inline-flex items-center gap-2 rounded-full border border-emerald-300/25 bg-emerald-300/10 px-6 py-3.5 text-sm font-semibold text-emerald-50 transition hover:-translate-y-0.5 hover:bg-emerald-300/15"
              >
                Request Institutional Access
              </Link>
            </div>

            <div className="mt-10 flex flex-wrap gap-x-6 gap-y-3 text-xs font-medium text-teal-50/60">
              <span className="inline-flex items-center gap-2">
                <BadgeCheck className="size-4 text-emerald-300" />
                Source-traced
              </span>
              <span className="inline-flex items-center gap-2">
                <Fingerprint className="size-4 text-emerald-300" />
                SHA-256 fingerprinted
              </span>
              <span className="inline-flex items-center gap-2">
                <ShieldCheck className="size-4 text-emerald-300" />
                Four-eyes publication control
              </span>
            </div>
          </div>

          <div className="relative mx-auto w-full max-w-xl lg:mx-0 lg:justify-self-end">
            <div className="absolute -inset-8 rounded-[3rem] bg-emerald-400/10 blur-3xl" />
            <div className="relative overflow-hidden rounded-[2rem] border border-white/10 bg-white/[0.055] p-5 shadow-[0_40px_120px_rgba(0,0,0,.45)] backdrop-blur-xl sm:p-7">
              <div className="flex items-center justify-between border-b border-white/10 pb-5">
                <div>
                  <p className="text-[0.68rem] font-semibold tracking-[0.18em] text-emerald-200/70 uppercase">
                    Gaia confidence engine
                  </p>
                  <p className="mt-1 text-sm font-medium text-white">
                    National evidence pulse
                  </p>
                </div>
                <div className="inline-flex items-center gap-2 rounded-full border border-emerald-300/20 bg-emerald-300/10 px-3 py-1.5 text-xs font-semibold text-emerald-100">
                  <span className="size-1.5 rounded-full bg-emerald-300" />
                  {data ? 'Verified' : 'Review gated'}
                </div>
              </div>

              <div className="relative mt-6 min-h-[390px] overflow-hidden rounded-[1.5rem] border border-white/10 bg-[#031612]/85 p-5">
                <div
                  className="absolute inset-0 opacity-20"
                  style={{
                    backgroundImage:
                      'linear-gradient(rgba(110,231,183,.22) 1px, transparent 1px), linear-gradient(90deg, rgba(110,231,183,.22) 1px, transparent 1px)',
                    backgroundSize: '34px 34px',
                  }}
                />
                <div className="gaia-scan absolute top-0 bottom-0 left-0 w-20 bg-gradient-to-r from-transparent via-emerald-200/12 to-transparent blur" />

                <div className="relative z-10 flex min-h-[350px] flex-col justify-between">
                  <div className="grid grid-cols-2 gap-3">
                    <div className="rounded-2xl border border-white/10 bg-white/[0.06] p-4">
                      <p className="text-[0.65rem] tracking-[0.14em] text-teal-100/50 uppercase">
                        Latest published total
                      </p>
                      <p className="mt-2 font-mono text-2xl font-semibold tracking-tight text-white">
                        {data ? compactNaira(data.total_net) : '—'}
                      </p>
                      <p className="mt-1 truncate text-xs text-teal-100/45">
                        {period}
                      </p>
                    </div>
                    <div className="rounded-2xl border border-white/10 bg-white/[0.06] p-4">
                      <p className="text-[0.65rem] tracking-[0.14em] text-teal-100/50 uppercase">
                        Jurisdiction coverage
                      </p>
                      <p className="mt-2 font-mono text-2xl font-semibold tracking-tight text-white">
                        {coverage}
                      </p>
                      <p className="mt-1 text-xs text-teal-100/45">
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

              <div className="mt-4 flex flex-wrap items-center justify-between gap-2 rounded-2xl border border-white/10 bg-[#092722]/80 px-4 py-3">
                <p className="text-[0.62rem] font-semibold tracking-[0.14em] text-amber-200/65 uppercase">
                  Evidence rule
                </p>
                <p className="text-xs font-medium text-white/90">
                  No interpolation. No inference. No guesswork.
                </p>
              </div>
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
                Gaia Fiscal Intelligence does not synthesize replacement values.
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
                      <div className="flex size-12 shrink-0 items-center justify-center rounded-2xl bg-emerald-950 text-emerald-200 dark:bg-emerald-300/10 dark:text-emerald-200">
                        <Icon className="size-5" />
                      </div>
                      <div className="max-w-2xl">
                        <h3 className="text-xl font-semibold tracking-tight text-slate-950 dark:text-white">
                          {layer.title}
                        </h3>
                        <p className="mt-3 leading-7 text-slate-600 dark:text-slate-300/70">
                          {layer.body}
                        </p>
                        <p className="mt-4 font-mono text-xs leading-5 text-emerald-700 dark:text-emerald-300/75">
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

      <section className="relative border-y border-teal-950/10 bg-[#e7f4ef] px-5 py-24 lg:px-8 lg:py-32 dark:border-white/10 dark:bg-[#08201b]">
        <div className="mx-auto max-w-7xl">
          <div className="grid items-center gap-14 lg:grid-cols-2 lg:gap-20">
            <div className="relative overflow-hidden rounded-[2rem] border border-teal-950/10 bg-[#031915] p-6 text-white shadow-[0_35px_100px_rgba(4,47,46,.18)] sm:p-8">
              <div className="flex items-center justify-between border-b border-white/10 pb-5">
                <div className="flex items-center gap-3">
                  <div className="flex size-9 items-center justify-center rounded-xl bg-amber-300 text-teal-950">
                    <Sparkles className="size-4" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold">Ask Gaia</p>
                    <p className="text-xs text-teal-100/45">
                      Governed intelligence interface
                    </p>
                  </div>
                </div>
                <span className="rounded-full border border-emerald-300/20 bg-emerald-300/10 px-2.5 py-1 text-[0.62rem] font-semibold text-emerald-200">
                  EVIDENCE BOUND
                </span>
              </div>

              <div className="mt-6 space-y-4">
                <div className="ml-auto max-w-[88%] rounded-2xl rounded-br-md bg-white/10 px-4 py-3 text-sm leading-6 text-teal-50/90">
                  Which jurisdictions show the largest movement from their
                  published baseline—and what evidence supports the conclusion?
                </div>
                <div className="max-w-[92%] rounded-2xl rounded-bl-md border border-white/10 bg-white/[0.055] px-4 py-4">
                  <div className="flex items-center gap-2 text-xs font-semibold text-emerald-200">
                    <BadgeCheck className="size-3.5" />
                    Gaia response policy
                  </div>
                  <p className="mt-3 text-sm leading-6 text-teal-50/75">
                    Answers are constrained to published evidence and return the
                    source trail, publication state, and revision context needed
                    to verify the result.
                  </p>
                  <div className="mt-4 flex flex-wrap gap-2">
                    {['Source IDs', 'Confidence state', 'Revision trail'].map(
                      (chip) => (
                        <span
                          key={chip}
                          className="rounded-full border border-white/10 bg-black/10 px-2.5 py-1 text-[0.65rem] text-teal-100/55"
                        >
                          {chip}
                        </span>
                      ),
                    )}
                  </div>
                </div>
              </div>

              <div className="mt-6 flex items-center gap-2 rounded-xl border border-white/10 bg-black/10 px-3 py-3 text-xs text-teal-100/40">
                <Search className="size-4" />
                Ask a question across governed fiscal evidence…
              </div>
            </div>

            <div>
              <p className="text-xs font-bold tracking-[0.18em] text-emerald-800 uppercase dark:text-emerald-300">
                Auditable AI
              </p>
              <h2 className="mt-5 max-w-[12ch] text-4xl leading-[1.03] font-semibold tracking-[-0.045em] text-teal-950 sm:text-5xl lg:text-6xl dark:text-white">
                AI should show its receipts.
              </h2>
              <p className="mt-6 max-w-xl text-base leading-7 text-teal-950/65 dark:text-teal-50/65">
                Gaia is designed so intelligence never floats free from
                evidence. The answer is useful because the institution can
                inspect what the system used, what was published, and what
                changed.
              </p>
              <div className="mt-8 flex flex-wrap gap-3">
                <Link
                  href="/gaia-analyst"
                  className="group inline-flex items-center gap-2 rounded-full bg-teal-950 px-5 py-3 text-sm font-semibold text-white transition hover:-translate-y-0.5 hover:bg-teal-900 dark:bg-emerald-300 dark:text-teal-950 dark:hover:bg-emerald-200"
                >
                  Ask Gaia
                  <ArrowRight className="size-4 transition-transform group-hover:translate-x-0.5" />
                </Link>
                <Link
                  href="/sources"
                  className="inline-flex items-center gap-2 rounded-full border border-teal-950/15 bg-white/55 px-5 py-3 text-sm font-semibold text-teal-950 backdrop-blur transition hover:bg-white dark:border-white/10 dark:bg-white/[0.04] dark:text-white dark:hover:bg-white/[0.08]"
                >
                  Inspect evidence registry
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="bg-white px-5 py-24 lg:px-8 lg:py-32 dark:bg-[#071512]">
        <div className="mx-auto max-w-7xl">
          <div className="max-w-3xl">
            <p className="text-xs font-bold tracking-[0.18em] text-emerald-700 uppercase dark:text-emerald-300">
              Institutional wedge
            </p>
            <h2 className="mt-5 text-4xl leading-[1.05] font-semibold tracking-[-0.045em] text-slate-950 sm:text-5xl dark:text-white">
              Built for the rooms where capital decisions are made.
            </h2>
          </div>

          <div className="mt-12 grid gap-5 lg:grid-cols-3">
            {audiences.map((audience) => {
              const Icon = audience.icon
              return (
                <article
                  key={audience.title}
                  className="rounded-[1.7rem] border border-slate-200 bg-[#f8faf8] p-7 transition hover:-translate-y-1 hover:border-emerald-200 dark:border-white/10 dark:bg-white/[0.03] dark:hover:border-emerald-300/20"
                >
                  <div className="flex size-11 items-center justify-center rounded-2xl border border-slate-200 bg-white text-emerald-800 shadow-sm dark:border-white/10 dark:bg-white/[0.06] dark:text-emerald-300">
                    <Icon className="size-5" />
                  </div>
                  <h3 className="mt-8 text-xl font-semibold tracking-tight text-slate-950 dark:text-white">
                    {audience.title}
                  </h3>
                  <p className="mt-3 leading-7 text-slate-600 dark:text-slate-300/70">
                    {audience.body}
                  </p>
                </article>
              )
            })}
          </div>

          <div className="mt-5 grid gap-5 md:grid-cols-2">
            <div className="rounded-[1.7rem] border border-slate-200 bg-slate-950 p-7 text-white sm:p-8 dark:border-white/10">
              <Database className="size-6 text-emerald-300" />
              <h3 className="mt-8 text-2xl font-semibold tracking-tight">
                API-native by design
              </h3>
              <p className="mt-3 max-w-xl leading-7 text-slate-300">
                Versioned endpoints let institutional systems consume governed
                evidence, jurisdiction metrics, provenance, and decision outputs
                without rebuilding the evidence layer.
              </p>
              <div className="mt-6 space-y-2 font-mono text-xs text-emerald-200/70">
                <p>GET /api/v1/published/readiness-matrix</p>
                <p>GET /api/v1/jurisdictions/&#123;code&#125;/metrics</p>
                <p>GET /api/v1/evidence/provenance/&#123;gaia_id&#125;</p>
              </div>
            </div>

            <div className="rounded-[1.7rem] border border-slate-200 bg-amber-200 p-7 text-teal-950 sm:p-8 dark:border-amber-200/10 dark:bg-amber-200">
              <Zap className="size-6" />
              <h3 className="mt-8 text-2xl font-semibold tracking-tight">
                A product that can compound
              </h3>
              <p className="mt-3 max-w-xl leading-7 text-teal-950/70">
                The moat is the governed evidence graph: every new period,
                jurisdiction, source, revision, and verified relationship
                increases the value of the intelligence layer built on top of
                it.
              </p>
              <Link
                href="/institutional"
                className="mt-6 inline-flex items-center gap-2 text-sm font-bold"
              >
                Explore institutional workflows
                <ArrowRight className="size-4" />
              </Link>
            </div>
          </div>
        </div>
      </section>

      <section className="relative overflow-hidden bg-[#02120f] px-5 py-24 text-white lg:px-8 lg:py-32">
        <div
          className="absolute inset-0 opacity-50"
          style={{
            backgroundImage:
              'radial-gradient(circle at 22% 30%, rgba(52,211,153,.18), transparent 28%), radial-gradient(circle at 80% 65%, rgba(251,191,36,.12), transparent 30%)',
          }}
        />
        <div className="relative mx-auto grid max-w-7xl gap-10 lg:grid-cols-[1fr_auto] lg:items-end">
          <div>
            <p className="text-xs font-bold tracking-[0.18em] text-emerald-300 uppercase">
              The standard
            </p>
            <h2 className="mt-5 max-w-[13ch] text-5xl leading-[0.98] font-semibold tracking-[-0.055em] sm:text-6xl lg:text-7xl">
              If a number can move capital, it should carry proof.
            </h2>
            <p className="mt-6 max-w-2xl text-lg leading-8 text-teal-50/60">
              Build the next fiscal decision on governed evidence—not a copied
              spreadsheet, an opaque model output, or a number nobody can trace.
            </p>
          </div>

          <div className="flex flex-wrap gap-3 lg:justify-end">
            <Link
              href="/pilot"
              className="group inline-flex items-center gap-2 rounded-full bg-amber-300 px-6 py-3.5 text-sm font-bold text-teal-950 transition hover:-translate-y-0.5 hover:bg-amber-200"
            >
              Start an institutional pilot
              <ArrowRight className="size-4 transition-transform group-hover:translate-x-0.5" />
            </Link>
            <Link
              href="/sources"
              className="inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/5 px-6 py-3.5 text-sm font-semibold text-white transition hover:bg-white/10"
            >
              <ShieldCheck className="size-4" />
              Verify the evidence
            </Link>
          </div>
        </div>
      </section>
    </div>
  )
}