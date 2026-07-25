import type { Metadata } from 'next'
import Link from 'next/link'

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
import { getDemoStates } from '@/lib/demo-api'
import { formatNaira } from '@/lib/format'

export const metadata: Metadata = { title: 'States' }
export const dynamic = 'force-dynamic'

export default async function StatesPage() {
  const result = await getDemoStates()

  return (
    <>
      <DemoBanner />
      <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
        <PageHeader
          eyebrow="36 states + FCT"
          title="State directory"
          description="Every jurisdiction is listed. Only Lagos, Kano, and Rivers have synthetic demo allocations; all other values remain unavailable."
        />

        {result.data === null ? (
          <div className="mt-10">
            <DataUnavailable
              message={result.error ?? 'The state directory is unavailable.'}
            />
          </div>
        ) : (
          <Card className="mt-10">
            <CardHeader>
              <CardTitle>Jurisdictions</CardTitle>
              <CardDescription>
                Availability refers only to the labelled demo period.
              </CardDescription>
            </CardHeader>
            <CardContent className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {result.data.states.map((state) => (
                <Link
                  key={state.code}
                  href={`/states/${state.slug}`}
                  className="border-border hover:border-primary/40 rounded-lg border p-4 transition-colors"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="font-medium">{state.name}</p>
                      <p className="text-muted-foreground mt-1 text-xs">
                        {state.capital} · {state.geopolitical_zone}
                      </p>
                    </div>
                    <span className="text-muted-foreground font-mono text-xs">
                      {state.code}
                    </span>
                  </div>
                  <div className="mt-4 flex items-end justify-between gap-3">
                    <p className="font-mono text-sm font-semibold">
                      {formatNaira(state.demo_net_allocation)}
                    </p>
                    <StatusPill
                      tone={state.has_demo_allocation ? 'demo' : 'neutral'}
                    >
                      {state.has_demo_allocation ? 'Demo row' : 'Unavailable'}
                    </StatusPill>
                  </div>
                </Link>
              ))}
            </CardContent>
          </Card>
        )}
      </div>
    </>
  )
}
