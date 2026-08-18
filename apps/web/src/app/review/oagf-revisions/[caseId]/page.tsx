import { AlertTriangle, ExternalLink, History, ShieldCheck } from 'lucide-react'
import type { Metadata } from 'next'
import Link from 'next/link'
import { redirect } from 'next/navigation'

import { DataUnavailable } from '@/components/data-unavailable'
import { PageHeader } from '@/components/page-header'
import { StatusPill } from '@/components/status-pill'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { formatDate } from '@/lib/format'
import { getOagfRevisionCase, resolveOagfRevision } from '@/lib/oagf-revision-api'
import { getReviewActors } from '@/lib/review-api'

export const metadata: Metadata = { title: 'OAGF revision packet' }
export const dynamic = 'force-dynamic'

export default async function OagfRevisionPacketPage({
  params,
  searchParams,
}: {
  params: Promise<{ caseId: string }>
  searchParams: Promise<{ error?: string }>
}) {
  const { caseId } = await params
  const query = await searchParams
  const [result, actorsResult] = await Promise.all([
    getOagfRevisionCase(caseId),
    getReviewActors(),
  ])
  const item = result.data
  const reviewers = (actorsResult.data ?? []).filter(
    (actor) => actor.role === 'reviewer' || actor.role === 'administrator',
  )

  async function resolveAction(formData: FormData) {
    'use server'
    const reviewerId = String(formData.get('reviewer_id') ?? '')
    const resolutionCode = String(formData.get('resolution_code') ?? '')
    const note = String(formData.get('note') ?? '').trim()
    const attestation = formData.get('attestation') === 'on'
    if (!reviewerId || !resolutionCode || note.length < 3 || !attestation) {
      redirect(
        `/review/oagf-revisions/${encodeURIComponent(caseId)}?error=${encodeURIComponent('Choose the actual reviewer, classify the revision, add a note, and complete the attestation.')}`,
      )
    }
    const action = await resolveOagfRevision(caseId, reviewerId, resolutionCode, note)
    if (action.error) {
      redirect(
        `/review/oagf-revisions/${encodeURIComponent(caseId)}?error=${encodeURIComponent(action.error)}`,
      )
    }
    redirect('/review/oagf-revisions')
  }

  if (!item) {
    return (
      <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
        <PageHeader eyebrow="OAGF source integrity" title="Revision packet unavailable" description="Only retained OAGF revision cases can be opened here." />
        <div className="mt-8"><DataUnavailable message={result.error ?? 'Revision packet unavailable.'} /></div>
        <Button asChild variant="outline" className="mt-5"><Link href="/review/oagf-revisions">Back to revisions</Link></Button>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
      <PageHeader
        eyebrow="OAGF source integrity"
        title={item.reporting_label ?? item.title}
        description="Compare the immutable source versions and classify the official revision. This action never changes already-published fiscal data automatically."
      />

      {query.error ? (
        <Card className="mt-6 border-amber-300 bg-amber-50"><CardContent className="flex items-start gap-3 pt-6 text-amber-950"><AlertTriangle className="mt-0.5 size-5 shrink-0" /><p className="text-sm font-medium">{query.error}</p></CardContent></Card>
      ) : null}

      <div className="mt-8 grid gap-5 lg:grid-cols-2">
        <Card>
          <CardHeader><History className="text-primary size-5" /><CardTitle className="pt-3">Version lineage</CardTitle><CardDescription>Official OAGF bytes changed for the same publication identity.</CardDescription></CardHeader>
          <CardContent>
            <dl className="grid gap-5 text-sm sm:grid-cols-2">
              <div><dt className="text-muted-foreground">Reporting period</dt><dd className="mt-1 font-medium">{item.revenue_month ? formatDate(item.revenue_month) : 'Not linked to a governed period'}</dd></div>
              <div><dt className="text-muted-foreground">Detected</dt><dd className="mt-1 font-medium">{new Intl.DateTimeFormat('en-NG', { dateStyle: 'medium', timeStyle: 'short', timeZone: 'UTC' }).format(new Date(item.detected_at))} UTC</dd></div>
              <div><dt className="text-muted-foreground">Previous</dt><dd className="mt-1 font-mono font-semibold">Version {item.previous_version}</dd></div>
              <div><dt className="text-muted-foreground">Current</dt><dd className="mt-1 font-mono font-semibold">Version {item.current_version}</dd></div>
            </dl>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><ShieldCheck className="text-primary size-5" /><CardTitle className="pt-3">Control status</CardTitle></CardHeader>
          <CardContent className="space-y-3 text-sm"><StatusPill tone={item.status === 'pending_review' ? 'neutral' : 'warning'}>{item.status.replaceAll('_', ' ')}</StatusPill><p className="text-muted-foreground">Published allocations and fiscal proofs remain untouched until a separate governed replacement workflow is explicitly performed.</p></CardContent>
        </Card>
      </div>

      <div className="mt-8 grid gap-5 lg:grid-cols-2">
        <Card>
          <CardHeader><CardTitle>Previous official version</CardTitle><CardDescription className="font-mono break-all">SHA-256 {item.previous_sha256}</CardDescription></CardHeader>
          <CardContent className="flex flex-wrap gap-3"><Button asChild variant="outline"><a href={`/review/oagf-revisions/${item.id}/source/previous`} target="_blank">Open retained bytes<ExternalLink className="size-4" /></a></Button><Button asChild variant="ghost"><a href={item.previous_source_url} target="_blank" rel="noreferrer">Official URL<ExternalLink className="size-4" /></a></Button></CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Current official version</CardTitle><CardDescription className="font-mono break-all">SHA-256 {item.current_sha256}</CardDescription></CardHeader>
          <CardContent className="flex flex-wrap gap-3"><Button asChild variant="outline"><a href={`/review/oagf-revisions/${item.id}/source/current`} target="_blank">Open retained bytes<ExternalLink className="size-4" /></a></Button><Button asChild variant="ghost"><a href={item.current_source_url} target="_blank" rel="noreferrer">Official URL<ExternalLink className="size-4" /></a></Button></CardContent>
        </Card>
      </div>

      <Card className="mt-8">
        <CardHeader><CardTitle>Classify official revision</CardTitle><CardDescription>Record what the human reviewer determined after comparing both retained versions.</CardDescription></CardHeader>
        <CardContent>
          <form action={resolveAction} className="grid gap-4 lg:max-w-2xl">
            <label className="grid gap-1.5 text-sm font-medium">Reviewer<select name="reviewer_id" required className="border-input bg-background rounded-md border px-3 py-2"><option value="">Choose active reviewer</option>{reviewers.map((actor) => <option key={actor.id} value={actor.id}>{actor.full_name} · {actor.role}</option>)}</select></label>
            <label className="grid gap-1.5 text-sm font-medium">Classification<select name="resolution_code" required className="border-input bg-background rounded-md border px-3 py-2"><option value="">Choose outcome</option><option value="metadata_only_change">Metadata/layout-only change</option><option value="no_material_fiscal_change">No material fiscal change</option><option value="requires_data_republication">Fiscal values changed — republication required</option><option value="investigation_required">Investigation required</option></select></label>
            <label className="grid gap-1.5 text-sm font-medium">Review note<textarea name="note" rows={4} minLength={3} required className="border-input bg-background rounded-md border px-3 py-2" /></label>
            <label className="flex items-start gap-3 text-sm leading-6"><input type="checkbox" name="attestation" className="mt-1 size-4" /><span>I compared the retained previous and current official OAGF source versions. I understand this classification does not silently overwrite published fiscal evidence.</span></label>
            <Button type="submit" disabled={reviewers.length === 0}>Record revision classification</Button>
          </form>
        </CardContent>
      </Card>

      <div className="mt-8 flex gap-3"><Button asChild variant="outline"><Link href="/review/oagf-revisions">Back to revisions</Link></Button><Button asChild variant="outline"><Link href="/review">Evidence control home</Link></Button></div>
    </div>
  )
}
