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
import { humanize } from '@/lib/format'
import { getPendingIgrReviews } from '@/lib/nbs-igr-review-api'

export const metadata: Metadata = { title: 'NBS IGR review queue' }
export const dynamic = 'force-dynamic'

export default async function NbsIgrReviewQueuePage() {
  const result = await getPendingIgrReviews()
  const items = result.data ?? []
  const approved = items.filter((item) => item.approved).length
  const readyForReview = items.filter(
    (item) => !item.approved && item.covered_states === item.expected_states,
  ).length

  return (
    <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
      <PageHeader
        eyebrow="NBS evidence control"
        title="State IGR evidence awaiting human action"
        description="Archived NBS IGR sources land here once deterministic extraction completes. Approval and publication into the governed IGR ledger are separate controlled actions."
      />

      <div className="mt-8 grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <Clock3 className="text-primary size-5" aria-hidden="true" />
            <CardTitle className="pt-3 text-2xl">{items.length}</CardTitle>
            <CardDescription>Unpublished sources</CardDescription>
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
      </div>

      {result.error ? (
        <Card className="mt-8 border-dashed">
          <CardContent className="pt-6">
            <p className="font-medium">Review service unavailable</p>
            <p className="text-muted-foreground mt-2 text-sm">
              {result.error} No review state has been inferred.
            </p>
          </CardContent>
        </Card>
      ) : items.length > 0 ? (
        <div className="mt-8 space-y-4">
          {items.map((item) => {
            const complete = item.covered_states === item.expected_states
            const status = item.approved
              ? 'Approved · publish next'
              : complete
                ? 'Ready for human review'
                : 'Incomplete coverage'

            return (
              <Card key={item.source_document_id}>
                <CardHeader>
                  <div className="flex flex-wrap items-start justify-between gap-4">
                    <div>
                      <CardTitle>{item.fiscal_year} annual IGR</CardTitle>
                      <CardDescription className="mt-2">
                        {item.source_organization}
                      </CardDescription>
                    </div>
                    <StatusPill
                      tone={item.approved || complete ? 'success' : 'neutral'}
                    >
                      {status}
                    </StatusPill>
                  </div>
                </CardHeader>
                <CardContent>
                  <dl className="grid gap-5 text-sm sm:grid-cols-3">
                    <div>
                      <dt className="text-muted-foreground">Coverage</dt>
                      <dd className="mt-1 font-mono font-semibold">
                        {item.covered_states} / {item.expected_states}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-muted-foreground">Pipeline</dt>
                      <dd className="mt-1 font-medium">
                        {humanize(item.processing_status)}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-muted-foreground">Approval</dt>
                      <dd className="mt-1 font-medium">
                        {item.approved ? 'Human verified' : 'Pending'}
                      </dd>
                    </div>
                  </dl>
                  <div className="border-border mt-5 flex flex-wrap items-center justify-between gap-3 border-t pt-4">
                    <p className="text-muted-foreground font-mono text-xs break-all">
                      Source {item.source_document_id}
                    </p>
                    <Button asChild size="sm">
                      <Link href={`/review/nbs-igr/${item.source_document_id}`}>
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
            <p className="mt-3 font-medium">NBS IGR queue clear</p>
            <p className="text-muted-foreground mt-2 max-w-2xl text-sm leading-6">
              There are no unpublished NBS IGR sources awaiting human action.
              Newly archived and extracted evidence will appear here
              automatically.
            </p>
          </CardContent>
        </Card>
      )}

      {items.length === 0 && !result.error ? (
        <Card className="mt-6 border-amber-300 bg-amber-50">
          <CardContent className="flex items-start gap-3 pt-6 text-amber-950">
            <AlertTriangle
              className="mt-0.5 size-5 shrink-0"
              aria-hidden="true"
            />
            <p className="text-sm font-medium">
              An empty queue can also mean nothing has been archived and
              extracted yet - check the NBS IGR collector before assuming
              publication is complete.
            </p>
          </CardContent>
        </Card>
      ) : null}

      <Button asChild variant="outline" className="mt-8">
        <Link href="/review">Back to evidence control</Link>
      </Button>
    </div>
  )
}
