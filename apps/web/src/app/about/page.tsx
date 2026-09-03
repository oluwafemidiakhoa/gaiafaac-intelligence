import type { Metadata } from 'next'
import Link from 'next/link'

import { PageHeader } from '@/components/page-header'
import { Button } from '@/components/ui/button'

export const metadata: Metadata = {
  title: 'About',
  description:
    'About Gaia Fiscal Intelligence: independent Nigerian fiscal data and institutional research.',
}

export default function AboutPage() {
  return (
    <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
      <PageHeader
        eyebrow="About Us"
        title="Gaia Fiscal Intelligence"
        description="Independent research platform for verified Nigerian fiscal data and institutional evidence."
      />

      <div className="mt-16 space-y-20">
        {/* Hero Statement */}
        <section className="grid gap-12 lg:grid-cols-2 lg:gap-16 items-center">
          <div>
            <div className="inline-block mb-4 px-3 py-1 bg-amber-400/10 border border-amber-400/30 rounded text-amber-900 text-xs font-semibold tracking-widest">
              INDEPENDENT EVIDENCE INFRASTRUCTURE
            </div>
            <h2 className="font-serif text-4xl font-bold leading-tight mb-6 text-foreground">
              Fiscal transparency backed by retained sources
            </h2>
            <p className="text-lg text-muted-foreground mb-4 leading-relaxed">
              GaiaFAAC is an independent research platform dedicated to bringing cryptographic evidence and accountability to Nigerian fiscal data. We retain every important number's primary source, verify it deterministically, and publish only after human review.
            </p>
            <p className="text-muted-foreground leading-relaxed">
              We do not interpolate, invent, or silently infer financial data. Missing is not zero. Every record carries proof of its source, timestamp, reviewer, and publication date.
            </p>
          </div>
          <div className="space-y-4">
            <div className="border-l-4 border-amber-400 pl-6 py-4">
              <div className="text-3xl font-bold text-foreground mb-1">37/37</div>
              <div className="text-sm text-muted-foreground">Nigerian jurisdictions covered with governed evidence</div>
            </div>
            <div className="border-l-4 border-teal-600 pl-6 py-4">
              <div className="text-3xl font-bold text-foreground mb-1">100%</div>
              <div className="text-sm text-muted-foreground">FAAC data retained with cryptographic proof</div>
            </div>
            <div className="border-l-4 border-emerald-600 pl-6 py-4">
              <div className="text-3xl font-bold text-foreground mb-1">Human-reviewed</div>
              <div className="text-sm text-muted-foreground">Mandatory four-eyes approval before publication</div>
            </div>
          </div>
        </section>

        {/* Core Principles */}
        <section className="border-t border-b border-border py-16">
          <h2 className="font-serif text-3xl font-bold mb-12 text-foreground">Core Principles</h2>
          <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-5">
            <div className="space-y-3">
              <div className="text-2xl text-amber-400 font-bold">01</div>
              <h3 className="font-semibold text-foreground">Evidence First</h3>
              <p className="text-sm text-muted-foreground">
                All claims rooted in verifiable primary source documentation with retained bytes and SHA-256 proof.
              </p>
            </div>
            <div className="space-y-3">
              <div className="text-2xl text-amber-400 font-bold">02</div>
              <h3 className="font-semibold text-foreground">Immutable Record</h3>
              <p className="text-sm text-muted-foreground">
                Cryptographic preservation of source history, publication lineage, and revision tracking.
              </p>
            </div>
            <div className="space-y-3">
              <div className="text-2xl text-amber-400 font-bold">03</div>
              <h3 className="font-semibold text-foreground">Human Authority</h3>
              <p className="text-sm text-muted-foreground">
                Mandatory review and four-eyes approval for all governed publications. No automated disclosure.
              </p>
            </div>
            <div className="space-y-3">
              <div className="text-2xl text-amber-400 font-bold">04</div>
              <h3 className="font-semibold text-foreground">Independent</h3>
              <p className="text-sm text-muted-foreground">
                Not an official government service. Neutral research platform serving institutions and public.
              </p>
            </div>
            <div className="space-y-3">
              <div className="text-2xl text-amber-400 font-bold">05</div>
              <h3 className="font-semibold text-foreground">Reconciliation</h3>
              <p className="text-sm text-muted-foreground">
                Conflicting evidence retained and flagged. Revisions transparent and explained in writing.
              </p>
            </div>
          </div>
        </section>

        {/* What We Do */}
        <section>
          <h2 className="font-serif text-3xl font-bold mb-12 text-foreground">Evidence Domains</h2>
          <div className="grid gap-8 md:grid-cols-3">
            <div className="rounded border border-border/50 p-8 hover:border-amber-400/50 transition-colors">
              <h3 className="font-semibold text-lg mb-3 text-foreground">Federal Allocations</h3>
              <p className="text-sm text-muted-foreground mb-4 leading-relaxed">
                FAAC distributions, state disbursements, and quarterly allocations with complete source registry and reconciliation findings.
              </p>
              <Link href="/live" className="text-sm text-primary font-medium hover:underline">
                Browse allocations →
              </Link>
            </div>
            <div className="rounded border border-border/50 p-8 hover:border-amber-400/50 transition-colors">
              <h3 className="font-semibold text-lg mb-3 text-foreground">Institutional Workflows</h3>
              <p className="text-sm text-muted-foreground mb-4 leading-relaxed">
                Decision Packets, audit tools, evidence registries, and API access for banks, auditors, and agencies.
              </p>
              <Link href="/institutional" className="text-sm text-primary font-medium hover:underline">
                Institutional programs →
              </Link>
            </div>
            <div className="rounded border border-border/50 p-8 hover:border-amber-400/50 transition-colors">
              <h3 className="font-semibold text-lg mb-3 text-foreground">Intelligence & Analysis</h3>
              <p className="text-sm text-muted-foreground mb-4 leading-relaxed">
                Fiscal Pulse signals, state profiles, and grounded AI-assisted research over governed evidence.
              </p>
              <Link href="/fiscal-pulse" className="text-sm text-primary font-medium hover:underline">
                Explore Intelligence →
              </Link>
            </div>
          </div>
        </section>

        {/* Evidence Chain */}
        <section className="bg-muted/30 rounded-lg border border-border p-12">
          <h2 className="font-serif text-3xl font-bold mb-8 text-foreground">How Publication Works</h2>
          <div className="space-y-6">
            <p className="text-muted-foreground leading-relaxed">
              Our evidence chain preserves financial data from its authoritative primary source through cryptographic proof and publication:
            </p>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-6">
              {[
                { step: 'Source', desc: 'Official government document' },
                { step: 'Hash', desc: 'SHA-256 proof' },
                { step: 'Extract', desc: 'Deterministic parsing' },
                { step: 'Validate', desc: 'Reconciliation check' },
                { step: 'Review', desc: 'Human approval' },
                { step: 'Publish', desc: 'Certificate issued' },
              ].map((stage, idx) => (
                <div key={idx}>
                  <div className="text-xs font-semibold text-amber-400 tracking-widest mb-2">STEP {idx + 1}</div>
                  <div className="font-semibold text-foreground text-sm mb-1">{stage.step}</div>
                  <div className="text-xs text-muted-foreground">{stage.desc}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* CTA */}
        <section className="text-center space-y-6">
          <div>
            <h2 className="font-serif text-3xl font-bold mb-3 text-foreground">Ready to explore?</h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              Browse live fiscal data, request institutional access, or explore our full methodology and evidence registry.
            </p>
          </div>
          <div className="flex gap-4 justify-center flex-wrap">
            <Button asChild>
              <Link href="/live">Browse Live Data</Link>
            </Button>
            <Button asChild variant="outline">
              <Link href="/contact">Get in Touch</Link>
            </Button>
            <Button asChild variant="outline">
              <Link href="/methodology">Read Methodology</Link>
            </Button>
          </div>
        </section>
      </div>
    </div>
  )
}
