import { ExternalLink, FileText } from 'lucide-react'
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
import { formatDate } from '@/lib/format'
import { getPublishedOverview } from '@/lib/published-api'

export const metadata: Metadata = { title: 'Sources' }
export const dynamic = 'force-dynamic'

export default async function SourcesPage() {
  const result = await getPublishedOverview()
  const data = result.data

  return (
    <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
      <PageHeader
        eyebrow="Source registry"
        title="Trace every figure to its document"
        description="Each published month links to the exact official OAGF report it was extracted from, verified by SHA-256."
      />

      {data === null ? (
        <div className="mt-10">
          <DataUnavailable
            message={result.error ?? 'No verified month is published yet.'}
          />
        </div>
      ) : (
        <div className="mt-10 space-y-5">
          <Card>
            <CardHeader>
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <FileText className="text-primary size-5" aria-hidden="true" />
                  <CardTitle className="pt-3">
                    {data.source.original_filename}
                  </CardTitle>
                  <CardDescription className="mt-2">
                    {data.source.source_organization} ·{' '}
                    {data.period.reporting_label}
                  </CardDescription>
                </div>
                <StatusPill tone="success">Verified · published</StatusPill>
              </div>
            </CardHeader>
            <CardContent>
              <dl className="grid gap-5 text-sm sm:grid-cols-2 lg:grid-cols-3">
                <div>
                  <dt className="text-muted-foreground">Reporting period</dt>
                  <dd className="mt-1 font-medium">
                    {formatDate(data.period.revenue_month)}
                  </dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Report published</dt>
                  <dd className="mt-1 font-medium">
                    {formatDate(data.source.publication_date)}
                  </dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Jurisdictions</dt>
                  <dd className="mt-1 font-mono">
                    {data.covered_states} / {data.expected_states}
                  </dd>
                </div>
                <div className="sm:col-span-2 lg:col-span-3">
                  <dt className="text-muted-foreground">SHA-256</dt>
                  <dd className="mt-1 font-mono text-xs break-all">
                    {data.source.sha256}
                  </dd>
                </div>
              </dl>
              {data.source.source_url ? (
                <a
                  href={data.source.source_url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-primary mt-5 inline-flex items-center gap-1 text-sm font-medium hover:underline"
                >
                  Open the original OAGF document
                  <ExternalLink className="size-3.5" aria-hidden="true" />
                </a>
              ) : null}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
