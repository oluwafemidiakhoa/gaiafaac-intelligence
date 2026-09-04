import { CheckCircle2, Fingerprint, GitBranch, ShieldCheck } from 'lucide-react'
import type { Metadata } from 'next'

import { DataUnavailable } from '@/components/data-unavailable'
import { PageHeader } from '@/components/page-header'
import { StatusPill } from '@/components/status-pill'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { verifyFiscalReceipt } from '@/lib/fiscal-receipt-api'

export const dynamic = 'force-dynamic'

export const metadata: Metadata = {
  title: 'Verify Fiscal Receipt | Gaia Fiscal Intelligence',
  description:
    'Verify the evidence manifest, lineage and SHA-256 digest recorded by a Gaia Fiscal Receipt.',
}

function shortHash(value: string) {
  return `${value.slice(0, 16)}…${value.slice(-12)}`
}

export default async function VerifyFiscalReceiptPage({
  params,
}: {
  params: Promise<{ receiptId: string }>
}) {
  const { receiptId } = await params
  const result = await verifyFiscalReceipt(receiptId)

  if (!result.data) {
    return (
      <div className="gaia-shell py-12 lg:py-16">
        <PageHeader
          eyebrow="Fiscal Receipt verification"
          title="Receipt could not be verified"
          description="Gaia could not resolve this receipt against the current verification registry."
        />
        <div className="mt-8">
          <DataUnavailable
            message={result.error ?? 'Fiscal Receipt unavailable.'}
          />
        </div>
      </div>
    )
  }

  const receipt = result.data
  const hasLineage = Boolean(
    receipt.predecessor_receipt_id || receipt.triggering_match_id,
  )

  return (
    <div className="gaia-shell py-12 lg:py-16">
      <PageHeader
        eyebrow="Fiscal Receipt · evidence manifest"
        title="Evidence boundary verified"
        description="This page verifies the recorded evidence manifest and declared lineage behind a Gaia analysis. It does not certify the quality of a lending, investment, procurement or policy decision."
      />

      <div className="mt-7 flex flex-wrap items-center gap-3">
        <StatusPill tone="success">Receipt found</StatusPill>
        {hasLineage ? (
          <StatusPill tone="warning">Successor receipt</StatusPill>
        ) : null}
        <span className="text-muted-foreground font-mono text-xs">
          {receipt.methodology_version}
        </span>
      </div>

      <div className="mt-8 grid gap-5 lg:grid-cols-[1.1fr_0.9fr]">
        <Card>
          <CardHeader>
            <div className="flex items-start gap-3">
              <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-2 text-emerald-800">
                <Fingerprint className="size-5" aria-hidden="true" />
              </div>
              <div>
                <CardTitle>Receipt fingerprint</CardTitle>
                <CardDescription>
                  SHA-256 of the canonical private evidence manifest recorded by
                  Gaia.
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-5">
            <div>
              <p className="text-muted-foreground text-xs font-semibold tracking-wide uppercase">
                Receipt ID
              </p>
              <p className="mt-1 font-mono text-sm break-all">{receipt.id}</p>
            </div>
            <div>
              <p className="text-muted-foreground text-xs font-semibold tracking-wide uppercase">
                Receipt SHA-256
              </p>
              <p className="mt-1 font-mono text-sm break-all">
                {receipt.receipt_sha256}
              </p>
            </div>
            {receipt.content_sha256 ? (
              <div>
                <p className="text-muted-foreground text-xs font-semibold tracking-wide uppercase">
                  Evidence-content SHA-256
                </p>
                <p className="mt-1 font-mono text-sm break-all">
                  {receipt.content_sha256}
                </p>
              </div>
            ) : null}
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <p className="text-muted-foreground text-xs font-semibold tracking-wide uppercase">
                  Generated
                </p>
                <p className="mt-1 text-sm">
                  {new Date(receipt.created_at).toLocaleString('en-GB', {
                    timeZone: 'UTC',
                    dateStyle: 'medium',
                    timeStyle: 'short',
                  })}{' '}
                  UTC
                </p>
              </div>
              <div>
                <p className="text-muted-foreground text-xs font-semibold tracking-wide uppercase">
                  Evidence cutoff
                </p>
                <p className="mt-1 text-sm">
                  {receipt.evidence_cutoff
                    ? new Date(receipt.evidence_cutoff).toISOString()
                    : 'No explicit cutoff declared'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-start gap-3">
              <div className="rounded-xl border border-sky-200 bg-sky-50 p-2 text-sky-800">
                <ShieldCheck className="size-5" aria-hidden="true" />
              </div>
              <div>
                <CardTitle>What this verifies</CardTitle>
                <CardDescription>{receipt.statement}</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-muted-foreground text-xs">
                  Evidence records
                </p>
                <p className="mt-1 font-mono text-2xl font-semibold">
                  {receipt.evidence_count}
                </p>
              </div>
              <div>
                <p className="text-muted-foreground text-xs">
                  Source fingerprints
                </p>
                <p className="mt-1 font-mono text-2xl font-semibold">
                  {receipt.source_sha256s.length}
                </p>
              </div>
            </div>
            <div>
              <p className="text-muted-foreground text-xs">Jurisdictions</p>
              <p className="mt-1 text-sm font-medium">
                {receipt.jurisdictions.length
                  ? receipt.jurisdictions.join(', ')
                  : 'No jurisdiction label declared'}
              </p>
            </div>
            <div>
              <p className="text-muted-foreground text-xs">Evidence domains</p>
              <p className="mt-1 text-sm font-medium">
                {receipt.evidence_domains.length
                  ? receipt.evidence_domains.join(', ')
                  : 'No domain label declared'}
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {hasLineage ? (
        <Card className="mt-5">
          <CardHeader>
            <div className="flex items-start gap-3">
              <GitBranch
                className="mt-0.5 size-5 text-emerald-700"
                aria-hidden="true"
              />
              <div>
                <CardTitle>Receipt lineage</CardTitle>
                <CardDescription>
                  This receipt records continuity with a prior evidence boundary
                  and, when present, the governed Watch Contract match that
                  triggered institutional re-review.
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="grid gap-5 md:grid-cols-2">
            <div>
              <p className="text-muted-foreground text-xs font-semibold tracking-wide uppercase">
                Predecessor receipt
              </p>
              <p className="mt-2 font-mono text-sm break-all">
                {receipt.predecessor_receipt_id ?? 'No predecessor declared'}
              </p>
              {receipt.predecessor_receipt_sha256 ? (
                <p
                  className="text-muted-foreground mt-2 font-mono text-xs"
                  title={receipt.predecessor_receipt_sha256}
                >
                  SHA-256 {shortHash(receipt.predecessor_receipt_sha256)}
                </p>
              ) : null}
            </div>
            <div>
              <p className="text-muted-foreground text-xs font-semibold tracking-wide uppercase">
                Monitoring trigger
              </p>
              <p className="mt-2 font-mono text-sm break-all">
                {receipt.triggering_match_id ??
                  'Evidence changed without a declared Watch Contract trigger'}
              </p>
            </div>
          </CardContent>
        </Card>
      ) : null}

      <Card className="mt-5">
        <CardHeader>
          <CardTitle>Evidence record fingerprints</CardTitle>
          <CardDescription>
            These hashes identify the captured evidence records without exposing
            private organization notes or the internal decision question.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {receipt.evidence_record_sha256s.length ? (
            <div className="divide-border border-border divide-y rounded-xl border">
              {receipt.evidence_record_sha256s.map((hash, index) => (
                <div
                  key={hash}
                  className="flex flex-col gap-1 px-4 py-3 sm:flex-row sm:items-center sm:justify-between"
                >
                  <span className="text-sm font-medium">
                    {receipt.evidence_kinds[index] ?? 'governed evidence'}
                  </span>
                  <span
                    className="text-muted-foreground font-mono text-xs"
                    title={hash}
                  >
                    {shortHash(hash)}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-muted-foreground text-sm">
              This receipt contains no captured evidence records.
            </p>
          )}
        </CardContent>
      </Card>

      <Card className="mt-5">
        <CardHeader>
          <div className="flex items-start gap-3">
            <CheckCircle2
              className="mt-0.5 size-5 text-amber-700"
              aria-hidden="true"
            />
            <div>
              <CardTitle>Verification boundary</CardTitle>
              <CardDescription>
                A Fiscal Receipt is an evidence receipt, not a rating,
                recommendation, government certification or investment opinion.
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <ul className="text-muted-foreground grid gap-2 text-sm">
            {receipt.limitations.map((item) => (
              <li key={item} className="flex gap-2">
                <span aria-hidden="true">—</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>
    </div>
  )
}
