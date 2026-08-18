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
import { StatusPill } from '@/components/status-pill'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
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
      <PageHeader
        eyebrow="OAGF evidence control"
        title="Jurisdiction evidence awaiting human action"
        description="New OAGF evidence lands here after collection, extraction and automated validation. Approval and publication are separate controlled actions."
      />

      <div className="mt-8 grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader>
            <Clock3 className="text-primary size-5" aria-hidden="true" />
            <CardTitle className="pt-3 text-2xl">{reviews.length}</CardTitle>
            <CardDescription>Unpublished packets</CardDescription>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader>
            <CheckCircle2 className="text-primary size-5" aria-hidden="true" />
            <CardTitle className="pt-3 text-2xl">{readyForReview}</CardTitle>
            <CardDescription>Ready for review</CardDescription>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader>
            <ShieldCheck className="text-primary size-5" aria-hidden="true" />
            <CardTitle className="pt-3 text-2xl">{approved}</CardTitle>
            <CardDescription>Approved, awaiting publication</CardDescription>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader>
            <AlertTriangle
              className="size-5 text-amber-700"
              aria-hidden="true"
            />
            <CardTitle className="pt-3 text-2xl">{blocked}</CardTitle>
            <CardDescription>Requiring investigation</CardDescription>
          </CardHeader>
        </Card>
      </div>

      <Card className="bg-muted/30 mt-6">
        <CardHeader>
          <div className="flex items-start gap-3">
            <ShieldCheck
              className="text-primary mt-0.5 size-5"
              aria-hidden="true"
            />
            <div>
              <CardTitle>Review protocol</CardTitle>
              <CardDescription className="mt-2 max-w-3xl leading-6">
                Confirm the official source and reporting period, verify
                complete 37-jurisdiction coverage, investigate validation
                findings, then record the actual reviewer. Publication is
                unlocked only after approval and must be performed by a
                different active administrator.
              </CardDescription>
            </div>
          </div>
        </CardHeader>
      </Card>

      {result.error ? (
        <Card className="mt-8 border-dashed">
          <CardContent className="pt-6">
            <p className="font-medium">Review service unavailable</p>
            <p className="text-muted-foreground mt-2 text-sm">
              {result.error} No review state has been inferred.
            </p>
          </CardContent>
        </Card>
      ) : reviews.length > 0 ? (
        <div className="mt-8 space-y-4">
          {reviews.map((item) => {
            const complete = item.covered_states === item.expected_states
            const hasBlocking = item.blocking_count > 0
            const status = item.approved
              ? 'Approved · publish next'
              : hasBlocking
                ? 'Investigation required'
                : complete
                  ? 'Ready for human review'
                  : 'Incomplete evidence'

            return (
              <Card key={item.run_id}>
                <CardHeader>
                  <div className="flex flex-wrap items-start justify-between gap-4">
                    <div>
                      <CardTitle>{item.reporting_label}</CardTitle>
                      <CardDescription className="mt-2">
                        {item.source_organization} · reporting period{' '}
                        {formatDate(item.revenue_month)}
                      </CardDescription>
                    </div>
                    <StatusPill
                      tone={
                        item.approved || (complete && !hasBlocking)
                          ? 'success'
                          : 'neutral'
                      }
                    >
                      {status}
                    </StatusPill>
                  </div>
                </CardHeader>
                <CardContent>
                  <dl className="grid gap-5 text-sm sm:grid-cols-2 lg:grid-cols-5">
                    <div>
                      <dt className="text-muted-foreground">Coverage</dt>
                      <dd className="mt-1 font-mono font-semibold">
                        {item.covered_states} / {item.expected_states}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-muted-foreground">Findings</dt>
                      <dd className="mt-1 font-semibold">
                        {item.finding_count}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-muted-foreground">Blocking</dt>
                      <dd
                        className={
                          hasBlocking
                            ? 'mt-1 font-semibold text-amber-800'
                            : 'mt-1 font-semibold'
                        }
                      >
                        {item.blocking_count}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-muted-foreground">Pipeline</dt>
                      <dd className="mt-1 font-medium">{item.status}</dd>
                    </div>
                    <div>
                      <dt className="text-muted-foreground">Approval</dt>
                      <dd className="mt-1 font-medium">
                        {item.approved ? 'Human verified' : 'Pending'}
                      </dd>
                    </div>
                  </dl>
                  <div className="border-border mt-5 flex flex-wrap items-center justify-between gap-3 border-t pt-4">
                    <div>
                      <p className="text-muted-foreground text-xs">
                        Queued{' '}
                        {item.created_at
                          ? new Intl.DateTimeFormat('en-NG', {
                              dateStyle: 'medium',
                              timeStyle: 'short',
                              timeZone: 'UTC',
                            }).format(new Date(item.created_at))
                          : 'time unavailable'}
                        {item.created_at ? ' UTC' : ''}
                      </p>
                      <p className="text-muted-foreground mt-1 font-mono text-xs break-all">
                        Run {item.run_id}
                      </p>
                    </div>
                    <Button asChild size="sm">
                      <Link href={`/review/pending/${item.run_id}`}>
                        {item.approved
                          ? 'Open publication packet'
                          : 'Open review packet'}
                        <ArrowRight className="size-4" aria-hidden="true" />
                      </Link>
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      ) : (
        <Card className="mt-8 border-dashed">
          <CardContent className="pt-6">
            <CheckCircle2 className="text-primary size-5" aria-hidden="true" />
            <p className="mt-3 font-medium">OAGF queue clear</p>
            <p className="text-muted-foreground mt-2 max-w-2xl text-sm leading-6">
              There are no unpublished OAGF months awaiting human action. Newly
              collected evidence will appear here automatically.
            </p>
          </CardContent>
        </Card>
      )}

      <Button asChild variant="outline" className="mt-8">
        <Link href="/review">Back to evidence control</Link>
      </Button>
    </div>
  )
}
