import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Clock3,
  DatabaseZap,
  History,
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
import { getPendingNationalReviews } from '@/lib/national-review-api'
import { getOagfRevisionCases } from '@/lib/oagf-revision-api'
import { getPendingReviews } from '@/lib/review-api'

export const metadata: Metadata = { title: 'FAAC evidence control' }
export const dynamic = 'force-dynamic'

export default async function EvidenceControlPage() {
  const [oagfResult, nationalResult, revisionsResult] = await Promise.all([
    getPendingReviews(),
    getPendingNationalReviews(),
    getOagfRevisionCases(),
  ])

  const oagf = oagfResult.data ?? []
  const national = nationalResult.data ?? []
  const revisions = revisionsResult.data ?? []

  const oagfBlocked = oagf.filter((item) => item.blocking_count > 0).length
  const oagfApproved = oagf.filter((item) => item.approved).length
  const nationalBlocked = national.filter(
    (item) => item.blocking_count > 0,
  ).length
  const nationalApproved = national.filter((item) => item.approved).length
  const revisionEscalations = revisions.filter(
    (item) => item.status === 'investigation_required',
  ).length
  const serviceError =
    oagfResult.error ?? nationalResult.error ?? revisionsResult.error

  return (
    <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
      <PageHeader
        eyebrow="Governed evidence operations"
        title="FAAC evidence control"
        description="One control surface for jurisdiction evidence, independent national evidence, and official source revisions. Automated collectors prepare evidence; human approval and publication remain separate controlled actions."
      />

      {serviceError ? (
        <Card className="mt-6 border-amber-300 bg-amber-50">
          <CardContent className="flex items-start gap-3 pt-6 text-amber-950">
            <AlertTriangle
              className="mt-0.5 size-5 shrink-0"
              aria-hidden="true"
            />
            <p className="text-sm font-medium">
              One or more review services could not be loaded. {serviceError}
            </p>
          </CardContent>
        </Card>
      ) : null}

      <div className="mt-8 grid gap-5 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <DatabaseZap className="text-primary size-5" aria-hidden="true" />
            <CardTitle className="pt-3">OAGF jurisdiction evidence</CardTitle>
            <CardDescription>
              37-jurisdiction allocation evidence collected from OAGF reports.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <dl className="grid gap-4 text-sm sm:grid-cols-3 lg:grid-cols-1 xl:grid-cols-3">
              <div>
                <dt className="text-muted-foreground">Unpublished</dt>
                <dd className="mt-1 text-2xl font-semibold">{oagf.length}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Approved</dt>
                <dd className="mt-1 text-2xl font-semibold">{oagfApproved}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Blocking</dt>
                <dd className="mt-1 text-2xl font-semibold">{oagfBlocked}</dd>
              </div>
            </dl>
            <Button asChild className="mt-6">
              <Link href="/review/pending">
                Open OAGF queue
                <ArrowRight className="size-4" aria-hidden="true" />
              </Link>
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <ShieldCheck className="text-primary size-5" aria-hidden="true" />
            <CardTitle className="pt-3">National FAAC evidence</CardTitle>
            <CardDescription>
              Independent official national distributions and reconciliation
              evidence.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <dl className="grid gap-4 text-sm sm:grid-cols-3 lg:grid-cols-1 xl:grid-cols-3">
              <div>
                <dt className="text-muted-foreground">Unpublished</dt>
                <dd className="mt-1 text-2xl font-semibold">
                  {national.length}
                </dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Approved</dt>
                <dd className="mt-1 text-2xl font-semibold">
                  {nationalApproved}
                </dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Blocking</dt>
                <dd className="mt-1 text-2xl font-semibold">
                  {nationalBlocked}
                </dd>
              </div>
            </dl>
            <Button asChild className="mt-6">
              <Link href="/review/national">
                Open national queue
                <ArrowRight className="size-4" aria-hidden="true" />
              </Link>
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <History className="text-primary size-5" aria-hidden="true" />
            <CardTitle className="pt-3">Official OAGF revisions</CardTitle>
            <CardDescription>
              Changed historical source bytes detected without overwriting
              published evidence.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <dl className="grid gap-4 text-sm sm:grid-cols-2 lg:grid-cols-1 xl:grid-cols-2">
              <div>
                <dt className="text-muted-foreground">Open cases</dt>
                <dd className="mt-1 text-2xl font-semibold">
                  {revisions.length}
                </dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Escalated</dt>
                <dd className="mt-1 text-2xl font-semibold">
                  {revisionEscalations}
                </dd>
              </div>
            </dl>
            <Button asChild className="mt-6">
              <Link href="/review/oagf-revisions">
                Open revision queue
                <ArrowRight className="size-4" aria-hidden="true" />
              </Link>
            </Button>
          </CardContent>
        </Card>
      </div>

      <div className="mt-8 grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <Clock3 className="text-primary size-5" aria-hidden="true" />
            <CardTitle className="pt-3">Automated intake</CardTitle>
            <CardDescription>
              Scheduled collectors discover and validate evidence before it
              reaches a human queue.
            </CardDescription>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader>
            <CheckCircle2 className="text-primary size-5" aria-hidden="true" />
            <CardTitle className="pt-3">Explicit approval</CardTitle>
            <CardDescription>
              Reviewer identity is selected from active database users at the
              moment of review.
            </CardDescription>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader>
            <ShieldCheck className="text-primary size-5" aria-hidden="true" />
            <CardTitle className="pt-3">Four-eyes publication</CardTitle>
            <CardDescription>
              Publication requires a different active administrator from the
              person who approved the evidence.
            </CardDescription>
          </CardHeader>
        </Card>
      </div>
    </div>
  )
}
