import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Clock3,
  ShieldCheck,
} from 'lucide-react'
import type { Metadata } from 'next'
import Link from 'next/link'

import { PageHeader } from '@/components/page-header'
import { Button } from '@/components/ui/button'
import { formatDate } from '@/lib/format'
import { getPendingReviews } from '@/lib/review-api'

export const metadata: Metadata = { title: 'OAGF review queue' }
export const dynamic = 'force-dynamic'

export default async function PendingReviewPage() {
  const result = await getPendingReviews()
  const reviews = result.data ?? []
  const blocked = reviews.filter((item) => item.blocking_count > 0).length
  const approved = reviews.filter((item) => item.approved).length
  const readyForReview = reviews.filter(
    (item) =>
      !item.approved &&
      item.blocking_count === 0 &&
      item.covered_states === item.expected_states,
  ).length

  return (
    <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
      <div style={{ fontFamily: 'Georgia, serif' }}>
        <PageHeader
          eyebrow="OAGF evidence control"
          title="Review Queue: OAGF Jurisdiction Evidence"
          description="New allocation evidence lands here after automated collection and validation. Human reviewers verify sources, coverage, and findings. Approval unlocks publication, which requires a different administrator."
        />
      </div>

      <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-lg border border-teal-200 bg-gradient-to-br from-teal-50 to-white p-5">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium tracking-wide text-teal-700 uppercase">
                Unpublished
              </p>
              <p className="mt-2 text-3xl font-bold text-teal-950">
                {reviews.length}
              </p>
            </div>
            <Clock3 className="size-8 text-teal-300" aria-hidden="true" />
          </div>
        </div>
        <div className="rounded-lg border border-blue-200 bg-gradient-to-br from-blue-50 to-white p-5">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium tracking-wide text-blue-700 uppercase">
                Ready to Review
              </p>
              <p className="mt-2 text-3xl font-bold text-blue-950">
                {readyForReview}
              </p>
            </div>
            <CheckCircle2 className="size-8 text-blue-300" aria-hidden="true" />
          </div>
        </div>
        <div className="rounded-lg border border-emerald-200 bg-gradient-to-br from-emerald-50 to-white p-5">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium tracking-wide text-emerald-700 uppercase">
                Approved
              </p>
              <p className="mt-2 text-3xl font-bold text-emerald-950">
                {approved}
              </p>
            </div>
            <ShieldCheck
              className="size-8 text-emerald-300"
              aria-hidden="true"
            />
          </div>
        </div>
        <div className="rounded-lg border border-amber-200 bg-gradient-to-br from-amber-50 to-white p-5">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium tracking-wide text-amber-700 uppercase">
                Blocking Issues
              </p>
              <p className="mt-2 text-3xl font-bold text-amber-950">
                {blocked}
              </p>
            </div>
            <AlertTriangle
              className="size-8 text-amber-300"
              aria-hidden="true"
            />
          </div>
        </div>
      </div>

      <div className="mt-8 rounded-lg border border-slate-200 bg-slate-50 p-5">
        <h3 className="flex items-center gap-2 font-semibold text-slate-950">
          <ShieldCheck className="size-5 text-teal-700" />
          Review Checklist
        </h3>
        <ol className="mt-4 space-y-2 text-sm text-slate-700">
          <li>✓ Confirm official source and reporting period</li>
          <li>✓ Verify complete 37-jurisdiction coverage</li>
          <li>✓ Review automated validation findings and blocking items</li>
          <li>✓ Record reviewer identity and approval time</li>
          <li>✓ Publication unlocked (must be performed by different admin)</li>
        </ol>
      </div>

      {result.error ? (
        <div className="mt-8 rounded-lg border border-red-300 bg-red-50 p-4">
          <p className="font-semibold text-red-900">
            Review service unavailable
          </p>
          <p className="mt-2 text-sm text-red-800">{result.error}</p>
        </div>
      ) : reviews.length > 0 ? (
        <div className="mt-8 space-y-4">
          {reviews.map((item) => {
            const complete = item.covered_states === item.expected_states
            const hasBlocking = item.blocking_count > 0
            const statusColor = item.approved
              ? 'emerald'
              : hasBlocking
                ? 'amber'
                : complete
                  ? 'teal'
                  : 'slate'

            return (
              <div
                key={item.run_id}
                className="rounded-lg border border-slate-200 bg-white p-6 transition-shadow hover:shadow-md"
              >
                <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3">
                      <h3 className="text-lg font-semibold text-slate-950">
                        {item.reporting_label}
                      </h3>
                      <span
                        className={`rounded-full px-2 py-1 text-xs font-bold text-white ${
                          statusColor === 'emerald'
                            ? 'bg-emerald-600'
                            : statusColor === 'amber'
                              ? 'bg-amber-600'
                              : statusColor === 'teal'
                                ? 'bg-teal-600'
                                : 'bg-slate-600'
                        }`}
                      >
                        {item.approved
                          ? 'Approved'
                          : hasBlocking
                            ? 'Blocked'
                            : complete
                              ? 'Ready'
                              : 'Incomplete'}
                      </span>
                    </div>
                    <p className="mt-1 text-sm text-slate-600">
                      {item.source_organization} •{' '}
                      {formatDate(item.revenue_month)}
                    </p>
                  </div>
                  <Button asChild>
                    <Link href={`/review/pending/${item.run_id}`}>
                      {item.approved ? 'Publish' : 'Review'}{' '}
                      <ArrowRight className="size-4" />
                    </Link>
                  </Button>
                </div>

                <div className="mt-4 grid gap-4 border-t border-slate-200 pt-4 text-sm sm:grid-cols-5">
                  <div>
                    <p className="text-xs font-medium tracking-wide text-slate-600 uppercase">
                      Coverage
                    </p>
                    <p className="mt-1 font-mono font-bold text-slate-950">
                      {item.covered_states}/{item.expected_states}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs font-medium tracking-wide text-slate-600 uppercase">
                      Findings
                    </p>
                    <p className="mt-1 font-bold text-slate-950">
                      {item.finding_count}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs font-medium tracking-wide text-slate-600 uppercase">
                      Blocking
                    </p>
                    <p
                      className={`mt-1 font-bold ${hasBlocking ? 'text-amber-700' : 'text-slate-950'}`}
                    >
                      {item.blocking_count}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs font-medium tracking-wide text-slate-600 uppercase">
                      Status
                    </p>
                    <p className="mt-1 font-medium text-slate-950">
                      {item.status}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs font-medium tracking-wide text-slate-600 uppercase">
                      Approval
                    </p>
                    <p className="mt-1 font-medium text-slate-950">
                      {item.approved ? 'Verified' : 'Pending'}
                    </p>
                  </div>
                </div>

                <p className="mt-3 text-xs text-slate-500">
                  Queued{' '}
                  {item.created_at
                    ? new Intl.DateTimeFormat('en-NG', {
                        dateStyle: 'medium',
                        timeStyle: 'short',
                        timeZone: 'UTC',
                      }).format(new Date(item.created_at))
                    : 'time unavailable'}{' '}
                  • Run {item.run_id}
                </p>
              </div>
            )
          })}
        </div>
      ) : (
        <div className="mt-8 rounded-lg border-2 border-dashed border-emerald-300 bg-emerald-50 p-8 text-center">
          <CheckCircle2 className="mx-auto size-8 text-emerald-600" />
          <p className="mt-3 font-semibold text-emerald-900">
            OAGF Queue Clear
          </p>
          <p className="mt-2 text-sm text-emerald-700">
            No unpublished evidence awaiting action. New evidence will appear
            automatically.
          </p>
        </div>
      )}

      <Button asChild variant="outline" className="mt-8">
        <Link href="/review">← Back to Evidence Control</Link>
      </Button>
    </div>
  )
}
