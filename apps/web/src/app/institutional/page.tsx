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
      <section className="grid gap-10 border-b border-teal-900/10 pb-12 lg:grid-cols-[1.1fr_0.9fr] lg:items-end">
        <div className="max-w-4xl">
          <p className="font-mono text-xs font-semibold tracking-[0.18em] text-teal-700 uppercase">
            Institutional intelligence
          </p>
          <h1
            className="mt-5 text-4xl font-semibold tracking-[-0.045em] text-balance text-teal-950 sm:text-5xl lg:text-6xl"
            style={{ fontFamily: 'Georgia, serif' }}
          >
            Nigerian fiscal evidence, organized for serious financial decisions.
          </h1>
          <p className="mt-6 max-w-3xl text-base leading-8 text-teal-700 sm:text-lg">
            Nigeria publishes critical fiscal information across many agencies,
            reports and formats. Gaia Fiscal Intelligence is building the
            governed evidence layer that brings those records into one
            traceable, comparable and decision-ready system.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Button asChild size="lg" className="bg-teal-900 hover:bg-teal-800">
              <Link href="/terminal">
                Open Gaia Terminal
                <ArrowRight className="size-4" aria-hidden="true" />
              </Link>
            </Button>
            <Button
              asChild
              size="lg"
              variant="outline"
              className="border-teal-900 text-teal-900 hover:bg-teal-50"
            >
              <Link href="/gaia-analyst">Ask Gaia</Link>
            </Button>
          </div>
        </div>

        <div className="rounded-xl border-2 border-amber-400 bg-teal-900 text-white shadow-xl">
          <div className="p-6">
            <ShieldCheck className="size-6 text-amber-300" aria-hidden="true" />
            <h3 className="pt-3 text-2xl font-semibold">
              The product is not the public data.
            </h3>
            <p className="mt-2 text-sm leading-6 text-amber-50/75">
              The value is the governed infrastructure around it: provenance,
              verification, structured history, monitoring, comparison and
              institutional delivery.
            </p>
            <p className="mt-4 text-sm leading-7 text-amber-50">
              A decision-maker should be able to move from a fiscal signal to
              the exact source document and know what was published, when it was
              reviewed, and whether the evidence changed later.
            </p>
          </div>
        </div>
      </section>

      <section className="py-12">
        <div className="max-w-3xl">
          <p className="font-mono text-xs font-semibold tracking-[0.16em] text-teal-700 uppercase">
            The problem
          </p>
          <h2
            className="mt-3 text-3xl font-semibold tracking-tight text-teal-950"
            style={{ fontFamily: 'Georgia, serif' }}
          >
            Public does not automatically mean decision-ready.
          </h2>
          <p className="mt-4 text-base leading-8 text-teal-700">
            FAAC allocations, state IGR, debt records, macroeconomic releases
            and tax evidence can be public while still being expensive to
            collect, reconcile, monitor and defend inside a serious institution.
            Gaia is designed to reduce that evidence burden without hiding
            uncertainty or inventing missing values.
          </p>
        </div>

        <div className="mt-8 grid gap-5 lg:grid-cols-3">
          {useCases.map(({ icon: Icon, title, description }) => (
            <div
              key={title}
              className="rounded-lg border-2 border-teal-200 bg-white p-6 transition-shadow hover:shadow-lg"
            >
              <Icon className="size-6 text-teal-900" aria-hidden="true" />
              <h3 className="pt-3 text-lg font-semibold text-teal-950">
                {title}
              </h3>
              <p className="mt-2 text-sm leading-6 text-teal-700">
                {description}
              </p>
            </div>
          ))}
        </div>
      </section>

      <section className="grid gap-8 rounded-2xl border-2 border-amber-300 bg-teal-950 p-6 text-white sm:p-8 lg:grid-cols-[0.85fr_1.15fr] lg:items-start">
        <div>
          <FileCheck2 className="size-6 text-amber-300" aria-hidden="true" />
          <p className="mt-5 font-mono text-xs font-semibold tracking-[0.16em] text-amber-300 uppercase">
            Evidence model
          </p>
          <h2
            className="mt-3 text-3xl font-semibold tracking-tight"
            style={{ fontFamily: 'Georgia, serif' }}
          >
            Every governed number should have a defensible evidence trail.
          </h2>
          <p className="mt-4 text-sm leading-7 text-amber-50/75">
            Gaia separates collection, extraction, validation, review and
            publication. Missing evidence remains unavailable rather than being
            silently estimated.
          </p>
        </div>
        <div className="grid gap-3 sm:grid-cols-2">
          {evidenceModel.map((item, index) => (
            <div
              key={item}
              className="rounded-lg border border-amber-400/20 bg-white/5 p-4"
            >
              <p className="font-mono text-xs font-semibold text-amber-300">
                0{index + 1}
              </p>
              <p className="mt-2 text-sm leading-6 font-medium text-amber-50">
                {item}
              </p>
            </div>
          ))}
        </div>
      </section>

      <section className="py-12">
        <div className="grid gap-6 lg:grid-cols-2">
          <div className="rounded-lg border-2 border-teal-200 bg-white p-6">
            <DatabaseZap className="size-6 text-teal-900" aria-hidden="true" />
            <h3 className="pt-3 text-2xl font-semibold text-teal-950">
              What institutions can buy
            </h3>
            <p className="mt-2 text-sm text-teal-700">
              Commercial value comes from the governed layer around public
              evidence—not ownership of government records.
            </p>
            <ul className="mt-4 space-y-3 text-sm leading-6 text-teal-800">
              <li>
                ✓ Institutional fiscal monitoring and executive intelligence
              </li>
              <li>
                ✓ Historical evidence, governed exports and decision packets
              </li>
              <li>✓ Higher-volume data and API delivery</li>
              <li>✓ Organization workspaces and custom evidence workflows</li>
              <li>
                ✓ Research support, integration and permitted downstream use
              </li>
            </ul>
          </div>

          <div className="rounded-lg border-2 border-amber-300 bg-gradient-to-br from-amber-50 to-white p-6">
            <ShieldCheck className="size-6 text-teal-900" aria-hidden="true" />
            <h3 className="pt-3 text-2xl font-semibold text-teal-950">
              Start by verifying it yourself
            </h3>
            <p className="mt-2 text-sm text-teal-700">
              The strongest introduction to Gaia is not a pitch deck. It is the
              live evidence, the source registry and an answer you can trace
              back to its records.
            </p>
            <div className="mt-4 flex flex-wrap gap-2">
              <Button
                asChild
                size="sm"
                className="bg-teal-900 hover:bg-teal-800"
              >
                <Link href="/terminal">Open Terminal</Link>
              </Button>
              <Button
                asChild
                size="sm"
                variant="outline"
                className="border-teal-900 text-teal-900"
              >
                <Link href="/sources">Inspect evidence</Link>
              </Button>
              <Button
                asChild
                size="sm"
                variant="outline"
                className="border-teal-900 text-teal-900"
              >
                <Link href="/pricing">See commercial access</Link>
              </Button>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
