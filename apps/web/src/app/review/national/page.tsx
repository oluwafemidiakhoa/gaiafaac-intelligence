import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
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
import { getPendingNationalReviews } from '@/lib/national-review-api'

export const metadata: Metadata = { title: 'National FAAC review queue' }
export const dynamic = 'force-dynamic'

export default async function NationalReviewQueuePage() {
  const result = await getPendingNationalReviews()
  const reviews = result.data ?? []
  const blocked = reviews.filter((item) => item.blocking_count > 0).length
  const approved = reviews.filter((item) => item.approved).length

  return (
    <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
      <PageHeader
        eyebrow="National evidence control"
        title="National FAAC evidence awaiting human action"
        description="Official national releases are discovered, retained, extracted and reconciled automatically. Human approval and publication remain separate controlled actions."
      />

      <div className="mt-8 grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <ShieldCheck className="text-primary size-5" aria-hidden="true" />
            <CardTitle className="pt-3 text-2xl">{reviews.length}</CardTitle>
            <CardDescription>Unpublished national packets</CardDescription>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader>
            <CheckCircle2 className="text-primary size-5" aria-hidden="true" />
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
            <CardDescription>Packets with blocking findings</CardDescription>
          </CardHeader>
        </Card>
      </div>

      {result.error ? (
        <Card className="mt-8 border-dashed">
          <CardContent className="pt-6 text-sm">{result.error}</CardContent>
        </Card>
      ) : reviews.length ? (
        <div className="mt-8 space-y-4">
          {reviews.map((item) => (
            <Card key={item.run_id}>
              <CardHeader>
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div>
                    <CardTitle>{item.reporting_label}</CardTitle>
                    <CardDescription className="mt-2">
                      {item.source_organization} · disbursed{' '}
                      {formatDate(item.disbursement_month)}
                      {item.allocation_period_month
                        ? ` · revenue ${formatDate(item.allocation_period_month)}`
                        : ''}
                    </CardDescription>
                  </div>
                  <StatusPill
                    tone={
                      item.blocking_count > 0
                        ? 'neutral'
                        : item.approved
                          ? 'success'
                          : 'neutral'
                    }
                  >
                    {item.blocking_count > 0
                      ? 'Investigation required'
                      : item.approved
                        ? 'Ready to publish'
                        : 'Ready for review'}
                  </StatusPill>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4 text-sm sm:grid-cols-3">
                  <div>
                    <p className="text-muted-foreground">Findings</p>
                    <p className="mt-1 font-semibold">{item.finding_count}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Blocking</p>
                    <p className="mt-1 font-semibold">{item.blocking_count}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Verification</p>
                    <p className="mt-1 font-medium">
                      {item.verification_status}
                    </p>
                  </div>
                </div>
                <div className="border-border mt-5 flex justify-end border-t pt-4">
                  <Button asChild size="sm">
                    <Link href={`/review/national/${item.run_id}`}>
                      Open national packet
                      <ArrowRight className="size-4" aria-hidden="true" />
                    </Link>
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <Card className="mt-8 border-dashed">
          <CardContent className="pt-6 text-sm">
            No unpublished national evidence is awaiting human action.
          </CardContent>
        </Card>
      )}
    </div>
  )
}
