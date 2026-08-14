import type { Metadata } from 'next'

import { DataUnavailable } from '@/components/data-unavailable'
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
import { formatNaira } from '@/lib/format'
import { getFiscalIntelligenceComparison } from '@/lib/fiscal-ledger-api'
import { getPublishedOverview } from '@/lib/published-api'

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
  const result = await getPublishedOverview()
  const data = result.data
  const directory = data
    ? [...data.allocations].sort((a, b) =>
        a.state_name.localeCompare(b.state_name),
      )
    : []
  const compared = data
    ? directory.filter((a) => selected.includes(a.state_slug))
    : []
  const intelligenceResult =
    selectionIsValid && compared.length === selected.length
      ? await getFiscalIntelligenceComparison(
          compared.map((state) => `NG-${state.state_code}`),
        )
      : { data: null, error: null }

  return (
    <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
      <PageHeader
        eyebrow="State comparison"
        title="Compare on verified figures"
        description="Select two to six jurisdictions from the latest verified FAAC month. Every figure traces to the official OAGF source; unavailable values stay blank."
      />

      {data === null ? (
        <div className="mt-10">
          <DataUnavailable
            message={result.error ?? 'No verified month is published yet.'}
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
                  {directory.map((state) => (
                    <label
                      key={state.state_code}
                      className="hover:bg-muted flex cursor-pointer items-center gap-3 rounded-md px-3 py-2 text-sm"
                    >
                      <input
                        type="checkbox"
                        name="states"
                        value={state.state_slug}
                        defaultChecked={selected.includes(state.state_slug)}
                        className="accent-primary size-4"
                      />
                      <span className="flex-1">{state.state_name}</span>
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
          ) : (
            <Card className="mt-8">
              <CardHeader>
                <CardTitle>Comparison</CardTitle>
                <CardDescription>{data.period.reporting_label}</CardDescription>
              </CardHeader>
              <CardContent className="overflow-x-auto">
                <table className="w-full min-w-3xl border-collapse text-left text-sm">
                  <thead>
                    <tr className="border-border border-b">
                      <th className="py-3 pr-5 font-medium">State</th>
                      <th className="py-3 pr-5 font-medium">Gross</th>
                      <th className="py-3 pr-5 font-medium">Deductions</th>
                      <th className="py-3 pr-5 font-medium">Net</th>
                      <th className="py-3 font-medium">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {compared.map((item) => (
                      <tr
                        key={item.state_code}
                        className="border-border border-b last:border-0"
                      >
                        <td className="py-4 pr-5">
                          <p className="font-medium">{item.state_name}</p>
                          <p className="text-muted-foreground mt-1 text-xs">
                            {item.geopolitical_zone}
                          </p>
                        </td>
                        <td className="py-4 pr-5 font-mono">
                          {formatNaira(item.gross_total)}
                        </td>
                        <td className="py-4 pr-5 font-mono">
                          {formatNaira(item.total_deductions)}
                        </td>
                        <td className="py-4 pr-5 font-mono font-semibold">
                          {formatNaira(item.net_allocation)}
                        </td>
                        <td className="py-4">
                          <StatusPill tone="success">Verified</StatusPill>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </CardContent>
            </Card>
          )}
          {selectionIsValid && intelligenceResult.data ? (
            <Card className="mt-8">
              <CardHeader>
                <CardTitle>Fiscal State intelligence</CardTitle>
                <CardDescription>
                  Deterministic metrics from immutable Fiscal States. Missing
                  evidence remains unavailable; jurisdictions are not ranked.
                </CardDescription>
              </CardHeader>
              <CardContent className="overflow-x-auto">
                <table className="w-full min-w-4xl text-left text-sm">
                  <thead>
                    <tr className="border-border border-b">
                      <th className="py-3 pr-5 font-medium">Jurisdiction</th>
                      <th className="py-3 pr-5 font-medium">Period</th>
                      <th className="py-3 pr-5 font-medium">Monthly change</th>
                      <th className="py-3 pr-5 font-medium">Momentum</th>
                      <th className="py-3 font-medium">Volatility</th>
                    </tr>
                  </thead>
                  <tbody>
                    {intelligenceResult.data.data.jurisdictions.map((item) => {
                      const metric = (key: string) =>
                        item.metrics.find((entry) => entry.key === key)
                          ?.value ?? 'Unavailable'
                      return (
                        <tr
                          key={item.fiscal_state_id}
                          className="border-border border-b last:border-0"
                        >
                          <td className="py-4 pr-5 font-medium">
                            {item.jurisdiction.name}
                          </td>
                          <td className="py-4 pr-5 font-mono">
                            {item.fiscal_period}
                          </td>
                          <td className="py-4 pr-5 font-mono">
                            {metric('faac_month_over_month_change')}
                          </td>
                          <td className="py-4 pr-5 font-mono">
                            {metric('faac_momentum')}
                          </td>
                          <td className="py-4 font-mono">
                            {metric('faac_volatility')}
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </CardContent>
            </Card>
          ) : null}
        </>
      )}
    </div>
  )
}
