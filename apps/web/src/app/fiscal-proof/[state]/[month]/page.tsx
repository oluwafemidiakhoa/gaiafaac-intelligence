import type { Metadata } from 'next'
import Link from 'next/link'
import { notFound } from 'next/navigation'

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
import { getFiscalProof } from '@/lib/fiscal-proof-api'
import { formatDate, formatNaira } from '@/lib/format'

export const dynamic = 'force-dynamic'

export async function generateMetadata({
  params,
}: {
  params: Promise<{ state: string; month: string }>
}): Promise<Metadata> {
  const { state, month } = await params
  return { title: `Fiscal Proof · ${state} · ${month}` }
}

export default async function FiscalProofPage({
  params,
}: {
  params: Promise<{ state: string; month: string }>
}) {
  const { state, month } = await params
  const result = await getFiscalProof(state, month)
  if (!result.data) notFound()
  const proof = result.data
  const reconciled = proof.financials.reconciliation_status === 'reconciled'

  return (
    <div className="mx-auto max-w-5xl px-5 py-12 lg:px-8 lg:py-16">
      <PageHeader
        eyebrow="GaiaFAAC Fiscal Proof · v1"
        title={`${proof.state_name} · ${formatDate(proof.revenue_month)}`}
        description={proof.claim}
      />

      <div className="mt-8 flex flex-wrap items-center gap-3">
        <StatusPill
          tone={proof.verification.human_verified ? 'success' : 'neutral'}
        >
          {proof.verification.human_verified
            ? 'Human verified'
            : 'Verification incomplete'}
        </StatusPill>
        <StatusPill tone={reconciled ? 'success' : 'neutral'}>
          {reconciled
            ? 'Arithmetic reconciled'
            : 'Reconciliation not applicable'}
        </StatusPill>
      </div>

      <Card className="mt-8">
        <CardHeader>
          <CardTitle>Proof identity</CardTitle>
          <CardDescription>
            Deterministic identifier derived from the published claim, financial
            values, verification state and source-document fingerprint.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4 text-sm">
          <div>
            <p className="text-muted-foreground">Fiscal Proof ID</p>
            <p className="mt-1 font-mono font-semibold break-all">
              {proof.proof_id}
            </p>
          </div>
          <div>
            <p className="text-muted-foreground">Proof digest · SHA-256</p>
            <p className="mt-1 font-mono break-all">
              {proof.proof_digest_sha256}
            </p>
          </div>
        </CardContent>
      </Card>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Published financial record</CardTitle>
            <CardDescription>{proof.reporting_label}</CardDescription>
          </CardHeader>
          <CardContent>
            <dl className="grid gap-5 text-sm">
              <div className="flex items-center justify-between gap-4">
                <dt className="text-muted-foreground">Gross allocation</dt>
                <dd className="font-mono font-semibold">
                  {formatNaira(proof.financials.gross_total)}
                </dd>
              </div>
              <div className="flex items-center justify-between gap-4">
                <dt className="text-muted-foreground">Deductions</dt>
                <dd className="font-mono font-semibold">
                  {formatNaira(proof.financials.total_deductions)}
                </dd>
              </div>
              <div className="flex items-center justify-between gap-4">
                <dt className="text-muted-foreground">Net allocation</dt>
                <dd className="font-mono font-semibold">
                  {formatNaira(proof.financials.net_allocation)}
                </dd>
              </div>
              <div className="flex items-center justify-between gap-4">
                <dt className="text-muted-foreground">Reconciliation</dt>
                <dd className="font-medium capitalize">
                  {proof.financials.reconciliation_status.replace('_', ' ')}
                </dd>
              </div>
            </dl>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Source evidence</CardTitle>
            <CardDescription>
              {proof.source.source_organization}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 text-sm">
            <div>
              <p className="text-muted-foreground">Document</p>
              <p className="mt-1 font-medium">
                {proof.source.original_filename}
              </p>
            </div>
            <div>
              <p className="text-muted-foreground">Source-document SHA-256</p>
              <p className="mt-1 font-mono break-all">{proof.source.sha256}</p>
            </div>
            {proof.source.source_url ? (
              <Button asChild variant="outline">
                <a
                  href={proof.source.source_url}
                  target="_blank"
                  rel="noreferrer"
                >
                  Open original source
                </a>
              </Button>
            ) : null}
          </CardContent>
        </Card>
      </div>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Verification chain</CardTitle>
          <CardDescription>
            The proof exposes the publication and verification states used to
            generate this record.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <dl className="grid gap-5 text-sm sm:grid-cols-2 lg:grid-cols-4">
            <div>
              <dt className="text-muted-foreground">Allocation</dt>
              <dd className="mt-1 font-medium">
                {proof.verification.allocation_status}
              </dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Period</dt>
              <dd className="mt-1 font-medium">
                {proof.verification.period_status}
              </dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Source</dt>
              <dd className="mt-1 font-medium">
                {proof.verification.source_status}
              </dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Human review</dt>
              <dd className="mt-1 font-medium">
                {proof.verification.human_verified
                  ? 'Confirmed'
                  : 'Not confirmed'}
              </dd>
            </div>
          </dl>
        </CardContent>
      </Card>

      <p className="text-muted-foreground mt-6 text-xs leading-5">
        {proof.disclaimer}
      </p>

      <div className="mt-8 flex flex-wrap gap-4">
        <Link
          href={`/states/${proof.state_slug}`}
          className="text-primary text-sm font-medium hover:underline"
        >
          ← Back to {proof.state_name}
        </Link>
        <Link
          href="/methodology"
          className="text-primary text-sm font-medium hover:underline"
        >
          Read verification methodology →
        </Link>
      </div>
    </div>
  )
}
