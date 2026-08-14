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
import {
  getFiscalEvents,
  getJurisdictionEvidenceSources,
  getJurisdictionFiscalState,
  getJurisdictionFiscalIntelligence,
} from '@/lib/fiscal-ledger-api'
import { formatDate, formatNaira, humanize } from '@/lib/format'

export const dynamic = 'force-dynamic'

export async function generateMetadata({
  params,
}: {
  params: Promise<{ code: string }>
}): Promise<Metadata> {
  const { code } = await params
  return { title: `Fiscal State · ${code.toUpperCase()}` }
}

function displayClaimValue(claim: {
  value: string | null
  currency: string | null
  unit: string
}) {
  if (claim.value === null) return 'Unavailable'
  return claim.currency === 'NGN'
    ? formatNaira(claim.value)
    : `${claim.value} ${claim.unit}`
}

export default async function JurisdictionFiscalStatePage({
  params,
}: {
  params: Promise<{ code: string }>
}) {
  const { code } = await params
  const canonicalCode = code.toUpperCase()
  const [stateResult, eventResult, sourceResult, intelligenceResult] =
    await Promise.all([
      getJurisdictionFiscalState(canonicalCode),
      getFiscalEvents({ jurisdiction: canonicalCode }),
      getJurisdictionEvidenceSources(canonicalCode),
      getJurisdictionFiscalIntelligence(canonicalCode),
    ])

  if (!stateResult.data) {
    return (
      <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
        <PageHeader
          eyebrow={`Jurisdiction ledger · ${canonicalCode}`}
          title="Fiscal State unavailable"
          description="Gaia has not published an evidence-backed Fiscal State for this jurisdiction."
        />
        <div className="mt-8">
          <DataUnavailable message="No immutable Fiscal State is currently published for this jurisdiction." />
        </div>
      </div>
    )
  }

  const fiscalState = stateResult.data.data
  const events = eventResult.data?.data ?? []
  const sources = sourceResult.data?.data ?? []
  const materialEvent = events.find((event) => event.severity === 'material')
  const integrityScore = fiscalState.evidence_integrity.score
  const coverage = fiscalState.evidence_coverage
    ? `${(Number(fiscalState.evidence_coverage) * 100).toFixed(2)}%`
    : 'Insufficient evidence'
  const missingDomains = Object.entries(fiscalState.domains)
    .filter(([, domain]) => domain.status === 'unavailable')
    .map(([name]) => name)

  return (
    <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
      <PageHeader
        eyebrow={`Jurisdiction fiscal ledger · ${fiscalState.jurisdiction.code}`}
        title={fiscalState.jurisdiction.name.toUpperCase()}
        description="A point-in-time, evidence-backed view. Every available metric links to its immutable proof; unsupported domains remain unavailable."
      />

      <div className="mt-7 flex flex-wrap items-center gap-3">
        <StatusPill
          tone={
            fiscalState.ledger_status === 'verified' ? 'success' : 'neutral'
          }
        >
          Ledger {humanize(fiscalState.ledger_status)}
        </StatusPill>
        <span className="text-muted-foreground font-mono text-xs">
          Effective {formatDate(fiscalState.effective_at.slice(0, 10))}
        </span>
      </div>

      <div className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {[
          ['Fiscal State', fiscalState.fiscal_state_id, 'text-sm break-all'],
          ['Evidence coverage', coverage, 'text-2xl'],
          [
            'Evidence integrity',
            typeof integrityScore === 'string'
              ? `${integrityScore} / 100`
              : 'Insufficient evidence',
            'text-2xl',
          ],
          ['Fiscal period', fiscalState.fiscal_period, 'text-2xl'],
        ].map(([label, value, size]) => (
          <Link
            key={label}
            href={`/jurisdictions/${canonicalCode}/manifest`}
            className="group"
          >
            <Card className="group-hover:border-primary/40 h-full transition-colors">
              <CardHeader>
                <CardTitle className="text-sm">{label}</CardTitle>
              </CardHeader>
              <CardContent className={`font-mono font-semibold ${size}`}>
                {value}
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>

      <section className="mt-10">
        <div className="flex items-end justify-between gap-4">
          <div>
            <p className="text-primary font-mono text-xs font-semibold tracking-[0.18em] uppercase">
              Evidence domains
            </p>
            <h2 className="mt-2 text-2xl font-semibold">Published claims</h2>
          </div>
        </div>
        <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {Object.entries(fiscalState.domains).map(([name, domain]) => (
            <Card key={name}>
              <CardHeader>
                <div className="flex items-center justify-between gap-3">
                  <CardTitle className="text-base capitalize">
                    {humanize(name)}
                  </CardTitle>
                  <StatusPill
                    tone={domain.status === 'verified' ? 'success' : 'neutral'}
                  >
                    {humanize(domain.status)}
                  </StatusPill>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {domain.claims.length ? (
                  domain.claims.map((claim) => (
                    <Link
                      key={claim.gaia_id}
                      href={`/proofs/${encodeURIComponent(claim.gaia_id)}`}
                      className="border-border hover:border-primary block rounded-md border p-3 transition-colors"
                    >
                      <p className="text-muted-foreground text-xs">
                        {humanize(claim.metric)} · {claim.fiscal_period}
                      </p>
                      <p className="mt-2 font-mono font-semibold">
                        {displayClaimValue(claim)}
                      </p>
                      <p className="text-primary mt-2 font-mono text-[0.65rem] break-all">
                        {claim.gaia_id}
                      </p>
                    </Link>
                  ))
                ) : (
                  <p className="text-muted-foreground text-sm">
                    Unavailable. No value has been substituted or inferred.
                  </p>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      {intelligenceResult.data ? (
        <section className="mt-10">
          <p className="text-primary font-mono text-xs font-semibold tracking-[0.18em] uppercase">
            Derived intelligence
          </p>
          <h2 className="mt-2 text-2xl font-semibold">Deterministic metrics</h2>
          <p className="text-muted-foreground mt-2 text-sm">
            Exact calculations over verified claims. Insufficient evidence is
            never converted to zero or an estimate.
          </p>
          <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {intelligenceResult.data.data.metrics.map((metric) => (
              <Card key={metric.key}>
                <CardHeader>
                  <CardTitle className="text-base">{metric.label}</CardTitle>
                  <CardDescription>
                    {metric.fiscal_period ?? 'Period unavailable'}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="font-mono text-xl font-semibold">
                    {metric.value === null
                      ? 'Insufficient evidence'
                      : metric.unit === 'percent' ||
                          metric.unit === 'percent_cv'
                        ? `${metric.value}%`
                        : metric.value}
                  </p>
                  <p className="text-muted-foreground mt-3 text-sm">
                    {metric.explanation}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
          <Card className="mt-5 border-dashed">
            <CardHeader>
              <CardTitle>
                {intelligenceResult.data.data.resilience.index_name}
              </CardTitle>
              <CardDescription>
                Not calculated ·{' '}
                {intelligenceResult.data.data.resilience.reason}
              </CardDescription>
            </CardHeader>
          </Card>
        </section>
      ) : null}

      <div className="mt-10 grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Recent fiscal events</CardTitle>
            <CardDescription>
              Deterministic evidence lifecycle changes only.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 text-sm">
            {events.slice(0, 5).map((event) => (
              <div
                key={event.event_id}
                className="border-border border-b pb-4 last:border-0"
              >
                <p className="font-medium">{event.explanation}</p>
                <p className="text-muted-foreground mt-1 font-mono text-xs">
                  {formatDate(event.detected_at.slice(0, 10))} ·{' '}
                  {humanize(event.event_type)}
                </p>
              </div>
            ))}
            {!events.length ? (
              <p className="text-muted-foreground">
                No lifecycle events are currently published.
              </p>
            ) : null}
            <Button asChild variant="outline" size="sm">
              <Link href={`/events?jurisdiction=${canonicalCode}`}>
                Open event stream
              </Link>
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Evidence posture</CardTitle>
            <CardDescription>
              Coverage gaps remain explicit and distinct from zero.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-5 text-sm">
            <div>
              <p className="text-muted-foreground">Last material change</p>
              <p className="mt-1 font-medium">
                {materialEvent
                  ? `${formatDate(materialEvent.detected_at.slice(0, 10))} · ${materialEvent.explanation}`
                  : 'No material lifecycle event recorded.'}
              </p>
            </div>
            <div>
              <p className="text-muted-foreground">Missing evidence domains</p>
              <p className="mt-1 font-medium capitalize">
                {missingDomains.length
                  ? missingDomains.map(humanize).join(', ')
                  : 'None'}
              </p>
            </div>
            <div>
              <p className="text-muted-foreground">Source documents</p>
              <p className="mt-1 font-mono font-medium">{sources.length}</p>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card id="source-registry" className="mt-6">
        <CardHeader>
          <CardTitle>Source registry</CardTitle>
          <CardDescription>
            Retained publisher, fingerprint, and workflow lineage.
          </CardDescription>
        </CardHeader>
        <CardContent className="overflow-x-auto">
          {sources.length ? (
            <table className="w-full min-w-2xl text-left text-sm">
              <thead>
                <tr className="border-border text-muted-foreground border-b">
                  <th className="py-3 pr-5 font-medium">Publisher</th>
                  <th className="py-3 pr-5 font-medium">Domain</th>
                  <th className="py-3 pr-5 font-medium">Verification</th>
                  <th className="py-3 font-medium">SHA-256</th>
                </tr>
              </thead>
              <tbody>
                {sources.map((source) => (
                  <tr
                    key={source.source_id}
                    className="border-border border-b last:border-0"
                  >
                    <td className="py-3 pr-5">{source.publisher}</td>
                    <td className="py-3 pr-5 capitalize">
                      {humanize(source.fiscal_domain)}
                    </td>
                    <td className="py-3 pr-5 capitalize">
                      {humanize(source.verification_status)}
                    </td>
                    <td className="py-3 font-mono text-xs break-all">
                      {source.document_sha256}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="text-muted-foreground text-sm">
              No source registry entries are published for this Fiscal State.
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
