import { AlertTriangle, CheckCircle2, FileCheck2, Scale } from 'lucide-react'
import type { Metadata } from 'next'

import { PageHeader } from '@/components/page-header'
import { StatusPill } from '@/components/status-pill'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { formatDate, formatNaira } from '@/lib/format'
import {
  getLatestNationalDistribution,
  type NationalDistribution,
} from '@/lib/national-distribution-api'

export const metadata: Metadata = {
  title: 'National FAAC Reconciliation',
  description:
    'Cross-source verification of Nigeria’s official national FAAC distribution against governed jurisdiction evidence.',
}
export const dynamic = 'force-dynamic'

function valueLabel(value: string | null) {
  return value ? formatNaira(value) : 'Unavailable'
}

function ReconciliationCard({
  title,
  reconciliation,
}: {
  title: string
  reconciliation: NationalDistribution['component_reconciliation']
}) {
  const good = reconciliation.status === 'reconciled'
  const conflicted = reconciliation.status === 'conflicted'
  return (
    <Card className={conflicted ? 'border-destructive/40' : ''}>
      <CardHeader>
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-muted-foreground font-mono text-xs uppercase">
              {reconciliation.basis}
            </p>
            <CardTitle className="mt-2">{title}</CardTitle>
          </div>
          {good ? (
            <CheckCircle2
              className="size-5 text-emerald-600"
              aria-hidden="true"
            />
          ) : (
            <AlertTriangle
              className={
                conflicted
                  ? 'text-destructive size-5'
                  : 'text-muted-foreground size-5'
              }
              aria-hidden="true"
            />
          )}
        </div>
      </CardHeader>
      <CardContent>
        <div className="mb-5">
          <StatusPill tone={good ? 'success' : 'neutral'}>
            {reconciliation.status.toUpperCase()}
          </StatusPill>
        </div>
        <dl className="grid gap-3 text-sm sm:grid-cols-2">
          <div>
            <dt className="text-muted-foreground">Observed total</dt>
            <dd className="mt-1 font-mono font-semibold">
              {valueLabel(reconciliation.observed_total)}
            </dd>
          </div>
          <div>
            <dt className="text-muted-foreground">
              Derived comparison total
            </dt>
            <dd className="mt-1 font-mono font-semibold">
              {valueLabel(reconciliation.derived_total)}
            </dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Variance</dt>
            <dd className="mt-1 font-mono">
              {valueLabel(reconciliation.variance)}
            </dd>
          </div>
          <div>
            <dt className="text-muted-foreground">Tolerance</dt>
            <dd className="mt-1 font-mono">
              {valueLabel(reconciliation.tolerance)}
            </dd>
          </div>
        </dl>
        <p className="text-muted-foreground mt-5 text-sm leading-6">
          {reconciliation.note}
        </p>
      </CardContent>
    </Card>
  )
}

export default async function NationalReconciliationPage() {
  const result = await getLatestNationalDistribution()
  const data = result.data

  if (!data) {
    return (
      <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
        <PageHeader
          eyebrow="National reconciliation"
          title="Awaiting governed national evidence"
          description="GaiaFAAC will publish this workspace only after an official national-distribution source is fingerprinted, validated, human-reviewed and independently published. Missing evidence is not replaced with estimates."
        />
        <Card className="mt-8 max-w-3xl">
          <CardHeader>
            <CardTitle>Publication gate remains closed</CardTitle>
          </CardHeader>
          <CardContent className="text-muted-foreground text-sm leading-6">
            {result.error ??
              'No human-verified national distribution has been published for the public ledger yet.'}
          </CardContent>
        </Card>
      </div>
    )
  }

  const values: Array<[string, string | null]> = [
    ['Total distributable', data.net_distributable_amount.value],
    ['Federal Government', data.federal_amount.value],
    ['States aggregate', data.states_amount.value],
    ['Local governments', data.local_governments_amount.value],
    ['13% derivation', data.derivation_amount.value],
  ]

  return (
    <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
      <PageHeader
        eyebrow="National reconciliation"
        title="One national claim. Two independent evidence paths."
        description="GaiaFAAC compares the official recipient breakdown with the reported national total, then checks the official states aggregate against the separately published jurisdiction ledger on an explicitly declared scope."
      />

      <div className="mt-8 flex flex-wrap gap-2">
        <StatusPill tone="success">HUMAN VERIFIED</StatusPill>
        <StatusPill tone="success">
          {data.covered_jurisdictions}/{data.expected_jurisdictions} JURISDICTIONS
        </StatusPill>
        <StatusPill tone="neutral">
          {data.states_scope.replaceAll('_', ' ')}
        </StatusPill>
      </div>

      <div className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-5">
        {values.map(([label, value]) => (
          <Card key={label}>
            <CardContent className="p-5">
              <p className="text-muted-foreground text-xs uppercase">{label}</p>
              <p className="mt-2 text-xl font-semibold">{valueLabel(value)}</p>
              <p className="text-primary mt-2 font-mono text-xs">OBSERVED</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="mt-6 grid gap-5 lg:grid-cols-2">
        <ReconciliationCard
          title="Recipient arithmetic"
          reconciliation={data.component_reconciliation}
        />
        <ReconciliationCard
          title="Jurisdiction ledger comparison"
          reconciliation={data.jurisdiction_reconciliation}
        />
      </div>

      <div className="mt-6 grid gap-5 lg:grid-cols-[1.2fr_0.8fr]">
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <FileCheck2
                className="text-primary size-5"
                aria-hidden="true"
              />
              <CardTitle>National source evidence</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <dl className="grid gap-4 text-sm sm:grid-cols-2">
              <div>
                <dt className="text-muted-foreground">Source organization</dt>
                <dd className="mt-1 font-medium">
                  {data.source.source_organization}
                </dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Revenue month</dt>
                <dd className="mt-1 font-medium">
                  {formatDate(data.revenue_month)}
                </dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Source document</dt>
                <dd className="mt-1 font-medium">
                  {data.source.original_filename}
                </dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Document version</dt>
                <dd className="mt-1 font-medium">
                  {data.source.document_version}
                </dd>
              </div>
              <div className="sm:col-span-2">
                <dt className="text-muted-foreground">SHA-256</dt>
                <dd className="mt-2 font-mono text-xs break-all">
                  {data.source.sha256}
                </dd>
              </div>
            </dl>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Scale className="text-primary size-5" aria-hidden="true" />
              <CardTitle>Interpretation controls</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="text-sm">
            <dl className="space-y-4">
              <div>
                <dt className="text-muted-foreground">Derivation treatment</dt>
                <dd className="mt-1 font-mono">{data.derivation_treatment}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">States comparison scope</dt>
                <dd className="mt-1 font-mono">{data.states_scope}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Reported unit</dt>
                <dd className="mt-1 font-mono">{data.reported_unit}</dd>
              </div>
            </dl>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
