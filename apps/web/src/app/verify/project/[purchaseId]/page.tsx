import {
  AlertTriangle,
  CheckCircle2,
  Fingerprint,
  History,
  ShieldCheck,
} from 'lucide-react'
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
import { verifyProjectReceipt } from '@/lib/project-receipt-api'

export const dynamic = 'force-dynamic'

export const metadata: Metadata = {
  title: 'Verify Project Receipt | Gaia Fiscal Intelligence',
  description:
    'Verify the frozen artifact, source fingerprints and revision state behind a Gaia Fiscal Intelligence Project Product.',
}

function shortHash(value: string) {
  return `${value.slice(0, 16)}…${value.slice(-12)}`
}

export default async function VerifyProjectReceiptPage({
  params,
}: {
  params: Promise<{ purchaseId: string }>
}) {
  const { purchaseId } = await params
  const result = await verifyProjectReceipt(purchaseId)

  if (!result.data) {
    return (
      <div className="gaia-shell py-12 lg:py-16">
        <PageHeader
          eyebrow="Project receipt verification"
          title="Project receipt could not be verified"
          description="Gaia could not resolve this issued Project Product against the current public verification registry."
        />
        <div className="mt-8">
          <DataUnavailable message={result.error ?? 'Project receipt unavailable.'} />
        </div>
      </div>
    )
  }

  const receipt = result.data
  const integrityVerified = receipt.integrity_status === 'verified'
  const revisionTone =
    receipt.revision_status === 'review_recommended' ||
    receipt.revision_status === 'integrity_failure'
      ? 'warning'
      : 'success'

  return (
    <div className="gaia-shell py-12 lg:py-16">
      <PageHeader
        eyebrow="GAIA FISCAL INTELLIGENCE · project receipt"
        title={integrityVerified ? 'Issued intelligence verified' : 'Integrity check failed'}
        description="This verification page checks the frozen artifact SHA-256, the document fingerprint and the source fingerprints recorded when the Project Product was fulfilled."
      />

      <div className="mt-7 flex flex-wrap items-center gap-3">
        <StatusPill tone={integrityVerified ? 'success' : 'warning'}>
          {integrityVerified ? 'Artifact integrity verified' : 'Integrity failure'}
        </StatusPill>
        <StatusPill tone={revisionTone}>
          {receipt.revision_status.replaceAll('_', ' ')}
        </StatusPill>
        <span className="text-muted-foreground font-mono text-xs">
          {receipt.document_id}
        </span>
      </div>

      <div className="mt-8 grid gap-5 lg:grid-cols-[1.08fr_0.92fr]">
        <Card>
          <CardHeader>
            <div className="flex items-start gap-3">
              <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-2 text-emerald-800">
                <Fingerprint className="size-5" aria-hidden="true" />
              </div>
              <div>
                <CardTitle>Frozen intelligence artifact</CardTitle>
                <CardDescription>
                  The artifact digest binds the issued intelligence package to the
                  evidence state Gaia froze for this order.
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-5">
            <div>
              <p className="text-muted-foreground text-xs font-semibold tracking-wide uppercase">
                Document ID
              </p>
              <p className="mt-1 font-mono text-sm break-all">{receipt.document_id}</p>
            </div>
            <div>
              <p className="text-muted-foreground text-xs font-semibold tracking-wide uppercase">
                Artifact SHA-256
              </p>
              <p className="mt-1 font-mono text-sm break-all">
                {receipt.artifact_sha256}
              </p>
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <p className="text-muted-foreground text-xs">Product</p>
                <p className="mt-1 text-sm font-semibold">{receipt.product_label}</p>
              </div>
              <div>
                <p className="text-muted-foreground text-xs">Jurisdiction / scope</p>
                <p className="mt-1 text-sm font-semibold">
                  {receipt.jurisdictions.length
                    ? receipt.jurisdictions.join(', ')
                    : 'Governed evidence boundary'}
                </p>
              </div>
              <div>
                <p className="text-muted-foreground text-xs">Evidence captured</p>
                <p className="mt-1 text-sm">
                  {receipt.evidence_captured_at ?? 'Capture time not declared'}
                </p>
              </div>
              <div>
                <p className="text-muted-foreground text-xs">Issued</p>
                <p className="mt-1 text-sm">
                  {receipt.issued_at
                    ? new Date(receipt.issued_at).toLocaleString('en-GB', {
                        timeZone: 'UTC',
                        dateStyle: 'medium',
                        timeStyle: 'short',
                      })
                    : 'Issuance time unavailable'}
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
                <CardTitle>What Gaia verifies</CardTitle>
                <CardDescription>{receipt.statement}</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-muted-foreground text-xs">Source fingerprints</p>
                <p className="mt-1 font-mono text-2xl font-semibold">
                  {receipt.source_count}
                </p>
              </div>
              <div>
                <p className="text-muted-foreground text-xs">Artifact schema</p>
                <p className="mt-1 text-sm font-semibold">
                  {receipt.artifact_schema ?? 'Not declared'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card className="mt-5">
        <CardHeader>
          <div className="flex items-start gap-3">
            {receipt.revision_status === 'review_recommended' ? (
              <AlertTriangle className="mt-0.5 size-5 text-amber-700" aria-hidden="true" />
            ) : (
              <History className="mt-0.5 size-5 text-emerald-700" aria-hidden="true" />
            )}
            <div>
              <CardTitle>Revision intelligence</CardTitle>
              <CardDescription>
                Gaia checks whether source documents captured in this paid artifact
                have known successor versions in the governed source registry.
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {receipt.revision_status === 'review_recommended' ? (
            <div>
              <p className="font-semibold text-amber-800">Review recommended</p>
              <p className="text-muted-foreground mt-1 text-sm leading-6">
                One or more source documents used in the issued artifact now have a
                known successor. The original receipt remains immutable, but a fresh
                review may be appropriate.
              </p>
            </div>
          ) : receipt.revision_status === 'source_registry_partial' ? (
            <div>
              <p className="font-semibold">Source registry coverage is partial</p>
              <p className="text-muted-foreground mt-1 text-sm leading-6">
                Gaia verified the artifact hash, but not every captured source
                fingerprint could be resolved against the current source registry.
              </p>
            </div>
          ) : integrityVerified ? (
            <div className="flex gap-3">
              <CheckCircle2 className="mt-0.5 size-5 shrink-0 text-emerald-700" />
              <div>
                <p className="font-semibold">No known source revision detected</p>
                <p className="text-muted-foreground mt-1 text-sm leading-6">
                  Gaia currently knows of no successor source document for the
                  captured source fingerprints in this receipt.
                </p>
              </div>
            </div>
          ) : (
            <p className="text-sm font-semibold text-amber-800">
              Revision status cannot be trusted because artifact integrity failed.
            </p>
          )}
        </CardContent>
      </Card>

      <Card className="mt-5">
        <CardHeader>
          <CardTitle>Captured source fingerprints</CardTitle>
          <CardDescription>
            These SHA-256 values identify source evidence without exposing private
            organization notes or customer decision context.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {receipt.source_sha256s.length ? (
            <div className="divide-border border-border divide-y rounded-xl border">
              {receipt.source_sha256s.map((hash) => (
                <div
                  key={hash}
                  className="flex flex-col gap-1 px-4 py-3 sm:flex-row sm:items-center sm:justify-between"
                >
                  <span className="text-sm font-medium">Governed source</span>
                  <span className="text-muted-foreground font-mono text-xs" title={hash}>
                    {shortHash(hash)}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-muted-foreground text-sm">
              No source SHA-256 fingerprints were present in this artifact.
            </p>
          )}
        </CardContent>
      </Card>

      <Card className="mt-5">
        <CardHeader>
          <CardTitle>Verification boundary</CardTitle>
          <CardDescription>
            Artifact verification is deliberately narrower than an investment,
            lending or policy opinion.
          </CardDescription>
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
