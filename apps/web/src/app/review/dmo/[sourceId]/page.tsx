import { AlertTriangle, ExternalLink, ShieldCheck } from 'lucide-react'
import type { Metadata } from 'next'
import Link from 'next/link'
import { redirect } from 'next/navigation'

import { DataUnavailable } from '@/components/data-unavailable'
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
import {
  approveDmoReview,
  getDmoReviewPacket,
  publishDmoReview,
} from '@/lib/dmo-review-api'
import { formatDate, humanize } from '@/lib/format'
import { getReviewActors } from '@/lib/review-api'

export const metadata: Metadata = { title: 'DMO review packet' }
export const dynamic = 'force-dynamic'

export default async function DmoReviewPacketPage({
  params,
  searchParams,
}: {
  params: Promise<{ sourceId: string }>
  searchParams: Promise<{ error?: string }>
}) {
  const { sourceId } = await params
  const query = await searchParams
  const [result, actorsResult] = await Promise.all([
    getDmoReviewPacket(sourceId),
    getReviewActors(),
  ])
  const packet = result.data
  const actors = actorsResult.data ?? []
  const reviewers = actors.filter(
    (actor) => actor.role === 'reviewer' || actor.role === 'administrator',
  )
  const publishers = actors.filter((actor) => actor.role === 'administrator')

  async function approveAction(formData: FormData) {
    'use server'
    const reviewerId = String(formData.get('reviewer_id') ?? '')
    const attestation = formData.get('attestation') === 'on'
    if (!reviewerId || !attestation) {
      redirect(
        `/review/dmo/${encodeURIComponent(sourceId)}?error=${encodeURIComponent('Choose the actual reviewer and complete the attestation.')}`,
      )
    }
    const action = await approveDmoReview(sourceId, reviewerId)
    if (action.error) {
      redirect(
        `/review/dmo/${encodeURIComponent(sourceId)}?error=${encodeURIComponent(action.error)}`,
      )
    }
    redirect(`/review/dmo/${encodeURIComponent(sourceId)}`)
  }

  async function publishAction(formData: FormData) {
    'use server'
    const publisherId = String(formData.get('publisher_id') ?? '')
    const attestation = formData.get('attestation') === 'on'
    if (!publisherId || !attestation) {
      redirect(
        `/review/dmo/${encodeURIComponent(sourceId)}?error=${encodeURIComponent('Choose a publisher and complete the publication attestation.')}`,
      )
    }
    const action = await publishDmoReview(sourceId, publisherId)
    if (action.error) {
      redirect(
        `/review/dmo/${encodeURIComponent(sourceId)}?error=${encodeURIComponent(action.error)}`,
      )
    }
    redirect('/review/dmo')
  }

  if (!packet) {
    return (
      <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
        <PageHeader
          eyebrow="DMO evidence control"
          title="Review packet unavailable"
          description="Only real, archived DMO debt sources can be opened here."
        />
        <div className="mt-8">
          <DataUnavailable
            message={result.error ?? 'Review packet unavailable.'}
          />
        </div>
        <Button asChild variant="outline" className="mt-5">
          <Link href="/review/dmo">Back to DMO queue</Link>
        </Button>
      </div>
    )
  }

  const complete = packet.covered_states === packet.expected_states
  const canApprove = complete && !packet.approval
  const canPublish = packet.approval !== null && !packet.published

  return (
    <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
      <PageHeader
        eyebrow="DMO evidence control"
        title={`${humanize(packet.debt_kind)} debt · as at ${formatDate(packet.as_of_date)}`}
        description="Review retained DMO debt evidence, approve it explicitly, then publish only through a different active administrator."
      />

      {query.error ? (
        <Card className="mt-6 border-amber-300 bg-amber-50">
          <CardContent className="flex items-start gap-3 pt-6 text-amber-950">
            <AlertTriangle
              className="mt-0.5 size-5 shrink-0"
              aria-hidden="true"
            />
            <p className="text-sm font-medium">{query.error}</p>
          </CardContent>
        </Card>
      ) : null}

      <div className="mt-8 grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
        <Card>
          <CardHeader>
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <CardTitle>Official source</CardTitle>
                <CardDescription className="mt-2">
                  {packet.source.source_organization} ·{' '}
                  {packet.source.original_filename}
                </CardDescription>
              </div>
              <StatusPill tone="neutral">
                Version {packet.source.document_version}
              </StatusPill>
            </div>
          </CardHeader>
          <CardContent>
            <dl className="grid gap-5 text-sm sm:grid-cols-2">
              <div className="sm:col-span-2">
                <dt className="text-muted-foreground">SHA-256</dt>
                <dd className="mt-1 font-mono text-xs break-all">
                  {packet.source.sha256}
                </dd>
              </div>
            </dl>
            {packet.source.source_url ? (
              <a
                href={packet.source.source_url}
                target="_blank"
                rel="noreferrer"
                className="text-primary mt-5 inline-flex items-center gap-1 text-sm font-medium hover:underline"
              >
                Open retained official source
                <ExternalLink className="size-3.5" aria-hidden="true" />
              </a>
            ) : null}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <ShieldCheck className="text-primary size-5" aria-hidden="true" />
            <CardTitle className="pt-3">Control status</CardTitle>
          </CardHeader>
          <CardContent>
            <dl className="grid gap-4 text-sm">
              <div>
                <dt className="text-muted-foreground">Coverage</dt>
                <dd className="mt-1 font-mono font-semibold">
                  {packet.covered_states} / {packet.expected_states}
                </dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Human approval</dt>
                <dd className="mt-1 font-medium">
                  {packet.approval
                    ? `Approved by ${packet.approval.actor_name ?? 'recorded reviewer'}`
                    : 'Awaiting review'}
                </dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Publication</dt>
                <dd className="mt-1 font-medium">
                  {packet.published ? 'Published' : 'Not yet published'}
                </dd>
              </div>
            </dl>
          </CardContent>
        </Card>
      </div>

      <section className="mt-8">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <p className="text-primary font-mono text-xs font-semibold tracking-[0.18em] uppercase">
              Extracted evidence
            </p>
            <h2 className="mt-2 text-2xl font-semibold">
              Jurisdiction debt records
            </h2>
          </div>
          <StatusPill tone={complete ? 'success' : 'neutral'}>
            {complete ? 'Complete coverage' : 'Incomplete coverage'}
          </StatusPill>
        </div>
        <div className="mt-5 overflow-x-auto rounded-lg border">
          <table className="w-full min-w-4xl border-collapse text-left text-sm">
            <thead className="bg-muted/50">
              <tr className="border-border border-b">
                <th className="px-4 py-3 font-medium">Jurisdiction</th>
                <th className="px-4 py-3 font-medium">Debt amount</th>
                <th className="px-4 py-3 font-medium">Currency</th>
                <th className="px-4 py-3 font-medium">Verification</th>
              </tr>
            </thead>
            <tbody>
              {packet.records.map((record) => (
                <tr
                  key={record.state_code}
                  className="border-border border-b last:border-0"
                >
                  <td className="px-4 py-3 font-medium">
                    {record.state_name}{' '}
                    <span className="text-muted-foreground font-mono text-xs">
                      {record.state_code}
                    </span>
                  </td>
                  <td className="px-4 py-3 font-mono text-xs font-semibold">
                    {record.debt_amount}
                  </td>
                  <td className="px-4 py-3 text-xs">{record.currency}</td>
                  <td className="px-4 py-3 text-xs">
                    {humanize(record.verification_status)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="mt-10 grid gap-5 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Reviewer approval</CardTitle>
            <CardDescription>
              Select the person who actually performed the review.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {packet.approval ? (
              <div className="space-y-2 text-sm">
                <StatusPill tone="success">Human verified</StatusPill>
                <p className="font-medium">
                  Approved by{' '}
                  {packet.approval.actor_name ?? 'recorded reviewer'}
                </p>
              </div>
            ) : (
              <form action={approveAction} className="space-y-4">
                <label className="grid gap-1.5 text-sm font-medium">
                  Reviewer
                  <select
                    name="reviewer_id"
                    required
                    className="border-input bg-background rounded-md border px-3 py-2"
                  >
                    <option value="">Choose active reviewer</option>
                    {reviewers.map((actor) => (
                      <option key={actor.id} value={actor.id}>
                        {actor.full_name} · {actor.role}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="flex items-start gap-3 text-sm leading-6">
                  <input
                    type="checkbox"
                    name="attestation"
                    className="mt-1 size-4"
                    disabled={!canApprove}
                  />
                  <span>
                    I verified the retained source and complete jurisdiction
                    coverage.
                  </span>
                </label>
                <Button
                  type="submit"
                  disabled={!canApprove || reviewers.length === 0}
                >
                  Approve evidence
                </Button>
              </form>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Administrator publication</CardTitle>
            <CardDescription>
              Enabled after approval. The API requires a different active
              administrator from the reviewer.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {packet.published ? (
              <div className="space-y-2 text-sm">
                <StatusPill tone="success">Published</StatusPill>
                <p className="text-muted-foreground">
                  This DMO debt evidence is live in the governed ledger.
                </p>
              </div>
            ) : (
              <form action={publishAction} className="space-y-4">
                <label className="grid gap-1.5 text-sm font-medium">
                  Publisher
                  <select
                    name="publisher_id"
                    required
                    disabled={!canPublish}
                    className="border-input bg-background rounded-md border px-3 py-2"
                  >
                    <option value="">Choose active administrator</option>
                    {publishers.map((actor) => (
                      <option key={actor.id} value={actor.id}>
                        {actor.full_name}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="flex items-start gap-3 text-sm leading-6">
                  <input
                    type="checkbox"
                    name="attestation"
                    className="mt-1 size-4"
                    disabled={!canPublish}
                  />
                  <span>
                    I am publishing previously approved DMO debt evidence under
                    four-eyes control.
                  </span>
                </label>
                <Button
                  type="submit"
                  disabled={!canPublish || publishers.length === 0}
                >
                  Publish DMO record
                </Button>
              </form>
            )}
          </CardContent>
        </Card>
      </section>

      <div className="mt-8 flex gap-3">
        <Button asChild variant="outline">
          <Link href="/review/dmo">Back to DMO queue</Link>
        </Button>
        <Button asChild variant="outline">
          <Link href="/review">Evidence control home</Link>
        </Button>
      </div>
    </div>
  )
}
