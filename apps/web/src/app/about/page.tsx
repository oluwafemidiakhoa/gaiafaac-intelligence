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

      <div className="mt-12 space-y-12">
        {/* Mission */}
        <section className="grid gap-8 md:grid-cols-2 md:gap-12 items-center">
          <div>
            <h2 className="font-bold text-2xl mb-4">Our Mission</h2>
            <p className="text-muted-foreground mb-4">
              GaiaFAAC Intelligence is an independent research platform dedicated to bringing transparency and accountability to Nigerian fiscal data. We believe that verified, auditable financial evidence is essential for informed decision-making across government, banking, development institutions, research organizations, and civil society.
            </p>
            <p className="text-muted-foreground">
              Every number published through GaiaFAAC is retained from its primary source, preserved as cryptographic proof, and subjected to rigorous human review before publication. We do not interpolate, invent, or silently infer financial data.
            </p>
          </div>
          <div className="rounded-lg border border-border p-8 bg-muted/50">
            <h3 className="font-semibold text-lg mb-4">Core Principles</h3>
            <ul className="space-y-3 text-sm">
              <li className="flex items-start gap-3">
                <span className="text-primary mt-1 font-bold">•</span>
                <span><strong>Evidence First:</strong> All claims rooted in verifiable primary source documentation</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="text-primary mt-1 font-bold">•</span>
                <span><strong>Immutable Proof:</strong> Cryptographic preservation of source history and publication lineage</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="text-primary mt-1 font-bold">•</span>
                <span><strong>Human Authority:</strong> Mandatory review and four-eyes approval for all governed publications</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="text-primary mt-1 font-bold">•</span>
                <span><strong>Independent:</strong> Not an official government service; neutral research platform</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="text-primary mt-1 font-bold">•</span>
                <span><strong>Accountable:</strong> Transparent methodology and reconciliation for all revisions</span>
              </li>
            </ul>
          </div>
        </section>

        {/* What We Do */}
        <section>
          <h2 className="font-bold text-2xl mb-6">What We Do</h2>
          <div className="grid gap-6 md:grid-cols-3">
            <div className="rounded-lg border border-border p-6">
              <h3 className="font-semibold text-lg mb-3">Federal Allocations</h3>
              <p className="text-sm text-muted-foreground">
                Publish verified FAAC allocation evidence, state disbursement records, and quarterly distribution data with complete source lineage and revision history.
              </p>
            </div>
            <div className="rounded-lg border border-border p-6">
              <h3 className="font-semibold text-lg mb-3">Institutional Workflows</h3>
              <p className="text-sm text-muted-foreground">
                Support banks, auditors, government agencies, and researchers with Decision Packets, audit tools, evidence registries, and institutional API access.
              </p>
            </div>
            <div className="rounded-lg border border-border p-6">
              <h3 className="font-semibold text-lg mb-3">Intelligence & Analysis</h3>
              <p className="text-sm text-muted-foreground">
                Deliver Fiscal Pulse signals, state profiles, allocation analysis, and grounded AI-assisted research over governed evidence with full audit trails.
              </p>
            </div>
          </div>
        </section>

        {/* How It Works */}
        <section>
          <h2 className="font-bold text-2xl mb-6">Evidence Chain</h2>
          <div className="space-y-4">
            <p className="text-muted-foreground">
              Our evidence chain preserves financial data from its primary source through publication and beyond:
            </p>
            <div className="rounded-lg border border-border p-6 bg-muted/30">
              <code className="text-xs font-mono leading-relaxed block text-muted-foreground">
                <div>source → SHA-256 hash → archive</div>
                <div>→ deterministic extraction → reconciliation</div>
                <div>→ human review → four-eyes approval</div>
                <div>→ immutable certificate → public API</div>
                <div>→ analytics & intelligence</div>
              </code>
            </div>
            <p className="text-sm text-muted-foreground mt-4">
              Every published record carries cryptographic proof of its source, timestamp, review authority, and publication date. Revisions are tracked and explained. Missing data remains missing; unavailable sources are reported transparently.
            </p>
          </div>
        </section>

        {/* Contact CTA */}
        <section className="rounded-lg border border-border bg-muted/50 p-8">
          <h2 className="font-bold text-xl mb-4">Work With Us</h2>
          <p className="text-muted-foreground mb-6">
            GaiaFAAC serves researchers, institutions, government agencies, and the public. We offer API access, custom data exports, institutional workflows, and research collaboration.
          </p>
          <Button asChild size="lg">
            <Link href="/contact">Get in Touch</Link>
          </Button>
        </section>
      </div>
    </div>
  )
}
