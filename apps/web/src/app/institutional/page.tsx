import {
  ArrowRight,
  BarChart3,
  Building2,
  DatabaseZap,
  FileCheck2,
  Landmark,
  ShieldCheck,
  Workflow,
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
    <div className="pb-8">
      <section className="relative overflow-hidden border-b border-white/8 bg-[#041915] text-white">
        <div className="absolute top-0 right-0 size-[34rem] rounded-full bg-emerald-300/[0.06] blur-3xl" />
        <div className="gaia-shell relative grid gap-12 py-16 lg:grid-cols-[1.08fr_.92fr] lg:items-center lg:py-24">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-amber-200/15 bg-amber-200/[0.06] px-3 py-1.5">
              <Landmark className="size-3.5 text-amber-300" />
              <span className="font-mono text-[0.65rem] font-bold tracking-[0.18em] text-amber-100 uppercase">
                Institutional / Decision infrastructure
              </span>
            </div>
            <h1 className="mt-6 max-w-[13ch] text-5xl leading-[0.96] font-semibold tracking-[-0.06em] text-balance sm:text-6xl lg:text-7xl">
              Public finance evidence built for capital decisions.
            </h1>
            <p className="mt-6 max-w-2xl text-lg leading-8 text-emerald-50/65">
              Gaia turns fragmented official fiscal records into a governed
              evidence layer banks, investors, advisers and public institutions
              can inspect, compare, monitor and defend.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Button asChild size="lg" className="rounded-full bg-amber-300 font-bold text-teal-950 hover:bg-amber-200">
                <Link href="/pilot">
                  Start institutional pilot <ArrowRight className="size-4" />
                </Link>
              </Button>
              <Button asChild size="lg" variant="outline" className="rounded-full border-white/15 bg-white/[0.04] text-white hover:bg-white/[0.08] hover:text-white">
                <Link href="/terminal">Open Control Plane</Link>
              </Button>
            </div>
          </div>

          <div className="gaia-panel-dark overflow-hidden p-6 sm:p-8">
            <p className="font-mono text-[0.64rem] font-semibold tracking-[0.18em] text-emerald-200/45 uppercase">
              The commercial product
            </p>
            <h2 className="mt-4 text-3xl font-semibold tracking-[-0.04em]">
              Not the public data. The governed infrastructure around it.
            </h2>
            <p className="mt-4 text-sm leading-7 text-white/55">
              Provenance, verification, structured history, monitoring,
              comparison, evidence-bound AI and institutional delivery turn
              public records into usable decision infrastructure.
            </p>
            <div className="mt-7 grid grid-cols-2 gap-3">
              {[
                ['Evidence', 'Source-linked'],
                ['Publication', 'Review-gated'],
                ['Delivery', 'API + workspace'],
                ['Decision', 'Auditable'],
              ].map(([label, value]) => (
                <div key={label} className="rounded-2xl border border-white/10 bg-white/[0.035] p-4">
                  <p className="font-mono text-[0.58rem] tracking-[0.14em] text-white/35 uppercase">{label}</p>
                  <p className="mt-2 text-sm font-semibold text-emerald-100">{value}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <div className="gaia-shell gaia-section">
        <section className="grid gap-8 lg:grid-cols-[.72fr_1.28fr] lg:items-start">
          <div>
            <p className="gaia-kicker">Institutional wedge</p>
            <h2 className="mt-4 text-4xl font-semibold tracking-[-0.045em] text-balance">
              Public does not mean decision-ready.
            </h2>
            <p className="text-muted-foreground mt-5 text-base leading-8">
              FAAC allocations, state IGR, debt records, macroeconomic releases
              and tax evidence can be public while still being costly to collect,
              reconcile, monitor and defend inside a serious institution.
            </p>
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            {useCases.map(({ icon: Icon, title, description }) => (
              <article key={title} className="gaia-panel group p-6 transition hover:-translate-y-1">
                <div className="flex size-11 items-center justify-center rounded-2xl border border-primary/10 bg-primary/[0.07]">
                  <Icon className="text-primary size-5" />
                </div>
                <h3 className="mt-7 text-lg font-semibold tracking-tight">{title}</h3>
                <p className="text-muted-foreground mt-3 text-sm leading-7">{description}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="mt-12 overflow-hidden rounded-3xl border border-white/8 bg-[#061d19] text-white shadow-[0_25px_80px_rgba(0,0,0,.15)]">
          <div className="grid lg:grid-cols-[.8fr_1.2fr]">
            <div className="border-b border-white/10 p-7 lg:border-r lg:border-b-0 lg:p-9">
              <FileCheck2 className="size-6 text-amber-300" />
              <p className="mt-6 font-mono text-[0.65rem] font-semibold tracking-[0.18em] text-amber-200/55 uppercase">
                Evidence architecture
              </p>
              <h2 className="mt-4 text-3xl font-semibold tracking-[-0.04em]">
                Every governed number carries a defensible path.
              </h2>
              <p className="mt-4 text-sm leading-7 text-white/55">
                Collection, extraction, validation, review and publication stay
                separate. Missing evidence remains unavailable instead of being
                silently estimated.
              </p>
            </div>
            <div className="grid sm:grid-cols-2 lg:grid-cols-3">
              {evidenceModel.map((item, index) => (
                <div key={item} className="border-t border-white/10 p-6 first:border-t-0 sm:border-l sm:first:border-l-0 lg:[&:nth-child(-n+3)]:border-t-0">
                  <p className="font-mono text-xs font-semibold text-amber-300">0{index + 1}</p>
                  <p className="mt-7 text-sm leading-6 font-medium text-white/75">{item}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="mt-12 grid gap-5 lg:grid-cols-2">
          <div className="gaia-panel p-7 sm:p-8">
            <DatabaseZap className="text-primary size-6" />
            <p className="gaia-kicker mt-6">Commercial layer</p>
            <h3 className="mt-3 text-3xl font-semibold tracking-[-0.04em]">What institutions can buy</h3>
            <p className="text-muted-foreground mt-4 text-sm leading-7">
              Commercial value comes from the governed layer around public
              evidence—not ownership of government records.
            </p>
            <ul className="mt-6 grid gap-3 text-sm leading-6">
              {[
                'Institutional fiscal monitoring and executive intelligence',
                'Historical evidence, governed exports and decision packets',
                'Higher-volume data and API delivery',
                'Organization workspaces and custom evidence workflows',
                'Research support, integration and permitted downstream use',
              ].map((item) => (
                <li key={item} className="flex gap-3">
                  <ShieldCheck className="text-primary mt-0.5 size-4 shrink-0" />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
            <Button asChild className="mt-7">
              <Link href="/pricing">See commercial access</Link>
            </Button>
          </div>

          <div className="overflow-hidden rounded-3xl border border-amber-300/40 bg-amber-100/60 p-7 dark:bg-amber-300/[0.07] sm:p-8">
            <Workflow className="size-6 text-amber-800 dark:text-amber-300" />
            <p className="mt-6 font-mono text-[0.65rem] font-bold tracking-[0.18em] text-amber-900/60 uppercase dark:text-amber-200/60">
              Proof before pitch
            </p>
            <h3 className="mt-3 text-3xl font-semibold tracking-[-0.04em]">
              Let the institution verify Gaia before buying Gaia.
            </h3>
            <p className="text-muted-foreground mt-4 text-sm leading-7">
              The strongest introduction is the live evidence, the source
              registry, the review protocol and an answer that can be traced back
              to official records.
            </p>
            <div className="mt-7 flex flex-wrap gap-2">
              <Button asChild><Link href="/terminal">Open Terminal</Link></Button>
              <Button asChild variant="outline"><Link href="/sources">Inspect evidence</Link></Button>
              <Button asChild variant="outline"><Link href="/review">See review controls</Link></Button>
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}
