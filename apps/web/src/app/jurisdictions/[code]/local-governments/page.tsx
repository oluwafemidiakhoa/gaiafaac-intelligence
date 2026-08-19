import Link from 'next/link'

import { DataUnavailable } from '@/components/data-unavailable'
import { PageHeader } from '@/components/page-header'
import { StatusPill } from '@/components/status-pill'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { formatDate, formatNaira } from '@/lib/format'
import { getPublishedLgasForState } from '@/lib/published-api'

export const dynamic = 'force-dynamic'

export default async function LocalGovernmentsPage({
  params,
}: {
  params: Promise<{ code: string }>
}) {
  const { code } = await params
  const stateCode = code.toUpperCase()
  const result = await getPublishedLgasForState(stateCode)

  if (!result.data) {
    return (
      <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
        <PageHeader
          eyebrow={`Local-government ledger · ${stateCode}`}
          title="Published LGA evidence unavailable"
          description="GaiaFAAC publishes individual local-government allocations only after the full OAGF Table IV batch passes validation, human review, and four-eyes publication."
        />
        <div className="mt-8">
          <DataUnavailable
            message={
              result.error ??
              'No governed local-government evidence is published for this jurisdiction yet.'
            }
          />
        </div>
      </div>
    )
  }

  const data = result.data

  return (
    <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
      <PageHeader
        eyebrow={`OAGF Table IV · ${data.state_code}`}
        title={`${data.state_name} local governments`}
        description="Individual observed allocations from published, human-verified OAGF Table IV evidence. No local-government value is estimated from the national aggregate."
      />

      <div className="mt-7 flex flex-wrap items-center gap-3">
        <StatusPill tone="success">Human verified</StatusPill>
        <span className="text-muted-foreground font-mono text-xs">
          {data.local_government_count} published local-government jurisdictions
        </span>
      </div>

      <div className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {data.local_governments.map((lga) => (
          <Link
            key={lga.local_government_slug}
            href={`/jurisdictions/${data.state_code}/local-governments/${lga.local_government_slug}`}
            className="group"
          >
            <Card className="group-hover:border-primary/40 h-full transition-colors">
              <CardHeader>
                <CardTitle className="text-base">
                  {lga.local_government_name}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <p className="text-muted-foreground text-xs">Latest total net</p>
                  <p className="mt-1 font-mono text-lg font-semibold">
                    {formatNaira(lga.total_net_allocation)}
                  </p>
                </div>
                <div className="text-muted-foreground text-xs">
                  Disbursement {formatDate(lga.disbursement_month)} · Table IV
                  {lga.source_page ? ` · p. ${lga.source_page}` : ''}
                </div>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  )
}
