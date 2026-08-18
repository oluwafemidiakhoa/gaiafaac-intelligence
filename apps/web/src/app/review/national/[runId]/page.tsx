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
import { formatDate, humanize } from '@/lib/format'
import {
  approveNationalReview,
  getNationalActors,
  getNationalReviewPacket,
  publishNationalReview,
} from '@/lib/national-review-api'

export const metadata: Metadata = { title: 'National FAAC review packet' }
export const dynamic = 'force-dynamic'

function rawAmount(value: string | null) {
  return value === null ? 'Unavailable' : `NGN ${value}`
}

export default async function NationalReviewPacketPage({
  params,
  searchParams,
}: {
  params: Promise<{ runId: string }>
  searchParams: Promise<{ error?: string }>
}) {
  const { runId } = await params
  const query = await searchParams
  const [packetResult, actorsResult] = await Promise.all([
    getNationalReviewPacket(runId),
    getNationalActors(),
  ])
  const packet = packetResult.data
  const actors = actorsResult.data ?? []
  const reviewers = actors.filter(
    (actor) => actor.role === 'reviewer' || actor.role === 'administrator',
  )
  const publishers = actors.filter((actor) => actor.role === 'administrator')

  async function approveAction(formData: FormData) {
    'use server'
    const reviewerId = String(formData.get('reviewer_id') ?? '')
    const note = String(formData.get('note') ?? '').trim()
    const attestation = formData.get('attestation') === 'on'
    if (!reviewerId || !attestation) {
      redirect(
        `/review/national/${encodeURIComponent(runId)}?error=${encodeURIComponent('Choose a reviewer and complete the attestation.')}`,
      )
    }
    const action = await approveNationalReview(
      runId,
      reviewerId,
      note || undefined,
    )
    if (action.error) {
      redirect(
        `/review/national/${encodeURIComponent(runId)}?error=${encodeURIComponent(action.error)}`,
      )
    }
    redirect(`/review/national/${encodeURIComponent(runId)}`)
  }

  async function publishAction(formData: FormData) {
    'use server'
    const publisherId = String(formData.get('publisher_id') ?? '')
    const attestation = formData.get('attestation') === 'on'
    if (!publisherId || !attestation) {
      redirect(
        `/review/national/${encodeURIComponent(runId)}?error=${encodeURIComponent('Choose a publisher and complete the publication attestation.')}`,
      )
    }
    const action = await publishNationalReview(runId, publisherId)
    if (action.error) {
      redirect(
        `/review/national/${encodeURIComponent(runId)}?error=${encodeURIComponent(action.error)}`,
      )
    }
    redirect('/review/national')
  }

  if (!packet) {
    return (
      <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
        <PageHeader
          eyebrow="National evidence control"
          title="National review packet unavailable"
          description="The requested national evidence packet could not be loaded."
        />
        <div className="mt-8">
          <DataUnavailable
            message={packetResult.error ?? 'Review packet unavailable.'}
          />
        </div>
        <Button asChild variant="outline" className="mt-5">
          <Link href="/review/national">Back to national queue</Link>
        </Button>
      </div>
    )
  }

  const canApprove = packet.blocking_count === 0 && !packet.approval
  const canPublish = packet.approval !== null && !packet.published

  return (
    <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
      <PageHeader
        eyebrow="National evidence control"
        title={packet.reporting_label}
        description="Verify the retained official claims and deterministic reconciliation. Approval never publishes; publication requires a different active administrator."
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

      <div className="mt-8 grid gap-5 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Official national source</CardTitle>
            <CardDescription>
              {packet.source.source_organization}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <dl className="grid gap-4 text-sm sm:grid-cols-2">
              <div>
                <dt className="text-muted-foreground">Disbursement month</dt>
                <dd className="mt-1 font-medium">
                  {formatDate(packet.disbursement_month)}
                </dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Revenue period</dt>
                <dd className="mt-1 font-medium">
                  {formatDate(packet.allocation_period_month)}
                </dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Authority</dt>
                <dd className="mt-1 font-medium">
                  {humanize(packet.source.source_authority ?? 'unavailable')}
                </dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Canonical source</dt>
                <dd className="mt-1 font-medium">
                  {humanize(
                    packet.source.canonical_source_status ?? 'unavailable',
                  )}
                </dd>
              </div>
              <div className="sm:col-span-2">
                <dt className="text-muted-foreground">SHA-256</dt>
                <dd className="mt-1 font-mono text-xs break-all">
                  {packet.source.sha256}
                </dd>
              </div>
            </dl>
            {packet.source.source_url ? (
              <a
                className="text-primary mt-5 inline-flex items-center gap-1 text-sm font-medium hover:underline"
                href={packet.source.source_url}
                target="_blank"
                rel="noreferrer"
              >
                Open official source
                <ExternalLink className="size-3.5" aria-hidden="true" />
              </a>
            ) : null}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <ShieldCheck className="text-primary size-5" aria-hidden="true" />
            <CardTitle className="pt-3">Deterministic reconciliation</CardTitle>
            <CardDescription>{packet.reconciliation.note}</CardDescription>
          </CardHeader>
          <CardContent>
            <dl className="grid gap-4 text-sm sm:grid-cols-2">
              <div>
                <dt className="text-muted-foreground">Status</dt>
                <dd className="mt-1 font-semibold">
                  {humanize(packet.reconciliation.status)}
                </dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Blocking findings</dt>
                <dd className="mt-1 font-semibold">{packet.blocking_count}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Component total</dt>
                <dd className="mt-1 font-mono text-xs">
                  {rawAmount(packet.reconciliation.component_total)}
                </dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Variance</dt>
                <dd className="mt-1 font-mono text-xs">
                  {rawAmount(packet.reconciliation.variance)}
                </dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Tolerance</dt>
                <dd className="mt-1 font-mono text-xs">
                  {rawAmount(packet.reconciliation.tolerance)}
                </dd>
              </div>
              <div>
                <dt className="text-muted-foreground">States scope</dt>
                <dd className="mt-1 font-medium">
                  {humanize(packet.states_scope ?? 'not_declared')}
                </dd>
              </div>
            </dl>
          </CardContent>
        </Card>
      </div>

      <section className="mt-8">
        <p className="text-primary font-mono text-xs font-semibold tracking-[0.18em] uppercase">
          Observed claims
        </p>
        <h2 className="mt-2 text-2xl font-semibold">National distribution</h2>
        <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          {[
            ['Total distributable', packet.amounts.net_distributable_amount],
            ['Federal', packet.amounts.federal_amount],
            ['States', packet.amounts.states_amount],
            ['Local governments', packet.amounts.local_governments_amount],
            ['13% derivation', packet.amounts.derivation_amount],
          ].map(([label, value]) => (
            <Card key={label}>
              <CardHeader>
                <CardDescription>{label}</CardDescription>
                <CardTitle className="font-mono text-base">
                  {rawAmount(value)}
                </CardTitle>
              </CardHeader>
            </Card>
          ))}
        </div>
      </section>

      <section className="mt-8">
        <h2 className="text-2xl font-semibold">Validation findings</h2>
        {packet.findings.length ? (
          <div className="mt-5 space-y-3">
            {packet.findings.map((finding, index) => (
              <Card key={`${finding.rule_code}-${index}`}>
                <CardContent className="grid gap-3 pt-6 md:grid-cols-[12rem_1fr_auto]">
                  <span className="font-mono text-xs font-semibold">
                    {finding.rule_code}
                  </span>
                  <p className="text-sm">{finding.message}</p>
                  <StatusPill tone="neutral">{finding.severity}</StatusPill>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <Card className="mt-5 border-dashed">
            <CardContent className="pt-6 text-sm">
              No validation findings.
            </CardContent>
          </Card>
        )}
      </section>

      <section className="mt-10 grid gap-5 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Reviewer approval</CardTitle>
            <CardDescription>
              Select the human who actually reviewed this evidence. Reviewer
              identity is loaded from active database users, not deployment
              configuration.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {packet.approval ? (
              <div className="space-y-2 text-sm">
                <StatusPill tone="success">Human verified</StatusPill>
                <p className="font-medium">
                  Approved by{' '}
                  {packet.approval.actor_name ??
                    packet.approval.actor_user_id ??
                    'recorded reviewer'}
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
                <label className="grid gap-1.5 text-sm font-medium">
                  Review note (optional)
                  <textarea
                    name="note"
                    rows={3}
                    className="border-input bg-background rounded-md border px-3 py-2"
                  />
                </label>
                <label className="flex items-start gap-3 text-sm leading-6">
                  <input
                    type="checkbox"
                    name="attestation"
                    className="mt-1 size-4"
                    disabled={!canApprove}
                  />
                  <span>
                    I verified the retained official source and the extracted
                    national claims.
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
              Publication is enabled only after approval. The API enforces that
              the publisher is a different active administrator from the
              reviewer.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form action={publishAction} className="space-y-4">
              <label className="grid gap-1.5 text-sm font-medium">
                Publisher
                <select
                  name="publisher_id"
                  required
                  className="border-input bg-background rounded-md border px-3 py-2"
                  disabled={!canPublish}
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
                  I am publishing previously approved national evidence under
                  four-eyes control.
                </span>
              </label>
              <Button
                type="submit"
                disabled={!canPublish || publishers.length === 0}
              >
                Publish national record
              </Button>
            </form>
          </CardContent>
        </Card>
      </section>

      <div className="mt-8">
        <Button asChild variant="outline">
          <Link href="/review/national">Back to national queue</Link>
        </Button>
      </div>
    </div>
  )
}
