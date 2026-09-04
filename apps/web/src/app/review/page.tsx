import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Clock3,
  DatabaseZap,
  FileBarChart,
  History,
  Landmark,
  ScanSearch,
  ShieldCheck,
} from 'lucide-react'
import type { Metadata } from 'next'
import Link from 'next/link'

import { PageHeader } from '@/components/page-header'
import { getPendingDmoReviews } from '@/lib/dmo-review-api'
import { getPendingNationalReviews } from '@/lib/national-review-api'
import { getPendingIgrReviews } from '@/lib/nbs-igr-review-api'
import { getOagfRevisionCases } from '@/lib/oagf-revision-api'
import { getPendingReviews } from '@/lib/review-api'

export const metadata: Metadata = { title: 'Evidence Review Control Room' }
export const dynamic = 'force-dynamic'

export default async function EvidenceControlPage() {
  const [oagfResult, nationalResult, revisionsResult, dmoResult, igrResult] =
    await Promise.all([
      getPendingReviews(),
      getPendingNationalReviews(),
      getOagfRevisionCases(),
      getPendingDmoReviews(),
      getPendingIgrReviews(),
    ])

  const oagf = oagfResult.data ?? []
  const national = nationalResult.data ?? []
  const revisions = revisionsResult.data ?? []
  const dmo = dmoResult.data ?? []
  const igr = igrResult.data ?? []

  const oagfBlocked = oagf.filter((item) => item.blocking_count > 0).length
  const oagfApproved = oagf.filter((item) => item.approved).length
  const nationalBlocked = national.filter(
    (item) => item.blocking_count > 0,
  ).length
  const nationalApproved = national.filter((item) => item.approved).length
  const dmoApproved = dmo.filter((item) => item.approved).length
  const igrApproved = igr.filter((item) => item.approved).length
  const serviceError =
    oagfResult.error ??
    nationalResult.error ??
    revisionsResult.error ??
    dmoResult.error ??
    igrResult.error

  const totalPending = oagf.length + national.length + dmo.length + igr.length
  const totalApproved =
    oagfApproved + nationalApproved + dmoApproved + igrApproved
  const totalBlocking = oagfBlocked + nationalBlocked

  const queues = [
    {
      href: '/review/pending',
      title: 'OAGF Jurisdiction',
      detail: '37-state allocation evidence from official reports',
      count: oagf.length,
      icon: DatabaseZap,
      status: oagfBlocked > 0 ? `${oagfBlocked} blocking` : 'Queue ready',
    },
    {
      href: '/review/national',
      title: 'National FAAC',
      detail: 'Official distributions and reconciliation evidence',
      count: national.length,
      icon: ShieldCheck,
      status:
        nationalBlocked > 0 ? `${nationalBlocked} blocking` : 'Queue ready',
    },
    {
      href: '/review/dmo',
      title: 'DMO Debt',
      detail: 'State and FCT debt stock and service evidence',
      count: dmo.length,
      icon: Landmark,
      status: 'Governed intake',
    },
    {
      href: '/review/nbs-igr',
      title: 'NBS IGR',
      detail: 'State internally generated revenue evidence',
      count: igr.length,
      icon: FileBarChart,
      status: 'Governed intake',
    },
    {
      href: '/review/oagf-revisions',
      title: 'Source Revisions',
      detail: 'Detected source changes preserved without overwriting history',
      count: revisions.length,
      icon: History,
      status: 'Revision ledger',
    },
  ]

  return (
    <div className="pb-8">
      <section className="border-b border-white/8 bg-[#061d19] text-white">
        <div className="gaia-shell grid gap-12 py-14 lg:grid-cols-[1.05fr_.95fr] lg:items-end lg:py-20">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-emerald-300/15 bg-emerald-300/[0.07] px-3 py-1.5">
              <ScanSearch className="size-3.5 text-emerald-300" />
              <span className="font-mono text-[0.65rem] font-bold tracking-[0.18em] text-emerald-100 uppercase">
                Review / Human control plane
              </span>
            </div>
            <h1 className="mt-6 max-w-[14ch] text-5xl leading-[0.98] font-semibold tracking-[-0.055em] text-balance sm:text-6xl lg:text-7xl">
              Nothing gets published by accident.
            </h1>
            <p className="mt-6 max-w-2xl text-lg leading-8 text-emerald-50/65">
              Gaia&apos;s evidence control room keeps automated intake, human
              verification, explicit approval, revision handling and four-eyes
              publication in one auditable workflow.
            </p>
          </div>

          <div className="gaia-panel-dark p-6 sm:p-7">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="font-mono text-[0.64rem] font-semibold tracking-[0.16em] text-white/40 uppercase">
                  Publication gate
                </p>
                <p className="mt-2 text-xl font-semibold">
                  Evidence operations
                </p>
              </div>
              <div className="flex size-11 items-center justify-center rounded-2xl border border-emerald-300/15 bg-emerald-300/[0.08]">
                <ShieldCheck className="size-5 text-emerald-300" />
              </div>
            </div>

            <div className="mt-7 grid grid-cols-3 divide-x divide-white/10 rounded-2xl border border-white/10 bg-white/[0.035]">
              <div className="p-4">
                <p className="font-mono text-[0.58rem] tracking-[0.14em] text-white/35 uppercase">
                  Pending
                </p>
                <p className="mt-2 font-mono text-2xl font-semibold">
                  {totalPending}
                </p>
              </div>
              <div className="p-4">
                <p className="font-mono text-[0.58rem] tracking-[0.14em] text-white/35 uppercase">
                  Approved
                </p>
                <p className="mt-2 font-mono text-2xl font-semibold text-emerald-200">
                  {totalApproved}
                </p>
              </div>
              <div className="p-4">
                <p className="font-mono text-[0.58rem] tracking-[0.14em] text-white/35 uppercase">
                  Blocking
                </p>
                <p className="mt-2 font-mono text-2xl font-semibold text-amber-200">
                  {totalBlocking}
                </p>
              </div>
            </div>

            <div className="mt-5 flex items-center gap-2 text-xs text-white/45">
              <span className="size-1.5 rounded-full bg-emerald-300" />
              Separate reviewer and publisher roles remain explicit.
            </div>
          </div>
        </div>
      </section>

      <div className="gaia-shell gaia-section">
        {serviceError ? (
          <div className="mb-8 flex items-start gap-3 rounded-2xl border border-red-300/60 bg-red-50/80 p-5 dark:border-red-400/20 dark:bg-red-400/[0.07]">
            <AlertTriangle className="mt-0.5 size-5 shrink-0 text-red-700 dark:text-red-300" />
            <div>
              <p className="font-semibold text-red-900 dark:text-red-100">
                Review service unavailable
              </p>
              <p className="mt-1 text-sm text-red-800/75 dark:text-red-100/60">
                {serviceError}
              </p>
            </div>
          </div>
        ) : null}

        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {[
            {
              label: 'Pending review',
              value: totalPending,
              detail: 'Awaiting human action',
              icon: Clock3,
            },
            {
              label: 'Approved',
              value: totalApproved,
              detail: 'Cleared within review workflow',
              icon: CheckCircle2,
            },
            {
              label: 'Blocking issues',
              value: totalBlocking,
              detail: 'Require investigation before publication',
              icon: AlertTriangle,
            },
            {
              label: 'Open revisions',
              value: revisions.length,
              detail: 'Source changes preserved as cases',
              icon: History,
            },
          ].map((metric) => {
            const Icon = metric.icon
            return (
              <div key={metric.label} className="gaia-panel p-6">
                <div className="flex items-center justify-between">
                  <p className="gaia-data-label">{metric.label}</p>
                  <Icon className="text-primary/55 size-4" />
                </div>
                <p className="gaia-data-value mt-5">{metric.value}</p>
                <p className="text-muted-foreground mt-2 text-xs leading-5">
                  {metric.detail}
                </p>
              </div>
            )
          })}
        </div>

        <section className="mt-10">
          <div className="flex flex-wrap items-end justify-between gap-4">
            <PageHeader
              eyebrow="Operational queues"
              title="Evidence lanes"
              description="Each source family keeps its own review state while sharing the same publication protocol and audit posture."
            />
            <Link
              href="/sources"
              className="text-primary inline-flex items-center gap-1.5 text-sm font-semibold"
            >
              Inspect evidence registry <ArrowRight className="size-4" />
            </Link>
          </div>

          <div className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-5">
            {queues.map((queue) => {
              const Icon = queue.icon
              return (
                <Link
                  key={queue.href}
                  href={queue.href}
                  className="gaia-panel group flex min-h-64 flex-col p-6 transition hover:-translate-y-1"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="border-primary/10 bg-primary/[0.07] flex size-11 items-center justify-center rounded-2xl border">
                      <Icon className="text-primary size-5" />
                    </div>
                    <span className="border-border bg-muted/50 rounded-full border px-2.5 py-1 font-mono text-xs font-semibold">
                      {queue.count}
                    </span>
                  </div>
                  <p className="text-muted-foreground mt-6 font-mono text-[0.6rem] font-semibold tracking-[0.14em] uppercase">
                    {queue.status}
                  </p>
                  <h2 className="mt-2 text-lg font-semibold tracking-tight">
                    {queue.title}
                  </h2>
                  <p className="text-muted-foreground mt-3 text-sm leading-6">
                    {queue.detail}
                  </p>
                  <div className="text-primary mt-auto flex items-center gap-1.5 pt-5 text-sm font-semibold">
                    Open control queue
                    <ArrowRight className="size-4 transition-transform group-hover:translate-x-1" />
                  </div>
                </Link>
              )
            })}
          </div>
        </section>

        <section className="mt-10 overflow-hidden rounded-3xl border border-white/8 bg-[#061d19] text-white shadow-[0_24px_80px_rgba(0,0,0,0.16)]">
          <div className="grid lg:grid-cols-[.72fr_1.28fr]">
            <div className="border-b border-white/10 p-7 lg:border-r lg:border-b-0 lg:p-9">
              <p className="font-mono text-[0.65rem] font-semibold tracking-[0.18em] text-amber-200/60 uppercase">
                Four-eyes protocol
              </p>
              <h2 className="mt-4 text-3xl font-semibold tracking-[-0.035em]">
                The publication path is part of the evidence.
              </h2>
              <p className="mt-4 text-sm leading-7 text-white/55">
                Gaia preserves the operational path from collection through
                human approval and publication so institutional users can
                inspect not just the number, but how it became publishable.
              </p>
            </div>

            <div className="grid md:grid-cols-3">
              {[
                [
                  '01',
                  'Automated collection',
                  'Scheduled collectors discover, parse and validate candidate evidence before human review.',
                ],
                [
                  '02',
                  'Human approval',
                  'A designated reviewer confirms source, period, coverage and blocking findings.',
                ],
                [
                  '03',
                  'Separate publication',
                  'A different administrator publishes approved evidence while the audit trail remains intact.',
                ],
              ].map(([number, title, detail]) => (
                <div
                  key={number}
                  className="border-t border-white/10 p-7 first:border-t-0 md:border-t-0 md:border-l md:first:border-l-0"
                >
                  <p className="font-mono text-sm font-semibold text-amber-300">
                    {number}
                  </p>
                  <h3 className="mt-8 font-semibold">{title}</h3>
                  <p className="mt-3 text-sm leading-6 text-white/50">
                    {detail}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}
