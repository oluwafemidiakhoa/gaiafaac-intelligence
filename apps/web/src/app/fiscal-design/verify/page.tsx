import type { Metadata } from 'next'
import Link from 'next/link'

import { PageHeader } from '@/components/page-header'
import { Button } from '@/components/ui/button'

import { ManifestVerifier } from './manifest-verifier'

export const metadata: Metadata = { title: 'Verify Fiscal Design Manifest' }

export default function FiscalDesignManifestVerifierPage() {
  return (
    <div className="mx-auto max-w-6xl px-5 py-12 lg:px-8 lg:py-16">
      <PageHeader
        eyebrow="Gaia Fiscal Design Lab"
        title="Verify an evidence manifest"
        description="Independently check whether a portable Fiscal Design evidence manifest still matches its embedded SHA-256 fingerprint. Verification runs in your browser and does not upload the manifest."
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
