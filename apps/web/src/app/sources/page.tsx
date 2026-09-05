import {
  ExternalLink,
  FileCheck2,
  FileText,
  Landmark,
  Scale,
  ShieldCheck,
} from 'lucide-react'
import type { Metadata } from 'next'

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
import { getEvidenceNetworkStatus } from '@/lib/evidence-network-api'
import { formatDate, formatNaira, humanize } from '@/lib/format'
import {
  getPublishedNationalDistributions,
  getPublishedSources,
} from '@/lib/published-api'

export const metadata: Metadata = { title: 'Sources' }
export const dynamic = 'force-dynamic'

export default async function SourcesPage() {
  const [jurisdictionResult, nationalResult] = await Promise.all([
    getPublishedSources(),
    getPublishedNationalDistributions(),
  ])
  const jurisdictionSources = jurisdictionResult.data ?? []
  const nationalSources = nationalResult.data ?? []
  const latestJurisdiction = jurisdictionSources.length
    ? [...jurisdictionSources].sort((a, b) =>
        b.revenue_month.localeCompare(a.revenue_month),
      )[0]
    : null
  const latestNational = nationalSources.length
    ? [...nationalSources].sort((a, b) =>
        b.disbursement_month.localeCompare(a.disbursement_month),
      )[0]
    : null
  const latestCoverageComplete =
    latestJurisdiction?.covered_states === latestJurisdiction?.expected_states

  const oagfLive =
    Boolean(latestJurisdiction) && latestCoverageComplete === true
  const oagfPeriod = latestJurisdiction?.revenue_month ?? null
  const evidenceNetworkResult = await getEvidenceNetworkStatus({
    oagfLive,
    oagfPeriod,
  })
  const lanes = evidenceNetworkResult.data ?? []

  return (
    <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
      <PageHeader
        eyebrow="Evidence registry"
        title="Trace every published fiscal record to its evidence"
        description="Every published GaiaFAAC record links to retained official source evidence, preserved by SHA-256 and released only after governed review."
      />

      <div className="mt-10 grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <FileCheck2 className="text-primary size-5" aria-hidden="true" />
            <CardTitle className="pt-3">OAGF jurisdiction evidence</CardTitle>
            <CardDescription>
              Shows the latest verified/published OAGF allocation available
              to Gaia, not the current calendar month.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-semibold">
              {formatDate(latestJurisdiction?.revenue_month ?? null)}
            </p>
            <p className="text-muted-foreground mt-2 text-sm">
              {latestJurisdiction
                ? `${latestJurisdiction.covered_states} / ${latestJurisdiction.expected_states} jurisdictions covered`
                : 'No governed jurisdiction publication yet.'}
            </p>
            {latestJurisdiction && !latestCoverageComplete ? (
              <p className="mt-3 text-sm font-medium">
                Coverage is incomplete; dependent metrics remain unavailable.
              </p>
            ) : null}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <Landmark className="text-primary size-5" aria-hidden="true" />
            <CardTitle className="pt-3">National FAAC evidence</CardTitle>
            <CardDescription>
              Independent official national distributions and reconciliation
              evidence.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-semibold">
              {formatDate(latestNational?.disbursement_month ?? null)}
            </p>
            <p className="text-muted-foreground mt-2 text-sm">
              {nationalSources.length} published national packet
              {nationalSources.length === 1 ? '' : 's'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <ShieldCheck className="text-primary size-5" aria-hidden="true" />
            <CardTitle className="pt-3">Publication gate</CardTitle>
            <CardDescription>
              Collection alone never makes evidence public.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground text-sm leading-6">
              Automated validation, explicit human approval and governed
              publication remain separate actions. Blocked, quarantined and
              unresolved evidence stays out of this public registry.
            </p>
          </CardContent>
        </Card>
      </div>

      <section className="mt-12" aria-labelledby="source-lanes">
        <div className="mb-5 max-w-3xl">
          <p className="text-primary text-xs font-semibold tracking-[0.18em] uppercase">
            Fiscal evidence lanes
          </p>
          <h2 id="source-lanes" className="mt-2 text-2xl font-semibold">
            One governed view across Nigeria&apos;s fiscal institutions
          </h2>
          <p className="text-muted-foreground mt-2 text-sm leading-6">
            Gaia does not blend sources or promote planned data as live. Each
            institution has its own evidence lane, source boundary and
            publication gate.
          </p>
        </div>
        {evidenceNetworkResult.error ? (
          <DataUnavailable message={evidenceNetworkResult.error} />
        ) : (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {lanes.map((lane) => (
              <Card key={lane.authority}>
                <CardHeader>
                  <div className="flex items-start justify-between gap-3">
                    <Landmark
                      className="text-primary size-5"
                      aria-hidden="true"
                    />
                    <StatusPill
                      tone={lane.state === 'Live' ? 'success' : 'neutral'}
                    >
                      {lane.state}
                    </StatusPill>
                  </div>
                  <CardTitle className="pt-3">{lane.authority}</CardTitle>
                  <CardDescription>{lane.label}</CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground text-sm leading-6">
                    {lane.description}
                  </p>
                  <p className="text-muted-foreground mt-3 text-sm">
                    {lane.publishedRecordCount} published record
                    {lane.publishedRecordCount === 1 ? '' : 's'}
                    {lane.latestPeriod
                      ? `, latest ${formatDate(lane.latestPeriod)}`
                      : null}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </section>

      <section className="mt-12" aria-labelledby="jurisdiction-evidence">
        <div className="mb-5 flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="text-primary text-xs font-semibold tracking-[0.18em] uppercase">
              OAGF jurisdiction evidence
            </p>
            <h2
              id="jurisdiction-evidence"
              className="mt-2 text-2xl font-semibold"
            >
              Published 37-jurisdiction allocation sources
            </h2>
            <p className="text-muted-foreground mt-2 text-sm">
              {jurisdictionSources.length} published month
              {jurisdictionSources.length === 1 ? '' : 's'}, each traceable to
              its official source.
            </p>
          </div>
          <StatusPill tone="success">Verified · published</StatusPill>
        </div>

        {jurisdictionSources.length === 0 ? (
          <DataUnavailable
            message={
              jurisdictionResult.error ??
              'No governed jurisdiction evidence is published yet.'
            }
          />
        ) : (
          <div className="space-y-5">
            {jurisdictionSources.map((source) => (
              <Card key={source.revenue_month}>
                <CardHeader>
                  <div className="flex flex-wrap items-start justify-between gap-4">
                    <div>
                      <FileText
                        className="text-primary size-5"
                        aria-hidden="true"
                      />
                      <CardTitle className="pt-3">
                        {source.original_filename}
                      </CardTitle>
                      <CardDescription className="mt-2">
                        {source.source_organization} · {source.reporting_label}
                      </CardDescription>
                    </div>
                    <StatusPill tone="success">37-jurisdiction</StatusPill>
                  </div>
                </CardHeader>
                <CardContent>
                  <dl className="grid gap-5 text-sm sm:grid-cols-2 lg:grid-cols-3">
                    <div>
                      <dt className="text-muted-foreground">
                        Reporting period
                      </dt>
                      <dd className="mt-1 font-medium">
                        {formatDate(source.revenue_month)}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-muted-foreground">Jurisdictions</dt>
                      <dd className="mt-1 font-mono">
                        {source.covered_states} / {source.expected_states}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-muted-foreground">
                        Publication state
                      </dt>
                      <dd className="mt-1 font-medium">Human verified</dd>
                    </div>
                    <div className="sm:col-span-2 lg:col-span-3">
                      <dt className="text-muted-foreground">SHA-256</dt>
                      <dd className="mt-1 font-mono text-xs break-all">
                        {source.sha256}
                      </dd>
                    </div>
                  </dl>
                  {source.source_url ? (
                    <a
                      href={source.source_url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-primary mt-5 inline-flex items-center gap-1 text-sm font-medium hover:underline"
                    >
                      Open official OAGF document
                      <ExternalLink className="size-3.5" aria-hidden="true" />
                    </a>
                  ) : null}
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </section>

      <section className="mt-14" aria-labelledby="national-evidence">
        <div className="mb-5 flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="text-primary text-xs font-semibold tracking-[0.18em] uppercase">
              National FAAC evidence
            </p>
            <h2 id="national-evidence" className="mt-2 text-2xl font-semibold">
              Published national distribution sources
            </h2>
            <p className="text-muted-foreground mt-2 text-sm">
              Independent national evidence remains separate from jurisdiction
              allocation evidence and carries its own reconciliation record.
            </p>
          </div>
          <StatusPill tone="success">Governed · published</StatusPill>
        </div>

        {nationalSources.length === 0 ? (
          <DataUnavailable
            message={
              nationalResult.error ??
              'No governed national evidence is published yet.'
            }
          />
        ) : (
          <div className="space-y-5">
            {nationalSources.map((item) => (
              <Card key={item.reporting_period_id}>
                <CardHeader>
                  <div className="flex flex-wrap items-start justify-between gap-4">
                    <div>
                      <Scale
                        className="text-primary size-5"
                        aria-hidden="true"
                      />
                      <CardTitle className="pt-3">
                        {item.reporting_label}
                      </CardTitle>
                      <CardDescription className="mt-2">
                        {item.source.source_organization} ·{' '}
                        {humanize(item.source.source_authority)}
                      </CardDescription>
                    </div>
                    <StatusPill
                      tone={
                        item.component_reconciliation.status === 'reconciled'
                          ? 'success'
                          : 'neutral'
                      }
                    >
                      {humanize(item.component_reconciliation.status)}
                    </StatusPill>
                  </div>
                </CardHeader>
                <CardContent>
                  <dl className="grid gap-5 text-sm sm:grid-cols-2 lg:grid-cols-4">
                    <div>
                      <dt className="text-muted-foreground">
                        Disbursement month
                      </dt>
                      <dd className="mt-1 font-medium">
                        {formatDate(item.disbursement_month)}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-muted-foreground">
                        Allocation period
                      </dt>
                      <dd className="mt-1 font-medium">
                        {formatDate(item.allocation_period_month)}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-muted-foreground">Observed total</dt>
                      <dd className="mt-1 font-medium">
                        {formatNaira(item.net_distributable_amount.value)}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-muted-foreground">Reconciliation</dt>
                      <dd className="mt-1 font-medium">
                        {humanize(item.component_reconciliation.status)}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-muted-foreground">
                        Source authority
                      </dt>
                      <dd className="mt-1 font-medium">
                        {humanize(item.source.source_authority)}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-muted-foreground">Source type</dt>
                      <dd className="mt-1 font-medium">
                        {humanize(item.source.source_type)}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-muted-foreground">
                        Document version
                      </dt>
                      <dd className="mt-1 font-mono">
                        {item.source.document_version}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-muted-foreground">
                        Publication state
                      </dt>
                      <dd className="mt-1 font-medium">Human verified</dd>
                    </div>
                    <div className="sm:col-span-2 lg:col-span-4">
                      <dt className="text-muted-foreground">SHA-256</dt>
                      <dd className="mt-1 font-mono text-xs break-all">
                        {item.source.sha256}
                      </dd>
                    </div>
                  </dl>
                  {item.source.source_url ? (
                    <a
                      href={item.source.source_url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-primary mt-5 inline-flex items-center gap-1 text-sm font-medium hover:underline"
                    >
                      Open official national source
                      <ExternalLink className="size-3.5" aria-hidden="true" />
                    </a>
                  ) : null}
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}
