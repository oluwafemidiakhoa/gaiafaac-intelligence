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
      <div className="mt-8 space-y-20">
        {/* Hero Section */}
        <section className="grid gap-12 lg:grid-cols-2 lg:gap-16 items-center">
          <div>
            <h1 className="font-serif text-5xl lg:text-6xl font-bold leading-tight mb-6 text-foreground">
              Fiscal transparency backed by retained sources
            </h1>
            <p className="text-lg text-muted-foreground mb-6 leading-relaxed">
              GaiaFAAC is an independent research platform dedicated to cryptographic evidence and accountability. Every important number retains its primary source, verified deterministically, published only after human review.
            </p>
            <p className="text-muted-foreground leading-relaxed">
              We do not interpolate, invent, or silently infer. Missing is not zero. Every record carries proof of source, timestamp, reviewer, and publication date.
            </p>
          </div>
          <div className="space-y-4">
            <div className="border-l-4 border-amber-400 pl-6 py-4">
              <div className="text-xs font-bold text-amber-400 tracking-widest mb-2">COVERAGE</div>
              <div className="text-4xl font-bold text-foreground mb-1">37/37</div>
              <div className="text-sm text-muted-foreground">Nigerian jurisdictions with governed evidence</div>
            </div>
            <div className="border-l-4 border-teal-600 pl-6 py-4">
              <div className="text-xs font-bold text-teal-600 tracking-widest mb-2">RETENTION</div>
              <div className="text-4xl font-bold text-foreground mb-1">100%</div>
              <div className="text-sm text-muted-foreground">FAAC data retained with cryptographic proof</div>
            </div>
            <div className="border-l-4 border-emerald-600 pl-6 py-4">
              <div className="text-xs font-bold text-emerald-600 tracking-widest mb-2">CONTROL</div>
              <div className="text-4xl font-bold text-foreground mb-1">Human-reviewed</div>
              <div className="text-sm text-muted-foreground">Mandatory four-eyes approval before publication</div>
            </div>
          </div>
        </section>

        {/* Evidence Process */}
        <section className="grid gap-12 lg:grid-cols-2 lg:gap-16">
          <div className="space-y-6">
            <div>
              <div className="text-xs font-bold text-amber-400 tracking-widest mb-3">EVIDENCE CHAIN</div>
              <h2 className="font-serif text-4xl font-bold leading-tight text-foreground mb-4">
                How publication works
              </h2>
              <p className="text-muted-foreground leading-relaxed">
                Our process preserves fiscal data from authoritative primary source through cryptographic proof and institutional publication.
              </p>
            </div>
          </div>
          <div className="space-y-4">
            {[
              { label: 'SOURCE', desc: 'Official government document' },
              { label: 'HASH', desc: 'SHA-256 cryptographic proof' },
              { label: 'EXTRACT', desc: 'Deterministic parsing' },
              { label: 'VALIDATE', desc: 'Reconciliation check' },
              { label: 'REVIEW', desc: 'Human verification' },
              { label: 'PUBLISH', desc: 'Certificate issued' },
            ].map((step) => (
              <div key={step.label} className="border-l-4 border-amber-400/30 pl-4 py-2">
                <div className="text-xs font-bold text-amber-600 tracking-widest mb-1">{step.label}</div>
                <div className="text-sm text-muted-foreground">{step.desc}</div>
              </div>
            ))}
          </div>
        </section>

        {/* Domains */}
        <section>
          <div className="mb-12">
            <div className="text-xs font-bold text-amber-400 tracking-widest mb-3">EVIDENCE DOMAINS</div>
            <h2 className="font-serif text-4xl font-bold leading-tight text-foreground">
              What we publish
            </h2>
          </div>
          <div className="grid gap-8 md:grid-cols-3">
            <div className="border-l-4 border-teal-600 pl-6 py-6">
              <div className="text-sm font-bold text-teal-600 tracking-widest mb-3">ALLOCATIONS</div>
              <p className="text-muted-foreground text-sm leading-relaxed">
                FAAC distributions, state disbursements, and quarterly allocations with complete source registry and reconciliation findings.
              </p>
            </div>
            <div className="border-l-4 border-teal-600 pl-6 py-6">
              <div className="text-sm font-bold text-teal-600 tracking-widest mb-3">WORKFLOWS</div>
              <p className="text-muted-foreground text-sm leading-relaxed">
                Decision Packets, audit tools, evidence registries, and API access for banks, auditors, and government agencies.
              </p>
            </div>
            <div className="border-l-4 border-teal-600 pl-6 py-6">
              <div className="text-sm font-bold text-teal-600 tracking-widest mb-3">INTELLIGENCE</div>
              <p className="text-muted-foreground text-sm leading-relaxed">
                Fiscal Pulse signals, state profiles, and grounded AI-assisted research over governed evidence.
              </p>
            </div>
          </div>
        </section>

        {/* CTA */}
        <section className="border-t border-b border-border py-12">
          <div className="text-center space-y-6">
            <h2 className="font-serif text-3xl font-bold text-foreground">Ready to explore?</h2>
            <div className="flex gap-4 justify-center flex-wrap">
              <Button asChild>
                <Link href="/live">Browse Data</Link>
              </Button>
              <Button asChild variant="outline">
                <Link href="/contact">Get in Touch</Link>
              </Button>
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}
