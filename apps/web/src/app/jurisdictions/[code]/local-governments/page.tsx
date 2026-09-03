import { FileSpreadsheet, FileText, ShieldCheck } from 'lucide-react'
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
import { formatDate, formatNaira } from '@/lib/format'
import { getLgaPublicationStatus } from '@/lib/lga-status-api'
import {
  getPublishedLgasForState,
  getPublishedOverview,
} from '@/lib/published-api'

export const dynamic = 'force-dynamic'

const stageCopy = {
  not_ingested: {
    label: 'Source not ingested',
    tone: 'neutral' as const,
  },
  investigation_required: {
    label: 'Extraction blocked',
    tone: 'warning' as const,
  },
  awaiting_review: {
    label: 'Awaiting human review',
    tone: 'warning' as const,
  },
  awaiting_publication: {
    label: 'Awaiting publisher',
    tone: 'success' as const,
  },
  published: {
    label: 'Published',
    tone: 'success' as const,
  },
}

export default async function LocalGovernmentsPage({
  params,
}: {
  params: Promise<{ code: string }>
}) {
  const { code } = await params
  const stateCode = code.toUpperCase()
  const [result, overviewResult, statusResult] = await Promise.all([
    getPublishedLgasForState(stateCode),
    getPublishedOverview(),
    getLgaPublicationStatus(stateCode),
  ])

  if (!result.data) {
    const publishedOverview = overviewResult.data
    const allocation =
      publishedOverview?.allocations.find(
        (item) => item.state_code === stateCode,
      ) ?? null
    const pipelineStatus = statusResult.data
    const statusPresentation = pipelineStatus
      ? stageCopy[pipelineStatus.stage]
      : null

    return (
      <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
        <PageHeader
          eyebrow={`Local-government ledger · ${stateCode}`}
          title="LGA evidence publication status"
          description="GaiaFAAC exposes the governed state of OAGF Table IV evidence instead of inferring local-government values from state totals."
        />

        <Card className="mt-8 overflow-hidden">
          <CardHeader className="border-b">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <CardTitle>OAGF Table IV pipeline</CardTitle>
                <CardDescription className="mt-2 max-w-3xl">
                  {pipelineStatus?.message ??
                    statusResult.error ??
                    'The publication status could not be loaded.'}
                </CardDescription>
              </div>
              {statusPresentation ? (
                <StatusPill tone={statusPresentation.tone}>
                  {statusPresentation.label}
                </StatusPill>
              ) : null}
            </div>
          </CardHeader>
          <CardContent className="grid gap-5 pt-6 sm:grid-cols-2 lg:grid-cols-4">
            <div>
              <p className="text-muted-foreground text-xs tracking-wide uppercase">
                Source format
              </p>
              <div className="mt-2 flex items-center gap-2 font-medium">
                {pipelineStatus?.source_format === 'excel' ? (
                  <FileSpreadsheet className="text-primary size-4" />
                ) : (
                  <FileText className="text-primary size-4" />
                )}
                {pipelineStatus?.source_format
                  ? pipelineStatus.source_format.toUpperCase()
                  : 'Not yet known'}
              </div>
            </div>
            <div>
              <p className="text-muted-foreground text-xs tracking-wide uppercase">
                Extracted jurisdictions
              </p>
              <p className="mt-2 font-mono text-lg font-semibold">
                {pipelineStatus
                  ? `${pipelineStatus.record_count}/${pipelineStatus.expected_record_count}`
                  : '—'}
              </p>
            </div>
            <div>
              <p className="text-muted-foreground text-xs tracking-wide uppercase">
                Blocking findings
              </p>
              <p className="mt-2 font-mono text-lg font-semibold">
                {pipelineStatus?.blocking_count ?? '—'}
              </p>
            </div>
            <div>
              <p className="text-muted-foreground text-xs tracking-wide uppercase">
                Evidence period
              </p>
              <p className="mt-2 font-medium">
                {formatDate(pipelineStatus?.disbursement_month ?? null)}
              </p>
            </div>

            {pipelineStatus?.original_filename ? (
              <div className="sm:col-span-2 lg:col-span-4">
                <p className="text-muted-foreground text-xs tracking-wide uppercase">
                  Retained official source
                </p>
                <p className="mt-2 text-sm font-medium break-all">
                  {pipelineStatus.original_filename}
                </p>
                {pipelineStatus.source_sha256 ? (
                  <p className="text-muted-foreground mt-2 font-mono text-xs break-all">
                    SHA-256 {pipelineStatus.source_sha256}
                  </p>
                ) : null}
              </div>
            ) : null}
          </CardContent>
        </Card>

        <div className="mt-6">
          <DataUnavailable
            message={
              result.error ??
              'No governed local-government evidence is published for this jurisdiction yet.'
            }
          />
        </div>

        {publishedOverview && allocation ? (
          <Card className="mt-6">
            <CardHeader>
              <CardTitle>Available state evidence</CardTitle>
              <CardDescription>
                Verified state-level FAAC evidence remains available while the
                local-government Table IV batch completes its governed publication path.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-5">
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <p className="text-muted-foreground text-sm">
                    Latest verified period
                  </p>
                  <p className="mt-1 font-medium">
                    {formatDate(publishedOverview.period.revenue_month)}
                  </p>
                </div>
                <div>
                  <p className="text-muted-foreground text-sm">
                    State FAAC net allocation
                  </p>
                  <p className="mt-1 font-mono text-lg font-semibold">
                    {formatNaira(allocation.net_allocation)}
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-3 rounded-xl border p-4">
                <ShieldCheck className="text-primary mt-0.5 size-5 shrink-0" />
                <p className="text-muted-foreground text-sm leading-6">
                  State-level evidence does not substitute for missing LGA evidence.
                  Gaia does not derive individual local-government allocations from the
                  state total.
                </p>
              </div>
              <div className="flex flex-wrap gap-3">
                <Button asChild>
                  <Link href={`/states/${allocation.state_slug}`}>
                    Open state evidence
                  </Link>
                </Button>
                <Button asChild variant="outline">
                  <Link
                    href={`/fiscal-proof/${allocation.state_slug}/${publishedOverview.period.revenue_month}`}
                  >
                    Verify allocation
                  </Link>
                </Button>
                <Button asChild variant="outline">
                  <Link
                    href={`/decision-packets/${allocation.state_slug}?year=${publishedOverview.period.revenue_month.slice(0, 4)}`}
                  >
                    Decision Packet
                  </Link>
                </Button>
              </div>
            </CardContent>
          </Card>
        ) : null}
      </div>
    )
  }

  const data = result.data

  return (
    <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
      <PageHeader
        eyebrow={`OAGF Table IV · ${data.state_code}`}
        title={`${data.state_name} local governments`}
        description="Individual observed allocations from published, human-verified OAGF Table IV evidence. No local-government value is estimated from the national aggregate."
      />

      <div className="mt-7 flex flex-wrap items-center gap-3">
        <StatusPill tone="success">Human verified</StatusPill>
        <span className="text-muted-foreground font-mono text-xs">
          {data.local_government_count} published local-government jurisdictions
        </span>
      </div>

      <div className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {data.local_governments.map((lga) => (
          <Link
            key={lga.local_government_slug}
            href={`/jurisdictions/${data.state_code}/local-governments/${lga.local_government_slug}`}
            className="group"
          >
            <Card className="group-hover:border-primary/40 h-full transition-colors">
              <CardHeader>
                <CardTitle className="text-base">
                  {lga.local_government_name}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <p className="text-muted-foreground text-xs">
                    Latest total net
                  </p>
                  <p className="mt-1 font-mono text-lg font-semibold">
                    {formatNaira(lga.total_net_allocation)}
                  </p>
                </div>
                <div className="text-muted-foreground text-xs">
                  Disbursement {formatDate(lga.disbursement_month)} · Table IV
                  {lga.source_page ? ` · p. ${lga.source_page}` : ''}
                </div>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  )
}
