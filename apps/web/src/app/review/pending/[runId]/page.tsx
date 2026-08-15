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
import { approveReview, getReviewPacket, rejectReview } from '@/lib/review-api'

export const metadata: Metadata = { title: 'Accountant review packet' }
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
  const result = await getReviewPacket(runId)
  const packet = result.data

  async function approveAction(formData: FormData) {
    'use server'

    const note = String(formData.get('note') ?? '').trim()
    const attestation = formData.get('attestation') === 'on'
    if (!attestation) {
      redirect(
        `/review/pending/${encodeURIComponent(runId)}?error=${encodeURIComponent('You must complete the reviewer attestation before approval.')}`,
      )
    }
    const action = await approveReview(runId, note || undefined)
    if (action.error) {
      redirect(
        `/review/pending/${encodeURIComponent(runId)}?error=${encodeURIComponent(action.error)}`,
      )
    }
    redirect('/review/pending')
  }

  async function rejectAction(formData: FormData) {
    'use server'

    const reason = String(formData.get('reason') ?? '').trim()
    if (reason.length < 3) {
      redirect(
        `/review/pending/${encodeURIComponent(runId)}?error=${encodeURIComponent('A clear rejection reason is required.')}`,
      )
    }
    const action = await rejectReview(runId, reason)
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
          eyebrow="Controlled accountant review"
          title="Review packet unavailable"
          description="Only real, unpublished evidence can be opened in the accountant review workspace."
        />
        <div className="mt-8">
          <DataUnavailable
            message={result.error ?? 'Review packet unavailable.'}
          />
        </div>
        <Button asChild variant="outline" className="mt-5">
          <Link href="/review/pending">Back to review queue</Link>
        </Button>
      </div>
    )
  }

  const complete = packet.covered_states === packet.expected_states
  const canApprove = complete && packet.blocking_count === 0

  return (
    <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
      <PageHeader
        eyebrow="Controlled accountant review"
        title={packet.reporting_label}
        description="Compare the extracted evidence against the retained official source before recording a human verification decision. Approval does not publish the report."
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
              <div>
                <dt className="text-muted-foreground">Reporting period</dt>
                <dd className="mt-1 font-medium">
                  {formatDate(packet.revenue_month)}
                </dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Publication date</dt>
                <dd className="mt-1 font-medium">
                  {formatDate(packet.source.publication_date)}
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
                href={packet.source.source_url}
                target="_blank"
                rel="noreferrer"
                className="text-primary mt-5 inline-flex items-center gap-1 text-sm font-medium hover:underline"
              >
                Open retained official source
                <ExternalLink className="size-3.5" aria-hidden="true" />
              </a>
            ) : (
              <p className="text-muted-foreground mt-5 text-sm">
                No external source URL was retained. Verify against the
                controlled source archive before approval.
              </p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <ShieldCheck className="text-primary size-5" aria-hidden="true" />
            <CardTitle className="pt-3">Control status</CardTitle>
            <CardDescription>
              Approval is enabled only for complete evidence with no blocking
              validation findings.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <dl className="grid gap-4 text-sm sm:grid-cols-2 lg:grid-cols-1">
              <div>
                <dt className="text-muted-foreground">Coverage</dt>
                <dd className="mt-1 font-mono font-semibold">
                  {packet.covered_states} / {packet.expected_states}
                </dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Validation findings</dt>
                <dd className="mt-1 font-semibold">{packet.finding_count}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Blocking findings</dt>
                <dd className="mt-1 font-semibold">{packet.blocking_count}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Pipeline status</dt>
                <dd className="mt-1 font-medium">{humanize(packet.status)}</dd>
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
              Jurisdiction reconciliation
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
                <th className="px-4 py-3 font-medium">Gross</th>
                <th className="px-4 py-3 font-medium">Deductions</th>
                <th className="px-4 py-3 font-medium">Net</th>
                <th className="px-4 py-3 font-medium">Validation</th>
                <th className="px-4 py-3 font-medium">Confidence</th>
              </tr>
            </thead>
            <tbody>
              {packet.allocations.map((allocation) => (
                <tr
                  key={allocation.state_code}
                  className="border-border border-b last:border-0"
                >
                  <td className="px-4 py-3 font-medium">
                    {allocation.state_name}{' '}
                    <span className="text-muted-foreground font-mono text-xs">
                      {allocation.state_code}
                    </span>
                  </td>
                  <td className="px-4 py-3 font-mono text-xs">
                    {rawAmount(
                      allocation.gross_total,
                      allocation.reported_unit,
                    )}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs">
                    {rawAmount(
                      allocation.total_deductions,
                      allocation.reported_unit,
                    )}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs font-semibold">
                    {rawAmount(
                      allocation.net_allocation,
                      allocation.reported_unit,
                    )}
                  </td>
                  <td className="px-4 py-3 text-xs">
                    {humanize(allocation.verification_status)}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs">
                    {allocation.extraction_confidence ?? 'Not provided'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="mt-8">
        <p className="text-primary font-mono text-xs font-semibold tracking-[0.18em] uppercase">
          Validation record
        </p>
        <h2 className="mt-2 text-2xl font-semibold">
          Findings requiring review
        </h2>
        {packet.findings.length ? (
          <div className="mt-5 space-y-3">
            {packet.findings.map((finding, index) => (
              <Card key={`${finding.rule_code}-${index}`}>
                <CardContent className="grid gap-3 pt-6 md:grid-cols-[9rem_1fr_auto] md:items-start">
                  <span className="font-mono text-xs font-semibold">
                    {finding.rule_code}
                  </span>
                  <div>
                    <p className="text-sm font-medium">{finding.message}</p>
                    {finding.details ? (
                      <pre className="bg-muted mt-3 overflow-x-auto rounded-md p-3 font-mono text-xs whitespace-pre-wrap">
                        {JSON.stringify(finding.details, null, 2)}
                      </pre>
                    ) : null}
                  </div>
                  <StatusPill tone="neutral">{finding.severity}</StatusPill>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <Card className="mt-5 border-dashed">
            <CardContent className="pt-6 text-sm">
              Automated validation recorded no findings for this import.
            </CardContent>
          </Card>
        )}
      </section>

      <section className="mt-10 grid gap-5 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Approve evidence</CardTitle>
            <CardDescription>
              Record human verification only after reconciling the extracted
              values against the official source. This action does not publish
              the report.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form action={approveAction} className="space-y-4">
              <label className="grid gap-1.5 text-sm font-medium">
                Review note (optional)
                <textarea
                  name="note"
                  rows={4}
                  className="border-input bg-background rounded-md border px-3 py-2 text-sm"
                  placeholder="Document material review observations or reconciliation notes."
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
                  I attest that I reviewed the retained source, checked the
                  reporting period and jurisdiction coverage, investigated
                  validation findings, and found the extracted evidence suitable
                  for human verification.
                </span>
              </label>
              <Button type="submit" disabled={!canApprove}>
                Record human verification
              </Button>
              {!canApprove ? (
                <p className="text-muted-foreground text-xs leading-5">
                  Approval is disabled until coverage is complete and all
                  blocking findings are resolved.
                </p>
              ) : null}
            </form>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Reject evidence</CardTitle>
            <CardDescription>
              Reject when the source, extraction, reconciliation, or validation
              evidence is not acceptable. The rejected records and reason remain
              in the audit trail.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form action={rejectAction} className="space-y-4">
              <label className="grid gap-1.5 text-sm font-medium">
                Rejection reason
                <textarea
                  name="reason"
                  rows={5}
                  required
                  minLength={3}
                  className="border-input bg-background rounded-md border px-3 py-2 text-sm"
                  placeholder="Describe the evidence problem clearly enough for remediation and later audit."
                />
              </label>
              <Button type="submit" variant="outline">
                Reject and preserve evidence
              </Button>
            </form>
          </CardContent>
        </Card>
      </section>

      <div className="mt-8">
        <Button asChild variant="outline">
          <Link href="/review/pending">Back to review queue</Link>
        </Button>
      </div>
    </div>
  )
}
