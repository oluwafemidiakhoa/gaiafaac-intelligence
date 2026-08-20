import type { Metadata } from 'next'

import { DataUnavailable } from '@/components/data-unavailable'
import { GaiaTerminalSearch } from '@/components/gaia-terminal-search'
import { PageHeader } from '@/components/page-header'
import { StatusPill } from '@/components/status-pill'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { formatDate, formatNaira } from '@/lib/format'
import { getPublishedOverview } from '@/lib/published-api'

export const metadata: Metadata = {
  title: 'Gaia Terminal',
  description:
    'Unified command surface for governed Nigerian fiscal evidence, jurisdiction research, reconciliation, monitoring and institutional workflows.',
}
export const dynamic = 'force-dynamic'

function compactNaira(value: string | null) {
  if (!value) return 'Unavailable'
  const amount = Number(value)
  if (!Number.isFinite(amount)) return formatNaira(value)
  if (Math.abs(amount) >= 1_000_000_000_000)
    return `₦${(amount / 1_000_000_000_000).toFixed(2)}T`
  if (Math.abs(amount) >= 1_000_000_000)
    return `₦${(amount / 1_000_000_000).toFixed(2)}B`
  return formatNaira(value)
}

export default async function GaiaTerminalPage() {
  const overview = await getPublishedOverview()
  const data = overview.data

  return (
    <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
      <div className="grid gap-8 xl:grid-cols-[1fr_19rem] xl:items-end">
        <PageHeader
          eyebrow="Gaia Terminal"
          title="One command surface for Nigeria’s fiscal evidence."
          description="Search governed jurisdictions, jump into proofs and local-government evidence, ask the verified ledger, inspect revisions and reconciliation, run scenarios, monitor signals and create institutional decision material without leaving the evidence boundary."
        />

        <Card className="bg-muted/25">
          <CardHeader>
            <div className="flex items-center justify-between gap-3">
              <CardTitle className="text-base">Evidence boundary</CardTitle>
              <StatusPill tone="success">Fail closed</StatusPill>
            </div>
            <CardDescription>
              Terminal search never synthesizes a missing jurisdiction or fiscal value.
            </CardDescription>
          </CardHeader>
        </Card>
      </div>

      {data ? (
        <>
          <section className="mt-9 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-muted-foreground text-sm font-medium">
                  Latest verified period
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="font-mono text-lg font-semibold">
                  {formatDate(data.period.revenue_month)}
                </p>
                <p className="text-muted-foreground mt-2 text-xs">
                  {data.period.reporting_label}
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="text-muted-foreground text-sm font-medium">
                  State-ledger net total
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="font-mono text-2xl font-semibold">
                  {compactNaira(data.total_net)}
                </p>
                <p className="text-muted-foreground mt-2 text-xs">
                  Published governed jurisdiction records only
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="text-muted-foreground text-sm font-medium">
                  Jurisdiction coverage
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="font-mono text-2xl font-semibold">
                  {data.covered_states}/{data.expected_states}
                </p>
                <p className="text-muted-foreground mt-2 text-xs">
                  Missing jurisdictions remain unavailable
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="text-muted-foreground text-sm font-medium">
                  Source fingerprint
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="font-mono text-xs leading-5 break-all">
                  {data.source.sha256}
                </p>
              </CardContent>
            </Card>
          </section>

          <section className="mt-9 rounded-2xl border border-emerald-950/10 bg-[radial-gradient(circle_at_top_left,rgba(16,185,129,0.10),transparent_30%)] p-5 sm:p-7">
            <GaiaTerminalSearch
              jurisdictions={data.allocations}
              periodLabel={data.period.reporting_label}
            />
          </section>
        </>
      ) : (
        <div className="mt-9">
          <DataUnavailable
            message={
              overview.error ??
              'No governed published jurisdiction ledger is available for Gaia Terminal.'
            }
          />
        </div>
      )}
    </div>
  )
}
