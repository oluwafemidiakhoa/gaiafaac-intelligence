import type { Metadata } from 'next'
import Link from 'next/link'

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
import { fiscalDesignBriefFingerprint } from '@/lib/fiscal-design-brief-integrity'
import { getFiscalDesign } from '@/lib/fiscal-design-api'
import { formatNaira } from '@/lib/format'

export const metadata: Metadata = { title: 'Fiscal Design Lab' }
export const dynamic = 'force-dynamic'

interface FiscalDesignPageProps {
  searchParams: Promise<{
    state?: string
    year?: string
    faacShock?: string
    igrShock?: string
    reserveShare?: string
    objective?: string
  }>
}

function bounded(
  value: string | undefined,
  fallback: number,
  min: number,
  max: number,
) {
  const parsed = Number(value)
  return Number.isFinite(parsed) && parsed >= min && parsed <= max
    ? parsed
    : fallback
}

export default async function FiscalDesignPage({
  searchParams,
}: FiscalDesignPageProps) {
  const query = await searchParams
  const state = (query.state ?? '').trim().toLowerCase()
  const year = Math.trunc(
    bounded(query.year, new Date().getUTCFullYear(), 2000, 2100),
  )
  const faacShock = bounded(query.faacShock, -20, -100, 100)
  const igrShock = bounded(query.igrShock, 0, -100, 100)
  const reserveShare = bounded(query.reserveShare, 10, 0, 100)
  const objective = (query.objective ?? '').trim().slice(0, 240)
  const result = state
    ? await getFiscalDesign(state, year, faacShock, igrShock, reserveShare)
    : { data: null, error: null }
  const latestComparableYear = result.data?.latest_comparable_year ?? null
  const comparableYearParams =
    result.data &&
    latestComparableYear !== null &&
    latestComparableYear !== year &&
    (!result.data.faac_complete_year || !result.data.annual_igr_available)
      ? new URLSearchParams({
          state,
          year: String(latestComparableYear),
          faacShock: String(faacShock),
          igrShock: String(igrShock),
          reserveShare: String(reserveShare),
        })
      : null
  if (comparableYearParams && objective) {
    comparableYearParams.set('objective', objective)
  }
  const comparableYearHref = comparableYearParams
    ? `/fiscal-design?${comparableYearParams.toString()}`
    : null
  const briefParams = result.data
    ? new URLSearchParams({
        state,
        year: String(year),
        faacShock: String(faacShock),
        igrShock: String(igrShock),
        reserveShare: String(reserveShare),
        fingerprint: fiscalDesignBriefFingerprint(result.data, objective),
      })
    : null
  if (briefParams && objective) {
    briefParams.set('objective', objective)
  }
  const briefHref = briefParams
    ? `/fiscal-design/brief?${briefParams.toString()}`
    : null

  return (
    <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
      <PageHeader
        eyebrow="Gaia Fiscal Design Lab · v0"
        title="Stress-test fiscal ideas against governed evidence"
        description="Explore hypothetical FAAC and IGR resilience scenarios with deterministic arithmetic, exact-year evidence boundaries, and source provenance. Gaia does not fill missing periods or present scenario assumptions as reported facts."
      />

      <Card className="mt-8">
        <CardHeader>
          <CardTitle>Scenario inputs</CardTitle>
          <CardDescription>
            Enter a state slug and explicit assumptions. Negative percentages
            model declines; positive percentages model increases.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form className="grid gap-4 md:grid-cols-5" method="get">
            <label className="text-sm font-medium">
              State slug
              <input
                name="state"
                defaultValue={state}
                placeholder="lagos"
                className="border-input bg-background mt-2 h-10 w-full rounded-md border px-3 text-sm"
                required
              />
            </label>
            <label className="text-sm font-medium">
              Year
              <input
                name="year"
                type="number"
                min="2000"
                max="2100"
                defaultValue={year}
                className="border-input bg-background mt-2 h-10 w-full rounded-md border px-3 text-sm"
              />
            </label>
            <label className="text-sm font-medium">
              FAAC change %
              <input
                name="faacShock"
                type="number"
                min="-100"
                max="100"
                step="0.1"
                defaultValue={faacShock}
                className="border-input bg-background mt-2 h-10 w-full rounded-md border px-3 text-sm"
              />
            </label>
            <label className="text-sm font-medium">
              IGR change %
              <input
                name="igrShock"
                type="number"
                min="-100"
                max="100"
                step="0.1"
                defaultValue={igrShock}
                className="border-input bg-background mt-2 h-10 w-full rounded-md border px-3 text-sm"
              />
            </label>
            <label className="text-sm font-medium">
              IGR buffer %
              <input
                name="reserveShare"
                type="number"
                min="0"
                max="100"
                step="0.1"
                defaultValue={reserveShare}
                className="border-input bg-background mt-2 h-10 w-full rounded-md border px-3 text-sm"
              />
            </label>
            <label className="text-sm font-medium md:col-span-5">
              Research objective (optional)
              <input
                name="objective"
                defaultValue={objective}
                maxLength={240}
                placeholder="Assess revenue resilience under a FAAC decline"
                className="border-input bg-background mt-2 h-10 w-full rounded-md border px-3 text-sm"
              />
            </label>
            <div className="md:col-span-5">
              <Button type="submit">Run fiscal scenarios</Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {!state ? (
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>Start with a governed evidence boundary</CardTitle>
            <CardDescription>
              Example: use <span className="font-mono">lagos</span>, choose a
              year, then test explicit revenue shocks.
            </CardDescription>
          </CardHeader>
        </Card>
      ) : null}

      {state && !result.data ? (
        <div className="mt-6">
          <DataUnavailable
            message={result.error ?? 'No governed evidence is available.'}
          />
        </div>
      ) : null}

      {result.data ? (
        <>
          <div className="mt-8 flex flex-wrap items-center gap-3">
            <StatusPill
              tone={result.data.faac_complete_year ? 'success' : 'neutral'}
            >
              {result.data.faac_complete_year
                ? 'Complete FAAC year'
                : 'Partial FAAC year'}
            </StatusPill>
            <StatusPill
              tone={result.data.annual_igr_available ? 'success' : 'neutral'}
            >
              {result.data.annual_igr_available
                ? 'Annual IGR available'
                : 'Annual IGR unavailable'}
            </StatusPill>
            <span className="text-muted-foreground text-sm">
              {result.data.coverage_label}
            </span>
          </div>

          {briefHref ? (
            <div className="mt-4 flex flex-wrap gap-3">
              <Button asChild variant="outline">
                <Link href={briefHref}>Open research brief</Link>
              </Button>
              <Button asChild variant="outline">
                <Link href="/fiscal-design/verify">
                  Verify evidence manifest
                </Link>
              </Button>
            </div>
          ) : null}

          {comparableYearHref && latestComparableYear !== null ? (
            <Card className="mt-6 border-dashed">
              <CardHeader>
                <CardTitle>Use the latest comparable year</CardTitle>
                <CardDescription>
                  {year} does not yet have both a complete 12-month FAAC series
                  and published annual IGR for {result.data.state_name}. The
                  latest year that satisfies both evidence requirements is{' '}
                  {latestComparableYear}.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Button asChild variant="outline">
                  <Link href={comparableYearHref}>
                    Run {latestComparableYear} comparable year
                  </Link>
                </Button>
              </CardContent>
            </Card>
          ) : null}

          <section className="mt-6 grid gap-5 lg:grid-cols-3">
            {result.data.candidates.map((candidate) => (
              <Card key={candidate.key}>
                <CardHeader>
                  <div className="mb-2">
                    <StatusPill
                      tone={
                        candidate.status === 'available' ? 'success' : 'neutral'
                      }
                    >
                      {candidate.status === 'available'
                        ? 'Available'
                        : 'Insufficient data'}
                    </StatusPill>
                  </div>
                  <CardTitle>{candidate.title}</CardTitle>
                  <CardDescription>{candidate.purpose}</CardDescription>
                </CardHeader>
                <CardContent>
                  {candidate.metrics.length > 0 ? (
                    <div className="space-y-4">
                      {candidate.metrics.map((metric) => (
                        <div key={metric.label}>
                          <p className="text-muted-foreground text-xs tracking-wide uppercase">
                            {metric.label}
                          </p>
                          <p className="mt-1 text-xl font-semibold">
                            {metric.unit === 'NGN'
                              ? formatNaira(metric.value)
                              : `${metric.value} ${metric.unit}`}
                          </p>
                        </div>
                      ))}
                    </div>
                  ) : null}
                  <p className="text-muted-foreground mt-5 text-sm leading-6">
                    {candidate.note}
                  </p>
                </CardContent>
              </Card>
            ))}
          </section>

          <div className="mt-8 grid gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Assumptions</CardTitle>
                <CardDescription>
                  Scenario parameters are explicit and kept separate from
                  evidence.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2 text-sm">
                  {result.data.assumptions.map((assumption) => (
                    <li key={assumption}>• {assumption}</li>
                  ))}
                </ul>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Evidence chain</CardTitle>
                <CardDescription>
                  {result.data.evidence.length} governed evidence records used.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {result.data.evidence.map((item) => (
                  <div
                    key={`${item.evidence_domain}-${item.label}`}
                    className="border-border rounded-lg border p-3 text-sm"
                  >
                    <div className="flex items-center justify-between gap-3">
                      <p className="font-medium">{item.label}</p>
                      <span className="bg-muted rounded-full px-2 py-1 text-xs font-medium tracking-wide uppercase">
                        {item.evidence_domain}
                      </span>
                    </div>
                    <p className="mt-2">
                      {item.value === 'Unavailable'
                        ? item.value
                        : formatNaira(item.value)}
                    </p>
                    <p className="text-muted-foreground mt-1">
                      {item.source_organization}
                    </p>
                    <p className="text-muted-foreground mt-1 font-mono text-xs break-all">
                      SHA-256 {item.source_sha256}
                    </p>
                    <Link
                      href={item.reference_path}
                      className="text-primary mt-2 inline-block font-medium hover:underline"
                    >
                      Open evidence →
                    </Link>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>

          <p className="text-muted-foreground mt-8 text-xs leading-5">
            {result.data.disclaimer}
          </p>
        </>
      ) : null}
    </div>
  )
}
