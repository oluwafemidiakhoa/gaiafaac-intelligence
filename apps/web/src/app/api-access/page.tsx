import type { Metadata } from 'next'
import Link from 'next/link'

import { PageHeader } from '@/components/page-header'
import { Button } from '@/components/ui/button'

export const metadata: Metadata = {
  title: 'API Access',
  description:
    'Integrate verified Nigerian fiscal data into your systems with our robust REST API.',
}

export default function APIAccessPage() {
  return (
    <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
      <PageHeader
        eyebrow="Developer Access"
        title="Integrate verified fiscal data via API"
        description="Build institutional workflows and applications with governed evidence from GaiaFAAC."
      />

      <div className="mt-12 grid gap-8 md:grid-cols-2">
        <div className="rounded-lg border border-border p-6">
          <h3 className="font-semibold text-lg mb-4">REST API</h3>
          <p className="text-muted-foreground mb-6">
            Query published FAAC allocations, state profiles, fiscal events and institutional evidence through our comprehensive REST endpoints.
          </p>
          <ul className="space-y-2 text-sm mb-6">
            <li className="flex items-start gap-2">
              <span className="text-primary mt-1">•</span>
              <span>Real-time verified data access</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-primary mt-1">•</span>
              <span>Pagination and filtering</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-primary mt-1">•</span>
              <span>Full audit trail lineage</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-primary mt-1">•</span>
              <span>JSON responses</span>
            </li>
          </ul>
          <Button asChild>
            <Link href="/documentation">View API Docs</Link>
          </Button>
        </div>

        <div className="rounded-lg border border-border p-6">
          <h3 className="font-semibold text-lg mb-4">Data Exports</h3>
          <p className="text-muted-foreground mb-6">
            Download complete datasets in CSV and Excel formats for offline analysis and institutional reporting.
          </p>
          <ul className="space-y-2 text-sm mb-6">
            <li className="flex items-start gap-2">
              <span className="text-primary mt-1">•</span>
              <span>Historical data snapshots</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-primary mt-1">•</span>
              <span>Custom date ranges</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-primary mt-1">•</span>
              <span>Evidence metadata included</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-primary mt-1">•</span>
              <span>SHA-256 verification</span>
            </li>
          </ul>
          <Button asChild variant="outline">
            <Link href="/pricing">Explore Plans</Link>
          </Button>
        </div>
      </div>

      <div className="mt-12 rounded-lg border border-border bg-muted/50 p-8">
        <h2 className="font-bold text-xl mb-4">Ready to integrate?</h2>
        <p className="text-muted-foreground mb-6">
          Request API credentials and receive dedicated support for your institution.
        </p>
        <Button asChild size="lg">
          <Link href="/pilot?plan=api">Request API Access</Link>
        </Button>
      </div>
    </div>
  )
}
