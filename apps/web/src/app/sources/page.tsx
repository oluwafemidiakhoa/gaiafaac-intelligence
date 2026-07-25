import { ExternalLink, FileText } from 'lucide-react'
import type { Metadata } from 'next'

import { DataUnavailable } from '@/components/data-unavailable'
import { DemoBanner } from '@/components/demo-banner'
import { PageHeader } from '@/components/page-header'
import { StatusPill } from '@/components/status-pill'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { getDemoSources } from '@/lib/demo-api'
import { formatDate, humanize } from '@/lib/format'

export const metadata: Metadata = { title: 'Demo sources' }
export const dynamic = 'force-dynamic'

export default async function SourcesPage() {
  const result = await getDemoSources()

  return (
    <>
      <DemoBanner note="The registered source is the synthetic CSV shipped with this repository." />
      <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
        <PageHeader
          eyebrow="Source registry"
          title="Trace every demo value to its file"
          description="Only safe source metadata is exposed. Internal storage paths are deliberately omitted."
        />

        {result.data === null ? (
          <div className="mt-10">
            <DataUnavailable
              message={result.error ?? 'The source registry is unavailable.'}
            />
          </div>
        ) : result.data.sources.length === 0 ? (
          <div className="mt-10">
            <DataUnavailable message="No labelled demo source is registered." />
          </div>
        ) : (
          <div className="mt-10 space-y-5">
            {result.data.sources.map((source) => (
              <Card key={source.id}>
                <CardHeader>
                  <div className="flex flex-wrap items-start justify-between gap-4">
                    <div>
                      <FileText
                        className="text-primary size-5"
                        aria-hidden="true"
                      />
                      <CardTitle className="pt-3">
                        {source.original_filename}
                      </CardTitle>
                      <CardDescription className="mt-2">
                        {source.source_organization}
                      </CardDescription>
                    </div>
                    <StatusPill tone="demo">
                      {humanize(source.source_status)}
                    </StatusPill>
                  </div>
                </CardHeader>
                <CardContent>
                  <dl className="grid gap-5 text-sm sm:grid-cols-2 lg:grid-cols-3">
                    <div>
                      <dt className="text-muted-foreground">Publication date</dt>
                      <dd className="mt-1 font-medium">
                        {formatDate(source.publication_date)}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-muted-foreground">MIME type</dt>
                      <dd className="mt-1 font-mono">{source.mime_type}</dd>
                    </div>
                    <div>
                      <dt className="text-muted-foreground">Version</dt>
                      <dd className="mt-1 font-mono">
                        {source.document_version}
                      </dd>
                    </div>
                    <div className="sm:col-span-2 lg:col-span-3">
                      <dt className="text-muted-foreground">SHA-256</dt>
                      <dd className="mt-1 break-all font-mono text-xs">
                        {source.sha256}
                      </dd>
                    </div>
                  </dl>
                  {source.source_url ? (
                    <a
                      href={source.source_url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-primary mt-5 inline-flex items-center gap-1 text-sm font-medium hover:underline"
                    >
                      Open source URL
                      <ExternalLink className="size-3.5" aria-hidden="true" />
                    </a>
                  ) : (
                    <p className="text-muted-foreground mt-5 text-sm">
                      No external URL: this source is the repository’s labelled
                      synthetic seed.
                    </p>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </>
  )
}
