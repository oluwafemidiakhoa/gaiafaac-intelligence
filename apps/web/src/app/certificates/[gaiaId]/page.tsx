import type { Metadata } from 'next'
import Link from 'next/link'
import { notFound } from 'next/navigation'

import { CopyHashButton } from '@/components/copy-hash-button'
import { PageHeader } from '@/components/page-header'
import { PrintButton } from '@/components/print-button'
import { StatusPill } from '@/components/status-pill'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { getFiscalCertificate } from '@/lib/fiscal-ledger-api'
import { formatDate, humanize } from '@/lib/format'

export const dynamic = 'force-dynamic'

export async function generateMetadata({
  params,
}: {
  params: Promise<{ gaiaId: string }>
}): Promise<Metadata> {
  const { gaiaId } = await params
  return { title: `Gaia Fiscal Certificate · ${gaiaId}` }
}

export default async function FiscalCertificatePage({
  params,
}: {
  params: Promise<{ gaiaId: string }>
}) {
  const { gaiaId } = await params
  const result = await getFiscalCertificate(gaiaId)
  if (!result.data) notFound()
  const certificate = result.data.data
  const manifest = result.data.evidence.manifest
  const integrityScore = certificate.evidence_integrity.score

  return (
    <div className="mx-auto max-w-5xl px-5 py-12 lg:px-8 lg:py-16 print:max-w-none print:px-0">
      <PageHeader
        eyebrow="Gaia Fiscal Certificate"
        title={`${certificate.jurisdiction.name} · ${certificate.fiscal_period}`}
        description="An immutable point-in-time package of a published Fiscal State and its linked proof objects."
      />

      <div className="mt-7 flex flex-wrap items-center gap-3 print:hidden">
        <PrintButton />
        <Button asChild variant="outline" size="sm">
          <a
            href={`/certificates/${encodeURIComponent(certificate.gaia_id)}/manifest`}
            download
          >
            Download certificate JSON
          </a>
        </Button>
        <Button asChild variant="outline" size="sm">
          <Link href="/fiscal-design/verify">Verify manifest</Link>
        </Button>
      </div>

      <Card className="mt-8">
        <CardHeader className="border-border border-b">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <CardTitle className="text-2xl">
                GAIA FISCAL CERTIFICATE
              </CardTitle>
              <CardDescription className="mt-2">
                Issued {formatDate(certificate.issued_at.slice(0, 10))}
              </CardDescription>
            </div>
            <StatusPill
              tone={
                certificate.ledger_status === 'verified' ? 'success' : 'neutral'
              }
            >
              {humanize(certificate.ledger_status)}
            </StatusPill>
          </div>
        </CardHeader>
        <CardContent className="space-y-8 pt-6">
          <dl className="grid gap-6 text-sm md:grid-cols-2">
            <div>
              <dt className="text-muted-foreground">Certificate</dt>
              <dd className="mt-1 font-mono font-semibold break-all">
                {certificate.gaia_id}
              </dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Fiscal State</dt>
              <dd className="mt-1 font-mono font-semibold break-all">
                <Link
                  href={`/jurisdictions/${certificate.jurisdiction.code}`}
                  className="hover:text-primary"
                >
                  {certificate.fiscal_state_id}
                </Link>
              </dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Evidence integrity</dt>
              <dd className="mt-1 font-mono text-2xl font-semibold">
                {typeof integrityScore === 'string'
                  ? `${integrityScore} / 100`
                  : 'Insufficient evidence'}
              </dd>
            </div>
            <div>
              <dt className="text-muted-foreground">Evidence coverage</dt>
              <dd className="mt-1 font-mono text-2xl font-semibold">
                {certificate.evidence_coverage
                  ? `${(Number(certificate.evidence_coverage) * 100).toFixed(2)}%`
                  : 'Insufficient evidence'}
              </dd>
            </div>
          </dl>

          <div className="grid gap-6 md:grid-cols-3">
            {[
              ['Verified domains', certificate.verified_domains],
              ['Partial / conflicting', certificate.partial_domains],
              ['Unavailable', certificate.unavailable_domains],
            ].map(([label, domains]) => (
              <div key={label as string}>
                <h2 className="text-sm font-semibold">{label as string}</h2>
                <p className="text-muted-foreground mt-2 text-sm capitalize">
                  {(domains as string[]).length
                    ? (domains as string[]).map(humanize).join(', ')
                    : 'None'}
                </p>
              </div>
            ))}
          </div>

          <div>
            <h2 className="text-sm font-semibold">Linked Fiscal Proofs</h2>
            <div className="mt-3 space-y-2">
              {certificate.proof_gaia_ids.length ? (
                certificate.proof_gaia_ids.map((proofId) => (
                  <Link
                    key={proofId}
                    href={`/proofs/${encodeURIComponent(proofId)}`}
                    className="text-primary block font-mono text-sm break-all hover:underline"
                  >
                    {proofId}
                  </Link>
                ))
              ) : (
                <p className="text-muted-foreground text-sm">
                  No proof objects are linked.
                </p>
              )}
            </div>
          </div>

          <div>
            <h2 className="text-sm font-semibold">Manifest SHA-256</h2>
            <p className="mt-2 font-mono text-sm break-all">
              {manifest.payload_sha256}
            </p>
            <div className="mt-3 print:hidden">
              <CopyHashButton value={manifest.payload_sha256} />
            </div>
          </div>
        </CardContent>
      </Card>

      <p className="text-muted-foreground mt-6 text-xs leading-5">
        {result.data.evidence.disclaimer}
      </p>
    </div>
  )
}
