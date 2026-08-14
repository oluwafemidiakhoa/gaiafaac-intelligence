import type { Metadata } from 'next'
import Link from 'next/link'
import { notFound } from 'next/navigation'

import { CopyHashButton } from '@/components/copy-hash-button'
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
import { getLedgerFiscalProof } from '@/lib/fiscal-ledger-api'
import { formatDate, formatNaira } from '@/lib/format'

export const dynamic = 'force-dynamic'

export async function generateMetadata({
  params,
}: {
  params: Promise<{ gaiaId: string }>
}): Promise<Metadata> {
  const { gaiaId } = await params
  return { title: `Gaia Fiscal Proof · ${gaiaId}` }
}

function verificationLabel(value: boolean | null, notApplicable: string) {
  if (value === null) return notApplicable
  return value ? 'Verified' : 'Not verified'
}

export default async function LedgerFiscalProofPage({
  params,
}: {
  params: Promise<{ gaiaId: string }>
}) {
  const { gaiaId } = await params
  const result = await getLedgerFiscalProof(gaiaId)
  if (!result.data) notFound()
  const proof = result.data
  const claim = proof.data
  const manifest = proof.evidence.manifest

  return (
    <div className="mx-auto max-w-6xl px-5 py-12 lg:px-8 lg:py-16">
      <PageHeader
        eyebrow={`Gaia Fiscal Proof · schema ${proof.meta.schema_version}`}
        title={`${claim.jurisdiction.name} · ${claim.fiscal_period}`}
        description="A portable, source-linked representation of a published fiscal claim, identified and hashed by GaiaFAAC."
      />

      <div className="mt-7 flex flex-wrap items-center gap-3">
        <StatusPill tone="success">Artifact published</StatusPill>
        <StatusPill
          tone={claim.verification.source_verified ? 'success' : 'neutral'}
        >
          {claim.verification.source_verified
            ? 'Source provenance verified'
            : 'Source verification incomplete'}
        </StatusPill>
        <StatusPill
          tone={claim.verification.human_reviewed ? 'success' : 'neutral'}
        >
          {claim.verification.human_reviewed
            ? 'Human reviewed'
            : 'Human review incomplete'}
        </StatusPill>
      </div>

      <Card className="mt-8">
        <CardHeader>
          <CardTitle>Proof identity</CardTitle>
          <CardDescription>
            Immutable Gaia ID and deterministic hash over canonical JSON.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-5 text-sm">
          <div>
            <p className="text-muted-foreground">Gaia object ID</p>
            <p className="mt-1 font-mono font-semibold break-all">
              {claim.gaia_id}
            </p>
          </div>
          <div>
            <p className="text-muted-foreground">Manifest payload · SHA-256</p>
            <p className="mt-1 font-mono break-all">
              {manifest.payload_sha256}
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <CopyHashButton value={manifest.payload_sha256} />
            <Button asChild variant="outline" size="sm">
              <a
                href={`/proofs/${encodeURIComponent(claim.gaia_id)}/manifest`}
                download
              >
                Download manifest JSON
              </a>
            </Button>
            <Button asChild variant="outline" size="sm">
              <Link href="/fiscal-design/verify">Verify in browser</Link>
            </Button>
          </div>
        </CardContent>
      </Card>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Fiscal claim</CardTitle>
            <CardDescription>
              Missing values remain unavailable and are never rendered as zero.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <dl className="grid gap-4 text-sm">
              <div className="flex justify-between gap-5 border-b pb-3">
                <dt className="text-muted-foreground">Metric</dt>
                <dd className="font-medium">{claim.metric}</dd>
              </div>
              <div className="flex justify-between gap-5 border-b pb-3">
                <dt className="text-muted-foreground">Value</dt>
                <dd className="font-mono font-semibold">
                  {claim.currency === 'NGN'
                    ? formatNaira(claim.value)
                    : (claim.value ?? 'Unavailable')}
                </dd>
              </div>
              <div className="flex justify-between gap-5 border-b pb-3">
                <dt className="text-muted-foreground">Jurisdiction</dt>
                <dd className="font-medium">{claim.jurisdiction.code}</dd>
              </div>
              <div className="flex justify-between gap-5 border-b pb-3">
                <dt className="text-muted-foreground">Effective at</dt>
                <dd>{formatDate(claim.effective_at.slice(0, 10))}</dd>
              </div>
              <div className="flex justify-between gap-5">
                <dt className="text-muted-foreground">Methodology</dt>
                <dd>{claim.methodology_version}</dd>
              </div>
            </dl>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Source evidence</CardTitle>
            <CardDescription>{claim.source.publisher}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 text-sm">
            <div>
              <p className="text-muted-foreground">Source-document SHA-256</p>
              <p className="mt-1 font-mono break-all">
                {claim.source.document_sha256}
              </p>
            </div>
            <div>
              <p className="text-muted-foreground">Publication date</p>
              <p className="mt-1">
                {claim.source.publication_date
                  ? formatDate(claim.source.publication_date)
                  : 'Unavailable'}
              </p>
            </div>
            <div>
              <p className="text-muted-foreground">Page / table</p>
              <p className="mt-1">
                {claim.source.page ?? 'Not recorded'} ·{' '}
                {claim.source.table ?? 'Not recorded'}
              </p>
            </div>
            {claim.source.document_url ? (
              <Button asChild variant="outline" size="sm">
                <a
                  href={claim.source.document_url}
                  target="_blank"
                  rel="noreferrer"
                >
                  Open source document
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
            Separate workflow assertions; cryptographic integrity alone does not
            prove the originating government claim is true.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <dl className="grid gap-5 text-sm sm:grid-cols-2 lg:grid-cols-4">
            <div>
              <dt className="text-muted-foreground">Artifact integrity</dt>
              <dd className="mt-1 font-semibold">Verified</dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Source provenance</dt>
              <dd className="mt-1 font-semibold">
                {verificationLabel(
                  claim.verification.source_verified,
                  'Not recorded',
                )}
              </dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Reconciliation</dt>
              <dd className="mt-1 font-semibold">
                {verificationLabel(
                  claim.verification.reconciled,
                  'Not applicable',
                )}
              </dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Human review</dt>
              <dd className="mt-1 font-semibold">
                {verificationLabel(
                  claim.verification.human_reviewed,
                  'Not recorded',
                )}
              </dd>
            </div>
          </dl>
          <p className="text-muted-foreground mt-5 text-xs leading-5">
            {claim.verification.note}
          </p>
        </CardContent>
      </Card>

      {(claim.supersedes_gaia_id || claim.superseded_by_gaia_id) && (
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>Evidence history</CardTitle>
            <CardDescription>
              Explicit lineage between immutable proof versions.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            {claim.supersedes_gaia_id ? (
              <Link
                href={`/proofs/${claim.supersedes_gaia_id}`}
                className="text-primary block font-mono hover:underline"
              >
                Previous: {claim.supersedes_gaia_id}
              </Link>
            ) : null}
            {claim.superseded_by_gaia_id ? (
              <Link
                href={`/proofs/${claim.superseded_by_gaia_id}`}
                className="text-primary block font-mono hover:underline"
              >
                Superseded by: {claim.superseded_by_gaia_id}
              </Link>
            ) : null}
          </CardContent>
        </Card>
      )}

      <p className="text-muted-foreground mt-6 text-xs leading-5">
        {proof.evidence.disclaimer}
      </p>
    </div>
  )
}
