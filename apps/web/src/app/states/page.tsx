import type { Metadata } from 'next'
import Link from 'next/link'

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
import { formatNaira } from '@/lib/format'
import { getPublishedOverview } from '@/lib/published-api'

export const metadata: Metadata = { title: 'States' }
export const dynamic = 'force-dynamic'

export default async function StatesPage() {
  const result = await getPublishedOverview()
  const data = result.data
  const states = data
    ? [...data.allocations].sort((a, b) =>
        a.state_name.localeCompare(b.state_name),
      )
    : []

  return (
    <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
      <PageHeader
        eyebrow="36 states + FCT"
        title="State directory"
        description="Every jurisdiction in the latest verified FAAC month. Each figure traces to the official OAGF source; unavailable values are left blank, never inferred."
      />

      {data === null ? (
        <div className="mt-10">
          <DataUnavailable
            message={result.error ?? 'No verified month is published yet.'}
          />
        </div>
      ) : (
        <Card className="mt-10">
          <CardHeader>
            <CardTitle>Jurisdictions</CardTitle>
            <CardDescription>{data.period.reporting_label}</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {states.map((state) => (
              <Link
                key={state.state_code}
                href={`/states/${state.state_slug}`}
                className="border-border hover:border-primary/40 rounded-lg border p-4 transition-colors"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="font-medium">{state.state_name}</p>
                    <p className="text-muted-foreground mt-1 text-xs">
                      {state.geopolitical_zone}
                    </p>
                  </div>
                  <span className="text-muted-foreground font-mono text-xs">
                    {state.state_code}
                  </span>
                </div>
                <div className="mt-4 flex items-end justify-between gap-3">
                  <p className="font-mono text-sm font-semibold">
                    {formatNaira(state.net_allocation)}
                  </p>
                  <StatusPill tone="success">Verified</StatusPill>
                </div>
              </Link>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  )
}
