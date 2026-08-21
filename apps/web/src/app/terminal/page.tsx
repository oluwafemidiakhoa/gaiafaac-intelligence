import type { Metadata } from 'next'
import Link from 'next/link'

import { DataUnavailable } from '@/components/data-unavailable'
import { GaiaTerminalSearch } from '@/components/gaia-terminal-search'
import { PageHeader } from '@/components/page-header'
import { StatusPill } from '@/components/status-pill'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { formatDate, formatNaira } from '@/lib/format'
import { getPublishedOverview } from '@/lib/published-api'

export const metadata: Metadata = {
  title: 'Gaia Terminal',
  description:
    'Unified command surface for governed Nigerian fiscal evidence, jurisdiction research, reconciliation, monitoring and institutional workflows.',
}
export const dynamic = 'force-dynamic'

const institutionalWorkflows = [
  {
    href: '/watchlist',
    title: 'Organization Monitoring',
    description:
      'Shared jurisdiction watchlists, evidence-linked alerts and per-member read state.',
  },
  {
    href: '/evidence-rooms',
    title: 'Evidence Rooms',
    description:
      'Durable organization case files with immutable evidence references and separate notes.',
  },
  {
    href: '/events',
    title: 'Fiscal Events',
    description:
      'Inspect governed fiscal changes before routing them into institutional workflows.',
  },
  {
    href: '/gaia-analyst',
    title: 'Gaia Analyst',
    description:
      'Ask deterministic questions across governed fiscal evidence and historical knowledge states.',
  },
  {
    href: '/compare',
    title: 'Jurisdiction Comparison',
    description:
      'Compare evidence-backed fiscal metrics without ranking incomparable periods.',
  },
  {
    href: '/decision-packets',
    title: 'Decision Packets',
    description:
      'Create decision-ready evidence dossiers while preserving source lineage and caveats.',
  },
  {
    href: '/account',
    title: 'Institutional API',
    description:
      'Manage Team/API access for the machine-readable Fiscal Event stream and enterprise workflows.',
  },
]

function compactNaira(value: string | null) {
  if (!value) return 'Unavailable'
  const amount = Number(value)
  if (!Number.isFinite(amount)) return formatNaira(value)
  if (Math.abs(amount) >= 1_000_000_000_000)
    return `₦${(amount / 1_000_000_000_000).toFixed(2)}T`
  if (Math.abs(amount) >= 1_000_000_000)
    return `₦${(amount / 1_000_000_000).toFixed(2)}B`
  return formatNaira(value)
}

export default async function GaiaTerminalPage() {
  const overview = await getPublishedOverview()
  const data = overview.data

  return (
    <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
      <div className="grid gap-8 xl:grid-cols-[1fr_19rem] xl:items-end">
        <PageHeader
          eyebrow="Gaia Terminal"
          title="One command surface for Nigeria’s fiscal evidence."
          description="Search governed jurisdictions, jump into proofs and local-government evidence, ask the verified ledger, inspect revisions and reconciliation, run scenarios, monitor signals, open durable Evidence Rooms and route machine-readable Fiscal Events without leaving the evidence boundary."
        />

        <Card className="bg-muted/25">
          <CardHeader>
            <div className="flex items-center justify-between gap-3">
              <CardTitle className="text-base">Evidence boundary</CardTitle>
              <StatusPill tone="success">Fail closed</StatusPill>
            </div>
            <CardDescription>
              Terminal search never synthesizes a missing jurisdiction or fiscal
              value.
            </CardDescription>
          </CardHeader>
        </Card>
      </div>

      {data ? (
        <>
          <section className="mt-9 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-muted-foreground text-sm font-medium">
                  Latest verified period
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="font-mono text-lg font-semibold">
                  {formatDate(data.period.revenue_month)}
                </p>
                <p className="text-muted-foreground mt-2 text-xs">
                  {data.period.reporting_label}
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="text-muted-foreground text-sm font-medium">
                  State-ledger net total
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="font-mono text-2xl font-semibold">
                  {compactNaira(data.total_net)}
                </p>
                <p className="text-muted-foreground mt-2 text-xs">
                  Published governed jurisdiction records only
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="text-muted-foreground text-sm font-medium">
                  Jurisdiction coverage
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="font-mono text-2xl font-semibold">
                  {data.covered_states}/{data.expected_states}
                </p>
                <p className="text-muted-foreground mt-2 text-xs">
                  Missing jurisdictions remain unavailable
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="text-muted-foreground text-sm font-medium">
                  Source fingerprint
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="font-mono text-xs leading-5 break-all">
                  {data.source.sha256}
                </p>
              </CardContent>
            </Card>
          </section>

          <section className="mt-9 rounded-2xl border border-emerald-950/10 bg-[radial-gradient(circle_at_top_left,rgba(16,185,129,0.10),transparent_30%)] p-5 sm:p-7">
            <GaiaTerminalSearch
              jurisdictions={data.allocations}
              periodLabel={data.period.reporting_label}
            />
          </section>
        </>
      ) : (
        <div className="mt-9">
          <DataUnavailable
            message={
              overview.error ??
              'No governed published jurisdiction ledger is available for Gaia Terminal.'
            }
          />
        </div>
      )}

      <section className="mt-12">
        <div className="mb-5 max-w-3xl">
          <p className="text-primary text-xs font-semibold tracking-[0.18em] uppercase">
            Institutional workflow
          </p>
          <h2 className="mt-2 text-2xl font-semibold tracking-tight">
            Move from fiscal change to governed decision.
          </h2>
          <p className="text-muted-foreground mt-2 text-sm leading-6">
            Monitoring, evidence, analysis and distribution share the same governed fiscal record.
            Human interpretation stays distinct from immutable evidence.
          </p>
        </div>
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {institutionalWorkflows.map((workflow) => (
            <Link key={workflow.href} href={workflow.href} className="group">
              <Card className="h-full transition-colors group-hover:bg-muted/40">
                <CardHeader>
                  <CardTitle className="text-base">{workflow.title}</CardTitle>
                  <CardDescription className="leading-6">
                    {workflow.description}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <span className="text-primary text-sm font-medium">
                    Open workflow →
                  </span>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      </section>
    </div>
  )
}
