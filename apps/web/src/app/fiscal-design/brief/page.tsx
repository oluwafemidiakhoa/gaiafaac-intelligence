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
import { getFiscalDesign } from '@/lib/fiscal-design-api'
import { formatNaira } from '@/lib/format'

export const metadata: Metadata = { title: 'Fiscal Design Research Brief' }
export const dynamic = 'force-dynamic'

interface FiscalDesignBriefPageProps {
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

export default async function FiscalDesignBriefPage({
  searchParams,
}: FiscalDesignBriefPageProps) {
  const query = await searchParams
  const state = (query.state ?? '').trim().toLowerCase()
  const year = Math.trunc(
    bounded(query.year, new Date().getUTCFullYear(), 2000, 2100),
  )
  const faacShock = bounded(query.faacShock, -20, -100, 100)
  const igrShock = bounded(query.igrShock, 0, -100, 100)
  const reserveShare = bounded(query.reserveShare, 10, 0, 100)
  const researchObjective = (query.objective ?? '').trim().slice(0, 240)
  const result = state
    ? await getFiscalDesign(state, year, faacShock, igrShock, reserveShare)
    : { data: null, error: 'Select a state in Fiscal Design Lab first.' }

  const backParams = new URLSearchParams({
    state,
    year: String(year),
    faacShock: String(faacShock),
    igrShock: String(igrShock),
    reserveShare: String(reserveShare),
  })
  if (researchObjective) {
    backParams.set('objective', researchObjective)
  }

  if (!result.data) {
    return (
      <div className="mx-auto max-w-5xl px-5 py-12 lg:px-8 lg:py-16">
        <PageHeader
          eyebrow="Gaia Fiscal Design Lab"
          title="Fiscal Design Research Brief"
          description="A shareable evidence-grounded summary of a Fiscal Design scenario run."
        />
        <div className="mt-8">
          <DataUnavailable
            message={result.error ?? 'No governed fiscal design is available.'}
          />
        </div>
        <div className="mt-6">
          <Button asChild variant="outline">
            <Link href="/fiscal-design">Return to Fiscal Design Lab</Link>
          </Button>
        </div>
      </div>
    )
  }

  const design = result.data

  return (
    <div className="mx-auto max-w-5xl px-5 py-12 lg:px-8 lg:py-16">
      <PageHeader
        eyebrow={`Gaia Fiscal Design Research Brief · ${design.design_version}`}
        title={`${design.state_name} · ${design.year}`}
        description="A governed research artifact built from the same deterministic scenario response shown in Fiscal Design Lab."
      />

      <div className="mt-6 flex flex-wrap gap-3 print:hidden">
        <Button asChild variant="outline">
          <Link href={`/fiscal-design?${backParams.toString()}`}>
            Back to Fiscal Design Lab
          </Link>
        </Button>
        <p className="text-muted-foreground self-center text-sm">
          Use your browser print command to print or save this brief as PDF.
        </p>
      </div>

      <Card className="mt-8">
        <CardHeader>
          <CardTitle>Research objective</CardTitle>
          <CardDescription>
            User context is displayed separately from governed evidence and
            scenario arithmetic.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm leading-6">
            {researchObjective || design.objective}
          </p>
        </CardContent>
      </Card>

      <div className="mt-6 grid gap-4 sm:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">FAAC coverage</CardTitle>
          </CardHeader>
          <CardContent>
            <StatusPill
              tone={design.faac_complete_year ? 'success' : 'neutral'}
            >
              {design.faac_complete_year
                ? 'Complete 12-month year'
                : `${design.faac_months_published} published months`}
            </StatusPill>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Annual IGR</CardTitle>
          </CardHeader>
          <CardContent>
            <StatusPill
              tone={design.annual_igr_available ? 'success' : 'neutral'}
            >
              {design.annual_igr_available ? 'Available' : 'Unavailable'}
            </StatusPill>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Evidence boundary</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm leading-6">{design.coverage_label}</p>
          </CardContent>
        </Card>
      </div>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Explicit assumptions</CardTitle>
          <CardDescription>
            These are scenario parameters, not reported fiscal facts.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2 text-sm">
            {design.assumptions.map((assumption) => (
              <li key={assumption}>• {assumption}</li>
            ))}
          </ul>
        </CardContent>
      </Card>

      <section className="mt-6 space-y-4">
        <div>
          <h2 className="text-2xl font-semibold">Scenario results</h2>
          <p className="text-muted-foreground mt-1 text-sm">
            Available and blocked scenarios are both retained so the brief does
            not hide evidence limitations.
          </p>
        </div>
        {design.candidates.map((candidate) => (
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
                <div className="grid gap-4 sm:grid-cols-3">
                  {candidate.metrics.map((metric) => (
                    <div key={metric.label}>
                      <p className="text-muted-foreground text-xs tracking-wide uppercase">
                        {metric.label}
                      </p>
                      <p className="mt-1 text-lg font-semibold">
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

      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Governed evidence chain</CardTitle>
          <CardDescription>
            {design.evidence.length} source-linked records support this brief.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {design.evidence.map((item) => (
            <div
              key={`${item.evidence_domain}-${item.label}`}
              className="border-border rounded-lg border p-3 text-sm"
            >
              <div className="flex flex-wrap items-center justify-between gap-3">
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
                className="text-primary mt-2 inline-block font-medium hover:underline print:hidden"
              >
                Open evidence →
              </Link>
            </div>
          ))}
        </CardContent>
      </Card>

      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Interpretation boundary</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-sm leading-6">
            {design.disclaimer}
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
