import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Clock3,
  DatabaseZap,
  FileBarChart,
  History,
  Landmark,
  ShieldCheck,
} from 'lucide-react'
import type { Metadata } from 'next'
import Link from 'next/link'

import { PageHeader } from '@/components/page-header'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { getPendingDmoReviews } from '@/lib/dmo-review-api'
import { getPendingNationalReviews } from '@/lib/national-review-api'
import { getPendingIgrReviews } from '@/lib/nbs-igr-review-api'
import { getOagfRevisionCases } from '@/lib/oagf-revision-api'
import { getPendingReviews } from '@/lib/review-api'

export const metadata: Metadata = { title: 'FAAC evidence control' }
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
  const revisionEscalations = revisions.filter(
    (item) => item.status === 'investigation_required',
  ).length
  const dmoApproved = dmo.filter((item) => item.approved).length
  const igrApproved = igr.filter((item) => item.approved).length
  const serviceError =
    oagfResult.error ??
    nationalResult.error ??
    revisionsResult.error ??
    dmoResult.error ??
    igrResult.error

  const totalPending = oagf.length + national.length + dmo.length + igr.length
  const totalApproved = oagfApproved + nationalApproved + dmoApproved + igrApproved
  const totalBlocking = oagfBlocked + nationalBlocked

  return (
    <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
      <div style={{ fontFamily: 'Georgia, serif' }}>
        <PageHeader
          eyebrow="Governed evidence operations"
          title="Evidence Review & Approval Center"
          description="Institutional approval workflow for FAAC allocation, national evidence, debt records, and revenue data. Automated intake, human review, explicit approval, and four-eyes publication—all tracked and auditable."
        />
      </div>

      {serviceError ? (
        <div className="mt-6 rounded-lg border border-red-300 bg-red-50 p-4">
          <div className="flex items-start gap-3">
            <AlertTriangle className="mt-0.5 size-5 shrink-0 text-red-900" aria-hidden="true" />
            <div>
              <p className="font-semibold text-red-900">Service unavailable</p>
              <p className="text-red-800 mt-1 text-sm">{serviceError}</p>
            </div>
          </div>
        </div>
      ) : null}

      <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-lg border border-teal-200 bg-gradient-to-br from-teal-50 to-white p-5">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-teal-700">Pending Review</p>
              <p className="mt-2 text-3xl font-bold text-teal-950">{totalPending}</p>
            </div>
            <Clock3 className="size-8 text-teal-300" aria-hidden="true" />
          </div>
          <p className="text-teal-700 mt-3 text-xs">Awaiting human action</p>
        </div>

        <div className="rounded-lg border border-emerald-200 bg-gradient-to-br from-emerald-50 to-white p-5">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-emerald-700">Approved</p>
              <p className="mt-2 text-3xl font-bold text-emerald-950">{totalApproved}</p>
            </div>
            <CheckCircle2 className="size-8 text-emerald-300" aria-hidden="true" />
          </div>
          <p className="text-emerald-700 mt-3 text-xs">Ready to publish</p>
        </div>

        <div className="rounded-lg border border-amber-200 bg-gradient-to-br from-amber-50 to-white p-5">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-amber-700">Blocking Issues</p>
              <p className="mt-2 text-3xl font-bold text-amber-950">{totalBlocking}</p>
            </div>
            <AlertTriangle className="size-8 text-amber-300" aria-hidden="true" />
          </div>
          <p className="text-amber-700 mt-3 text-xs">Require investigation</p>
        </div>

        <div className="rounded-lg border border-slate-200 bg-gradient-to-br from-slate-50 to-white p-5">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-slate-700">Open Revisions</p>
              <p className="mt-2 text-3xl font-bold text-slate-950">{revisions.length}</p>
            </div>
            <History className="size-8 text-slate-300" aria-hidden="true" />
          </div>
          <p className="text-slate-700 mt-3 text-xs">Source change cases</p>
        </div>
      </div>

      <div className="mt-10">
        <h2 className="mb-5 text-lg font-semibold text-teal-950" style={{ fontFamily: 'Georgia, serif' }}>Review Queues</h2>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
          <Link
            href="/review/pending"
            className="group rounded-lg border-2 border-teal-300 bg-white p-6 transition-all hover:border-teal-600 hover:shadow-lg"
          >
            <div className="flex items-start justify-between">
              <div className="flex size-10 items-center justify-center rounded-lg bg-teal-100">
                <DatabaseZap className="size-5 text-teal-900" aria-hidden="true" />
              </div>
              <span className="rounded-full bg-teal-100 px-2 py-1 text-xs font-bold text-teal-900">{oagf.length}</span>
            </div>
            <h3 className="mt-4 font-semibold text-teal-950">OAGF Jurisdiction</h3>
            <p className="text-muted-foreground mt-2 text-sm">37-state allocation evidence from official reports</p>
            <div className="text-primary mt-4 inline-flex items-center gap-1 text-sm font-medium">
              Review queue <ArrowRight className="size-3.5" aria-hidden="true" />
            </div>
          </Link>

          <Link
            href="/review/national"
            className="group rounded-lg border-2 border-teal-300 bg-white p-6 transition-all hover:border-teal-600 hover:shadow-lg"
          >
            <div className="flex items-start justify-between">
              <div className="flex size-10 items-center justify-center rounded-lg bg-teal-100">
                <ShieldCheck className="size-5 text-teal-900" aria-hidden="true" />
              </div>
              <span className="rounded-full bg-teal-100 px-2 py-1 text-xs font-bold text-teal-900">{national.length}</span>
            </div>
            <h3 className="mt-4 font-semibold text-teal-950">National FAAC</h3>
            <p className="text-muted-foreground mt-2 text-sm">Official distributions and reconciliation evidence</p>
            <div className="text-primary mt-4 inline-flex items-center gap-1 text-sm font-medium">
              Review queue <ArrowRight className="size-3.5" aria-hidden="true" />
            </div>
          </Link>

          <Link
            href="/review/dmo"
            className="group rounded-lg border-2 border-teal-300 bg-white p-6 transition-all hover:border-teal-600 hover:shadow-lg"
          >
            <div className="flex items-start justify-between">
              <div className="flex size-10 items-center justify-center rounded-lg bg-teal-100">
                <Landmark className="size-5 text-teal-900" aria-hidden="true" />
              </div>
              <span className="rounded-full bg-teal-100 px-2 py-1 text-xs font-bold text-teal-900">{dmo.length}</span>
            </div>
            <h3 className="mt-4 font-semibold text-teal-950">DMO Debt</h3>
            <p className="text-muted-foreground mt-2 text-sm">State and FCT debt stock and service evidence</p>
            <div className="text-primary mt-4 inline-flex items-center gap-1 text-sm font-medium">
              Review queue <ArrowRight className="size-3.5" aria-hidden="true" />
            </div>
          </Link>

          <Link
            href="/review/nbs-igr"
            className="group rounded-lg border-2 border-teal-300 bg-white p-6 transition-all hover:border-teal-600 hover:shadow-lg"
          >
            <div className="flex items-start justify-between">
              <div className="flex size-10 items-center justify-center rounded-lg bg-teal-100">
                <FileBarChart className="size-5 text-teal-900" aria-hidden="true" />
              </div>
              <span className="rounded-full bg-teal-100 px-2 py-1 text-xs font-bold text-teal-900">{igr.length}</span>
            </div>
            <h3 className="mt-4 font-semibold text-teal-950">NBS IGR</h3>
            <p className="text-muted-foreground mt-2 text-sm">State internally generated revenue evidence</p>
            <div className="text-primary mt-4 inline-flex items-center gap-1 text-sm font-medium">
              Review queue <ArrowRight className="size-3.5" aria-hidden="true" />
            </div>
          </Link>

          <Link
            href="/review/oagf-revisions"
            className="group rounded-lg border-2 border-teal-300 bg-white p-6 transition-all hover:border-teal-600 hover:shadow-lg"
          >
            <div className="flex items-start justify-between">
              <div className="flex size-10 items-center justify-center rounded-lg bg-teal-100">
                <History className="size-5 text-teal-900" aria-hidden="true" />
              </div>
              <span className="rounded-full bg-teal-100 px-2 py-1 text-xs font-bold text-teal-900">{revisions.length}</span>
            </div>
            <h3 className="mt-4 font-semibold text-teal-950">Revisions</h3>
            <p className="text-muted-foreground mt-2 text-sm">Source changes detected without overwriting</p>
            <div className="text-primary mt-4 inline-flex items-center gap-1 text-sm font-medium">
              Review queue <ArrowRight className="size-3.5" aria-hidden="true" />
            </div>
          </Link>
        </div>
      </div>

      <div className="mt-10 rounded-lg bg-slate-950 p-6 text-white lg:p-8">
        <h3 className="text-lg font-semibold" style={{ fontFamily: 'Georgia, serif' }}>Approval Protocol</h3>
        <div className="mt-5 grid gap-5 md:grid-cols-3">
          <div className="flex gap-4">
            <div className="flex size-9 shrink-0 items-center justify-center rounded-full bg-amber-400 font-bold text-slate-950">1</div>
            <div>
              <p className="font-medium">Automated Collection</p>
              <p className="text-slate-300 mt-1 text-sm">Scheduled evidence collectors discover and validate data before human review</p>
            </div>
          </div>
          <div className="flex gap-4">
            <div className="flex size-9 shrink-0 items-center justify-center rounded-full bg-amber-400 font-bold text-slate-950">2</div>
            <div>
              <p className="font-medium">Human Approval</p>
              <p className="text-slate-300 mt-1 text-sm">Designated reviewer confirms source, period, coverage, and investigates findings</p>
            </div>
          </div>
          <div className="flex gap-4">
            <div className="flex size-9 shrink-0 items-center justify-center rounded-full bg-amber-400 font-bold text-slate-950">3</div>
            <div>
              <p className="font-medium">Four-Eyes Publication</p>
              <p className="text-slate-300 mt-1 text-sm">Different administrator publishes approved evidence—all actions remain auditable</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
