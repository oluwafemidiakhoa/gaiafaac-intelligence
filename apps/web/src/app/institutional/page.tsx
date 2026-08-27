import {
  ArrowRight,
  BarChart3,
  Building2,
  DatabaseZap,
  FileCheck2,
  Landmark,
  ShieldCheck,
} from 'lucide-react'
import type { Metadata } from 'next'
import Link from 'next/link'

import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'

export const metadata: Metadata = {
  title: 'Institutional Intelligence',
  description:
    'How Gaia Fiscal Intelligence turns official Nigerian public-finance evidence into decision-ready intelligence for banks, investors, advisers, companies and public institutions.',
}

const useCases = [
  {
    icon: Building2,
    title: 'Banking & credit',
    description:
      'Understand allocation trends, internally generated revenue, debt pressure and source evidence before extending public-sector or state-linked exposure.',
  },
  {
    icon: BarChart3,
    title: 'Investment & research',
    description:
      'Compare jurisdictions, identify material changes and move from a headline to the underlying official evidence without rebuilding the data pipeline yourself.',
  },
  {
    icon: Landmark,
    title: 'Government & advisory',
    description:
      'Create traceable comparative analysis, evidence packs and monitoring workflows that preserve the original public record and its revision history.',
  },
]

const evidenceModel = [
  'Official-source collection',
  'Document identity and SHA-256 fingerprinting',
  'Structured extraction and deterministic validation',
  'Explicit human review before publication',
  'Version-aware records and revision history',
  'Decision interfaces, exports and programmatic delivery',
]

export default function InstitutionalPage() {
  return (
    <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
      <section className="grid gap-10 border-b border-emerald-950/10 pb-12 lg:grid-cols-[1.1fr_0.9fr] lg:items-end">
        <div className="max-w-4xl">
          <p className="text-primary font-mono text-xs font-semibold tracking-[0.18em] uppercase">
            Institutional intelligence
          </p>
          <h1 className="mt-5 text-4xl font-semibold tracking-[-0.045em] text-balance text-slate-950 sm:text-5xl lg:text-6xl">
            Nigerian fiscal evidence, organized for serious financial decisions.
          </h1>
          <p className="mt-6 max-w-3xl text-base leading-8 text-slate-600 sm:text-lg">
            Nigeria publishes critical fiscal information across many agencies,
            reports and formats. Gaia Fiscal Intelligence is building the
            governed evidence layer that brings those records into one
            traceable, comparable and decision-ready system.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Button asChild size="lg">
              <Link href="/terminal">
                Open Gaia Terminal
                <ArrowRight className="size-4" aria-hidden="true" />
              </Link>
            </Button>
            <Button asChild size="lg" variant="outline">
              <Link href="/gaia-analyst">Ask Gaia</Link>
            </Button>
          </div>
        </div>

        <Card className="border-emerald-950/10 bg-emerald-950 text-white shadow-xl shadow-emerald-950/10">
          <CardHeader>
            <ShieldCheck
              className="size-6 text-emerald-300"
              aria-hidden="true"
            />
            <CardTitle className="pt-3 text-2xl">
              The product is not the public data.
            </CardTitle>
            <CardDescription className="text-emerald-50/75">
              The value is the governed infrastructure around it: provenance,
              verification, structured history, monitoring, comparison and
              institutional delivery.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm leading-7 text-emerald-50/80">
              A decision-maker should be able to move from a fiscal signal to
              the exact source document and know what was published, when it was
              reviewed, and whether the evidence changed later.
            </p>
          </CardContent>
        </Card>
      </section>

      <section className="py-12">
        <div className="max-w-3xl">
          <p className="text-primary font-mono text-xs font-semibold tracking-[0.16em] uppercase">
            The problem
          </p>
          <h2 className="mt-3 text-3xl font-semibold tracking-tight text-slate-950">
            Public does not automatically mean decision-ready.
          </h2>
          <p className="mt-4 text-base leading-8 text-slate-600">
            FAAC allocations, state IGR, debt records, macroeconomic releases
            and tax evidence can be public while still being expensive to
            collect, reconcile, monitor and defend inside a serious institution.
            Gaia is designed to reduce that evidence burden without hiding
            uncertainty or inventing missing values.
          </p>
        </div>

        <div className="mt-8 grid gap-5 lg:grid-cols-3">
          {useCases.map(({ icon: Icon, title, description }) => (
            <Card key={title}>
              <CardHeader>
                <Icon className="text-primary size-5" aria-hidden="true" />
                <CardTitle className="pt-3">{title}</CardTitle>
                <CardDescription className="leading-6">
                  {description}
                </CardDescription>
              </CardHeader>
            </Card>
          ))}
        </div>
      </section>

      <section className="grid gap-8 rounded-2xl border border-emerald-950/10 bg-slate-950 p-6 text-white sm:p-8 lg:grid-cols-[0.85fr_1.15fr] lg:items-start">
        <div>
          <FileCheck2 className="size-6 text-emerald-300" aria-hidden="true" />
          <p className="mt-5 font-mono text-xs font-semibold tracking-[0.16em] text-emerald-300 uppercase">
            Evidence model
          </p>
          <h2 className="mt-3 text-3xl font-semibold tracking-tight">
            Every governed number should have a defensible evidence trail.
          </h2>
          <p className="mt-4 text-sm leading-7 text-slate-300">
            Gaia separates collection, extraction, validation, review and
            publication. Missing evidence remains unavailable rather than being
            silently estimated.
          </p>
        </div>
        <div className="grid gap-3 sm:grid-cols-2">
          {evidenceModel.map((item, index) => (
            <div
              key={item}
              className="rounded-xl border border-white/10 bg-white/5 p-4"
            >
              <p className="font-mono text-xs text-emerald-300">0{index + 1}</p>
              <p className="mt-2 text-sm leading-6 font-medium">{item}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="py-12">
        <div className="grid gap-6 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <DatabaseZap className="text-primary size-5" aria-hidden="true" />
              <CardTitle className="pt-3 text-2xl">
                What institutions can buy
              </CardTitle>
              <CardDescription>
                Commercial value comes from the governed layer around public
                evidence—not ownership of government records.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="space-y-3 text-sm leading-6 text-slate-700">
                <li>
                  Institutional fiscal monitoring and executive intelligence
                </li>
                <li>
                  Historical evidence, governed exports and decision packets
                </li>
                <li>Higher-volume data and API delivery</li>
                <li>Organization workspaces and custom evidence workflows</li>
                <li>
                  Research support, integration and permitted downstream use
                </li>
              </ul>
            </CardContent>
          </Card>

          <Card className="bg-muted/30">
            <CardHeader>
              <ShieldCheck className="text-primary size-5" aria-hidden="true" />
              <CardTitle className="pt-3 text-2xl">
                Start by verifying it yourself
              </CardTitle>
              <CardDescription>
                The strongest introduction to Gaia is not a pitch deck. It is
                the live evidence, the source registry and an answer you can
                trace back to its records.
              </CardDescription>
            </CardHeader>
            <CardContent className="flex flex-wrap gap-3">
              <Button asChild>
                <Link href="/terminal">Open Terminal</Link>
              </Button>
              <Button asChild variant="outline">
                <Link href="/sources">Inspect evidence</Link>
              </Button>
              <Button asChild variant="outline">
                <Link href="/pricing">See commercial access</Link>
              </Button>
            </CardContent>
          </Card>
        </div>
      </section>
    </div>
  )
}
