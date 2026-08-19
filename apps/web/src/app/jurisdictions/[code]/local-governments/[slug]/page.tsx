import Link from 'next/link'

import { DataUnavailable } from '@/components/data-unavailable'
import { PageHeader } from '@/components/page-header'
import { StatusPill } from '@/components/status-pill'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { formatDate, formatNaira } from '@/lib/format'
import { getPublishedLgaHistory } from '@/lib/published-api'

export const dynamic = 'force-dynamic'

export default async function LocalGovernmentPage({
  params,
}: {
  params: Promise<{ code: string; slug: string }>
}) {
  const { code, slug } = await params
  const stateCode = code.toUpperCase()
  const result = await getPublishedLgaHistory(stateCode, slug)

  if (!result.data) {
    return (
      <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
        <PageHeader
          eyebrow={`Local-government ledger · ${stateCode}`}
          title="Published LGA evidence unavailable"
          description="No governed OAGF Table IV publication is available for this local government."
        />
        <div className="mt-8">
          <DataUnavailable
            message={
              result.error ??
              'No published allocation history exists for this local government.'
            }
          />
        </div>
      </div>
    )
  }

  const data = result.data
  const latest = data.allocations[0]

  return (
    <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
      <PageHeader
        eyebrow={`${data.state_name} · OAGF Table IV`}
        title={data.local_government_name}
        description="A governed history of observed local-government FAAC allocations, linked to the exact retained OAGF source document and SHA-256 fingerprint."
      />

      <div className="mt-7 flex flex-wrap items-center gap-3">
        <StatusPill tone="success">Human verified</StatusPill>
        <span className="text-muted-foreground font-mono text-xs">
          {data.record_count} published period
          {data.record_count === 1 ? '' : 's'}
        </span>
        <Button asChild variant="outline" size="sm">
          <Link href={`/jurisdictions/${data.state_code}/local-governments`}>
            All local governments
          </Link>
        </Button>
      </div>

      {latest ? (
        <div className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Latest total net</CardTitle>
            </CardHeader>
            <CardContent className="font-mono text-xl font-semibold">
              {formatNaira(latest.total_net_allocation)}
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Net statutory</CardTitle>
            </CardHeader>
            <CardContent className="font-mono text-xl font-semibold">
              {formatNaira(latest.net_statutory_allocation)}
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">VAT</CardTitle>
            </CardHeader>
            <CardContent className="font-mono text-xl font-semibold">
              {formatNaira(latest.vat_amount)}
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Disbursement month</CardTitle>
            </CardHeader>
            <CardContent className="font-mono text-lg font-semibold">
              {formatDate(latest.disbursement_month)}
            </CardContent>
          </Card>
        </div>
      ) : null}

      <section className="mt-10">
        <p className="text-primary font-mono text-xs font-semibold tracking-[0.18em] uppercase">
          Published history
        </p>
        <h2 className="mt-2 text-2xl font-semibold">
          Monthly allocation evidence
        </h2>

        <div className="mt-5 space-y-4">
          {data.allocations.map((allocation) => (
            <Card key={allocation.reporting_period_id}>
              <CardHeader>
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <CardTitle className="text-base">
                      {formatDate(allocation.disbursement_month)}
                    </CardTitle>
                    <p className="text-muted-foreground mt-1 text-xs">
                      {allocation.reporting_label}
                    </p>
                  </div>
                  <StatusPill tone="success">Published</StatusPill>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
                  <div>
                    <p className="text-muted-foreground text-xs">Total net</p>
                    <p className="mt-1 font-mono font-semibold">
                      {formatNaira(allocation.total_net_allocation)}
                    </p>
                  </div>
                  <div>
                    <p className="text-muted-foreground text-xs">Deductions</p>
                    <p className="mt-1 font-mono font-semibold">
                      {formatNaira(allocation.deduction_amount)}
                    </p>
                  </div>
                  <div>
                    <p className="text-muted-foreground text-xs">Net ecology</p>
                    <p className="mt-1 font-mono font-semibold">
                      {formatNaira(allocation.net_ecology_share)}
                    </p>
                  </div>
                  <div>
                    <p className="text-muted-foreground text-xs">VAT</p>
                    <p className="mt-1 font-mono font-semibold">
                      {formatNaira(allocation.vat_amount)}
                    </p>
                  </div>
                </div>

                <div className="border-border mt-5 border-t pt-4 text-xs">
                  <p className="font-medium">
                    {allocation.source.organization}
                  </p>
                  <p className="text-muted-foreground mt-1">
                    {allocation.source.original_filename} ·{' '}
                    {allocation.source_table}
                    {allocation.source_page
                      ? ` · page ${allocation.source_page}`
                      : ''}
                  </p>
                  <p className="text-muted-foreground mt-2 font-mono break-all">
                    SHA-256 {allocation.source.sha256}
                  </p>
                  {allocation.source.source_url ? (
                    <Button
                      asChild
                      variant="outline"
                      size="sm"
                      className="mt-3"
                    >
                      <a
                        href={allocation.source.source_url}
                        target="_blank"
                        rel="noreferrer"
                      >
                        Open official source
                      </a>
                    </Button>
                  ) : null}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>
    </div>
  )
}
