import type { Metadata } from 'next'

import { DataUnavailable } from '@/components/data-unavailable'
import { DemoBanner } from '@/components/demo-banner'
import { PageHeader } from '@/components/page-header'
import { StatusPill } from '@/components/status-pill'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { getDemoComparison, getDemoStates } from '@/lib/demo-api'
import { formatNaira, humanize } from '@/lib/format'

export const metadata: Metadata = { title: 'Compare states' }
export const dynamic = 'force-dynamic'

function selectedSlugs(value: string | string[] | undefined): string[] {
  if (Array.isArray(value)) return [...new Set(value)]
  if (value) return [value]
  return ['lagos', 'kano']
}

export default async function ComparePage({
  searchParams,
}: {
  searchParams: Promise<{ states?: string | string[] }>
}) {
  const query = await searchParams
  const selected = selectedSlugs(query.states)
  const selectionIsValid = selected.length >= 2 && selected.length <= 6
  const [directory, comparison] = await Promise.all([
    getDemoStates(),
    selectionIsValid ? getDemoComparison(selected) : Promise.resolve(null),
  ])

  return (
    <>
      <DemoBanner note="Comparisons use only available synthetic rows; missing values remain unavailable." />
      <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
        <PageHeader
          eyebrow="State comparison"
          title="Compare without filling the gaps"
          description="Select two to six states. Only three jurisdictions have demo allocations, so unavailable comparisons are shown honestly."
        />

        {directory.data === null ? (
          <div className="mt-10">
            <DataUnavailable
              message={directory.error ?? 'The state directory is unavailable.'}
            />
          </div>
        ) : (
          <>
            <Card className="mt-10">
              <CardHeader>
                <CardTitle>Choose jurisdictions</CardTitle>
                <CardDescription>
                  Select between two and six states, then update the comparison.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form>
                  <fieldset className="grid max-h-72 gap-2 overflow-y-auto rounded-lg border p-4 sm:grid-cols-2 lg:grid-cols-3">
                    <legend className="sr-only">States to compare</legend>
                    {directory.data.states.map((state) => (
                      <label
                        key={state.code}
                        className="hover:bg-muted flex cursor-pointer items-center gap-3 rounded-md px-3 py-2 text-sm"
                      >
                        <input
                          type="checkbox"
                          name="states"
                          value={state.slug}
                          defaultChecked={selected.includes(state.slug)}
                          className="accent-primary size-4"
                        />
                        <span className="flex-1">{state.name}</span>
                        {state.has_demo_allocation ? (
                          <span className="text-amber-800 text-xs">demo</span>
                        ) : null}
                      </label>
                    ))}
                  </fieldset>
                  <div className="mt-4 flex items-center gap-4">
                    <Button type="submit">Update comparison</Button>
                    <p className="text-muted-foreground text-sm">
                      {selected.length} selected
                    </p>
                  </div>
                </form>
              </CardContent>
            </Card>

            {!selectionIsValid ? (
              <div className="mt-8">
                <DataUnavailable message="Select between two and six unique states." />
              </div>
            ) : comparison?.data === null || comparison === null ? (
              <div className="mt-8">
                <DataUnavailable
                  message={
                    comparison?.error ?? 'The comparison service is unavailable.'
                  }
                />
              </div>
            ) : (
              <Card className="mt-8">
                <CardHeader>
                  <CardTitle>Demo comparison</CardTitle>
                  <CardDescription>{comparison.data.scope_note}</CardDescription>
                </CardHeader>
                <CardContent className="overflow-x-auto">
                  <table className="w-full min-w-3xl border-collapse text-left text-sm">
                    <thead>
                      <tr className="border-border border-b">
                        <th className="py-3 pr-5 font-medium">State</th>
                        <th className="py-3 pr-5 font-medium">Gross</th>
                        <th className="py-3 pr-5 font-medium">Deductions</th>
                        <th className="py-3 pr-5 font-medium">Net</th>
                        <th className="py-3 font-medium">Availability</th>
                      </tr>
                    </thead>
                    <tbody>
                      {comparison.data.states.map((item) => (
                        <tr
                          key={item.state.code}
                          className="border-border border-b last:border-0"
                        >
                          <td className="py-4 pr-5">
                            <p className="font-medium">{item.state.name}</p>
                            <p className="text-muted-foreground mt-1 text-xs">
                              {item.state.geopolitical_zone}
                            </p>
                          </td>
                          <td className="py-4 pr-5 font-mono">
                            {formatNaira(item.allocation?.gross_total ?? null)}
                          </td>
                          <td className="py-4 pr-5 font-mono">
                            {formatNaira(
                              item.allocation?.total_deductions ?? null,
                            )}
                          </td>
                          <td className="py-4 pr-5 font-mono font-semibold">
                            {formatNaira(item.allocation?.net_allocation ?? null)}
                          </td>
                          <td className="py-4">
                            <StatusPill
                              tone={item.allocation ? 'demo' : 'neutral'}
                            >
                              {item.allocation
                                ? humanize(
                                    item.allocation.verification_status,
                                  )
                                : 'Unavailable'}
                            </StatusPill>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </CardContent>
              </Card>
            )}
          </>
        )}
      </div>
    </>
  )
}
