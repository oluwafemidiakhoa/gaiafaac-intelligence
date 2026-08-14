import type { Metadata } from 'next'
import Link from 'next/link'

import { PageHeader } from '@/components/page-header'
import { Button } from '@/components/ui/button'

import { ManifestVerifier } from './manifest-verifier'

export const metadata: Metadata = { title: 'Gaia Fiscal Proof Verification' }

export default function FiscalDesignManifestVerifierPage() {
  return (
    <div className="mx-auto max-w-6xl px-5 py-12 lg:px-8 lg:py-16">
      <PageHeader
        eyebrow="Gaia Fiscal Proof"
        title="Verify a fiscal artifact"
        description="Independently recompute the SHA-256 integrity hash for a Gaia Fiscal Proof or Fiscal Design evidence manifest. Verification runs in your browser and does not upload the artifact."
      />

      <div className="mt-6">
        <Button asChild variant="outline">
          <Link href="/fiscal-design">Back to Fiscal Design Lab</Link>
        </Button>
      </div>

      <ManifestVerifier />
    </div>
  )
}
