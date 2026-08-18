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
  approveReview,
  getReviewActors,
  getReviewPacket,
  publishReview,
  rejectReview,
} from '@/lib/review-api'

export const metadata: Metadata = { title: 'OAGF review packet' }
export const dynamic = 'force-dynamic'

function rawAmount(value: string | null, unit: string) {
  if (value === null) return 'Unavailable'
  return `${value} ${humanize(unit)}`
}

export default async function ReviewPacketPage({
  params,
  searchParams,
}: {
  params: Promise<{ runId: string }>
  searchParams: Promise<{ error?: string }>
}) {
  const { runId } = await params
  const query = await searchParams
  const [result, actorsResult] = await Promise.all([
    getReviewPacket(runId),
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
    const note = String(formData.get('note') ?? '').trim()
    const attestation = formData.get('attestation') === 'on'
    if (!reviewerId || !attestation) {
      redirect(
        `/review/pending/${encodeURIComponent(runId)}?error=${encodeURIComponent('Choose the actual reviewer and complete the attestation.')}`,
      )
    }
    const action = await approveReview(runId, reviewerId, note || undefined)
    if (action.error) {
      redirect(
        `/review/pending/${encodeURIComponent(runId)}?error=${encodeURIComponent(action.error)}`,
      )
    }
    redirect(`/review/pending/${encodeURIComponent(runId)}`)
  }

  async function rejectAction(formData: FormData) {
    'use server'
    const reviewerId = String(formData.get('reviewer_id') ?? '')
    const reason = String(formData.get('reason') ?? '').trim()
    if (!reviewerId || reason.length < 3) {
      redirect(
        `/review/pending/${encodeURIComponent(runId)}?error=${encodeURIComponent('Choose the reviewer and provide a clear rejection reason.')}`,
      )
    }
    const action = await rejectReview(runId, reviewerId, reason)
    if (action.error) {
      redirect(
        `/review/pending/${encodeURIComponent(runId)}?error=${encodeURIComponent(action.error)}`,
      )
    }
    redirect('/review/pending')
  }

  async function publishAction(formData: FormData) {
    'use server'
    const publisherId = String(formData.get('publisher_id') ?? '')
    const attestation = formData.get('attestation') === 'on'
    if (!publisherId || !attestation) {
      redirect(
        `/review/pending/${encodeURIComponent(runId)}?error=${encodeURIComponent('Choose a publisher and complete the publication attestation.')}`,
      )
    }
    const action = await publishReview(runId, publisherId)
    if (action.error) {
      redirect(
        `/review/pending/${encodeURIComponent(runId)}?error=${encodeURIComponent(action.error)}`,
      )
    }
    redirect('/review/pending')
  }

  if (!packet) {
    return (
      <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
        <PageHeader
          eyebrow="OAGF evidence control"
          title="Review packet unavailable"
          description="Only real, unpublished OAGF evidence can be opened here."
        />
        <div className="mt-8">
          <DataUnavailable message={result.error ?? 'Review packet unavailable.'} />
        </div>
        <Button asChild variant="outline" className="mt-5">
          <Link href="/review/pending">Back to OAGF queue</Link>
        </Button>
      </div>
    )
  }

  const complete = packet.covered_states === packet.expected_states
  const canApprove = complete && packet.blocking_count === 0 && !packet.approval
  const canPublish = packet.approval !== null

  return (
    <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
      <PageHeader
        eyebrow="OAGF evidence control"
        title={packet.reporting_label}
        description="Review retained jurisdiction evidence, approve it explicitly, then publish only through a different active administrator."
      />

      {query.error ? (
        <Card className="mt-6 border-amber-300 bg-amber-50">
          <CardContent className="flex items-start gap-3 pt-6 text-amber-950">
            <AlertTriangle className="mt-0.5 size-5 shrink-0" aria-hidden="true" />
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
                  {packet.source.source_organization} · {packet.source.original_filename}
                </CardDescription>
              </div>
              <StatusPill tone="neutral">Version {packet.source.document_version}</StatusPill>
            </div>
          </CardHeader>
          <CardContent>
            <dl className="grid gap-5 text-sm sm:grid-cols-2">
              <div>
                <dt className="text-muted-foreground">Reporting period</dt>
                <dd className="mt-1 font-medium">{formatDate(packet.revenue_month)}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Publication date</dt>
                <dd className="mt-1 font-medium">{formatDate(packet.source.publication_date)}</dd>
              </div>
              <div className="sm:col-span-2">
                <dt className="text-muted-foreground">SHA-256</dt>
                <dd className="mt-1 font-mono text-xs break-all">{packet.source.sha256}</dd>
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
              <div><dt className="text-muted-foreground">Coverage</dt><dd className="mt-1 font-mono font-semibold">{packet.covered_states} / {packet.expected_states}</dd></div>
              <div><dt className="text-muted-foreground">Validation findings</dt><dd className="mt-1 font-semibold">{packet.finding_count}</dd></div>
              <div><dt className="text-muted-foreground">Blocking findings</dt><dd className="mt-1 font-semibold">{packet.blocking_count}</dd></div>
              <div><dt className="text-muted-foreground">Pipeline status</dt><dd className="mt-1 font-medium">{humanize(packet.status)}</dd></div>
              <div><dt className="text-muted-foreground">Human approval</dt><dd className="mt-1 font-medium">{packet.approval ? `Approved by ${packet.approval.actor_name ?? 'recorded reviewer'}` : 'Awaiting review'}</dd></div>
            </dl>
          </CardContent>
        </Card>
      </div>

      <section className="mt-8">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <p className="text-primary font-mono text-xs font-semibold tracking-[0.18em] uppercase">Extracted evidence</p>
            <h2 className="mt-2 text-2xl font-semibold">Jurisdiction reconciliation</h2>
          </div>
          <StatusPill tone={complete ? 'success' : 'neutral'}>{complete ? 'Complete coverage' : 'Incomplete coverage'}</StatusPill>
        </div>
        <div className="mt-5 overflow-x-auto rounded-lg border">
          <table className="w-full min-w-4xl border-collapse text-left text-sm">
            <thead className="bg-muted/50"><tr className="border-border border-b"><th className="px-4 py-3 font-medium">Jurisdiction</th><th className="px-4 py-3 font-medium">Gross</th><th className="px-4 py-3 font-medium">Deductions</th><th className="px-4 py-3 font-medium">Net</th><th className="px-4 py-3 font-medium">Validation</th><th className="px-4 py-3 font-medium">Confidence</th></tr></thead>
            <tbody>
              {packet.allocations.map((allocation) => (
                <tr key={allocation.state_code} className="border-border border-b last:border-0">
                  <td className="px-4 py-3 font-medium">{allocation.state_name} <span className="text-muted-foreground font-mono text-xs">{allocation.state_code}</span></td>
                  <td className="px-4 py-3 font-mono text-xs">{rawAmount(allocation.gross_total, allocation.reported_unit)}</td>
                  <td className="px-4 py-3 font-mono text-xs">{rawAmount(allocation.total_deductions, allocation.reported_unit)}</td>
                  <td className="px-4 py-3 font-mono text-xs font-semibold">{rawAmount(allocation.net_allocation, allocation.reported_unit)}</td>
                  <td className="px-4 py-3 text-xs">{humanize(allocation.verification_status)}</td>
                  <td className="px-4 py-3 font-mono text-xs">{allocation.extraction_confidence ?? 'Not provided'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="mt-8">
        <h2 className="text-2xl font-semibold">Validation findings</h2>
        {packet.findings.length ? (
          <div className="mt-5 space-y-3">
            {packet.findings.map((finding, index) => (
              <Card key={`${finding.rule_code}-${index}`}>
                <CardContent className="grid gap-3 pt-6 md:grid-cols-[9rem_1fr_auto] md:items-start">
                  <span className="font-mono text-xs font-semibold">{finding.rule_code}</span>
                  <div><p className="text-sm font-medium">{finding.message}</p>{finding.details ? <pre className="bg-muted mt-3 overflow-x-auto rounded-md p-3 font-mono text-xs whitespace-pre-wrap">{JSON.stringify(finding.details, null, 2)}</pre> : null}</div>
                  <StatusPill tone="neutral">{finding.severity}</StatusPill>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : <Card className="mt-5 border-dashed"><CardContent className="pt-6 text-sm">Automated validation recorded no findings.</CardContent></Card>}
      </section>

      <section className="mt-10 grid gap-5 lg:grid-cols-3">
        <Card>
          <CardHeader><CardTitle>Reviewer approval</CardTitle><CardDescription>Select the person who actually performed the review.</CardDescription></CardHeader>
          <CardContent>
            {packet.approval ? (
              <div className="space-y-2 text-sm"><StatusPill tone="success">Human verified</StatusPill><p className="font-medium">Approved by {packet.approval.actor_name ?? 'recorded reviewer'}</p></div>
            ) : (
              <form action={approveAction} className="space-y-4">
                <label className="grid gap-1.5 text-sm font-medium">Reviewer<select name="reviewer_id" required className="border-input bg-background rounded-md border px-3 py-2"><option value="">Choose active reviewer</option>{reviewers.map((actor) => <option key={actor.id} value={actor.id}>{actor.full_name} · {actor.role}</option>)}</select></label>
                <label className="grid gap-1.5 text-sm font-medium">Review note (optional)<textarea name="note" rows={3} className="border-input bg-background rounded-md border px-3 py-2" /></label>
                <label className="flex items-start gap-3 text-sm leading-6"><input type="checkbox" name="attestation" className="mt-1 size-4" disabled={!canApprove} /><span>I verified the retained source, reporting period, complete jurisdiction coverage and validation record.</span></label>
                <Button type="submit" disabled={!canApprove || reviewers.length === 0}>Approve evidence</Button>
              </form>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Reject evidence</CardTitle><CardDescription>Preserve unacceptable evidence and its rejection reason in the audit trail.</CardDescription></CardHeader>
          <CardContent>
            <form action={rejectAction} className="space-y-4">
              <label className="grid gap-1.5 text-sm font-medium">Reviewer<select name="reviewer_id" required className="border-input bg-background rounded-md border px-3 py-2"><option value="">Choose active reviewer</option>{reviewers.map((actor) => <option key={actor.id} value={actor.id}>{actor.full_name}</option>)}</select></label>
              <label className="grid gap-1.5 text-sm font-medium">Rejection reason<textarea name="reason" rows={4} required minLength={3} className="border-input bg-background rounded-md border px-3 py-2" /></label>
              <Button type="submit" variant="outline" disabled={packet.approval !== null}>Reject and preserve evidence</Button>
            </form>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Administrator publication</CardTitle><CardDescription>Enabled after approval. The API requires a different active administrator from the reviewer.</CardDescription></CardHeader>
          <CardContent>
            <form action={publishAction} className="space-y-4">
              <label className="grid gap-1.5 text-sm font-medium">Publisher<select name="publisher_id" required disabled={!canPublish} className="border-input bg-background rounded-md border px-3 py-2"><option value="">Choose active administrator</option>{publishers.map((actor) => <option key={actor.id} value={actor.id}>{actor.full_name}</option>)}</select></label>
              <label className="flex items-start gap-3 text-sm leading-6"><input type="checkbox" name="attestation" className="mt-1 size-4" disabled={!canPublish} /><span>I am publishing previously approved OAGF evidence under four-eyes control.</span></label>
              <Button type="submit" disabled={!canPublish || publishers.length === 0}>Publish OAGF record</Button>
            </form>
          </CardContent>
        </Card>
      </section>

      <div className="mt-8 flex gap-3"><Button asChild variant="outline"><Link href="/review/pending">Back to OAGF queue</Link></Button><Button asChild variant="outline"><Link href="/review">Evidence control home</Link></Button></div>
    </div>
  )
}
