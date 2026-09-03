import type { Metadata } from 'next'
import Link from 'next/link'

import { PageHeader } from '@/components/page-header'
import { Button } from '@/components/ui/button'

export const metadata: Metadata = {
  title: 'Contact',
  description:
    'Contact Gaia Fiscal Intelligence for API access, partnerships, research collaboration, or institutional support.',
}

export default function ContactPage() {
  return (
    <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
      <PageHeader
        eyebrow="Get Support"
        title="Contact Us"
        description="Reach out for API access, partnerships, research collaboration, or institutional support."
      />

      <div className="mt-16 space-y-20">
        {/* Contact Channels */}
        <section>
          <h2 className="font-serif text-3xl font-bold mb-12 text-foreground">Support Channels</h2>

          <div className="grid gap-8 md:grid-cols-2">
            {/* API & Development */}
            <div className="border border-border rounded-lg p-8 hover:border-amber-400/50 transition-colors">
              <div className="inline-block mb-4 px-3 py-1 bg-blue-400/10 border border-blue-400/30 rounded text-blue-900 text-xs font-semibold tracking-widest">
                DEVELOPERS
              </div>
              <h3 className="font-semibold text-xl mb-3 text-foreground">API & Integration</h3>
              <p className="text-sm text-muted-foreground mb-6 leading-relaxed">
                For REST API documentation, credential requests, data export configuration, and technical integration support.
              </p>
              <Button asChild size="sm">
                <Link href="/api-access">View API Docs</Link>
              </Button>
            </div>

            {/* Institutional Access */}
            <div className="border border-border rounded-lg p-8 hover:border-amber-400/50 transition-colors">
              <div className="inline-block mb-4 px-3 py-1 bg-amber-400/10 border border-amber-400/30 rounded text-amber-900 text-xs font-semibold tracking-widest">
                INSTITUTIONS
              </div>
              <h3 className="font-semibold text-xl mb-3 text-foreground">Fiscal Watch Access</h3>
              <p className="text-sm text-muted-foreground mb-6 leading-relaxed">
                For banks, auditors, government agencies, and development institutions requesting Decision Packets and audit tools.
              </p>
              <Button asChild size="sm">
                <Link href="/pilot">Request Access</Link>
              </Button>
            </div>

            {/* Research & Partnership */}
            <div className="border border-border rounded-lg p-8 hover:border-amber-400/50 transition-colors">
              <div className="inline-block mb-4 px-3 py-1 bg-emerald-400/10 border border-emerald-400/30 rounded text-emerald-900 text-xs font-semibold tracking-widest">
                RESEARCH
              </div>
              <h3 className="font-semibold text-xl mb-3 text-foreground">Academic & Partnerships</h3>
              <p className="text-sm text-muted-foreground mb-6 leading-relaxed">
                For academic research, media partnerships, data collaboration, and methodology inquiries.
              </p>
              <Button asChild size="sm" variant="outline">
                <a href="mailto:research@gaiafaac.org">research@gaiafaac.org</a>
              </Button>
            </div>

            {/* General Inquiry */}
            <div className="border border-border rounded-lg p-8 hover:border-amber-400/50 transition-colors">
              <div className="inline-block mb-4 px-3 py-1 bg-slate-400/10 border border-slate-400/30 rounded text-slate-900 text-xs font-semibold tracking-widest">
                GENERAL
              </div>
              <h3 className="font-semibold text-xl mb-3 text-foreground">Support & Feedback</h3>
              <p className="text-sm text-muted-foreground mb-6 leading-relaxed">
                For general inquiries, platform feedback, or support requests.
              </p>
              <Button asChild size="sm" variant="outline">
                <a href="mailto:support@gaiafaac.org">support@gaiafaac.org</a>
              </Button>
            </div>
          </div>
        </section>

        {/* Quick Navigation */}
        <section className="border-t border-b border-border py-16">
          <h2 className="font-serif text-3xl font-bold mb-12 text-foreground">Explore GaiaFAAC</h2>

          <div className="grid gap-6 md:grid-cols-2">
            <a href="/live" className="group rounded border border-border/50 p-8 hover:border-amber-400/50 hover:bg-muted/30 transition-all">
              <h3 className="font-semibold text-foreground mb-3 group-hover:text-amber-600">Live Fiscal Data</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Browse FAAC allocations, state profiles, and real-time fiscal analysis across all 37 jurisdictions.
              </p>
              <span className="text-sm text-primary font-medium">Browse data →</span>
            </a>

            <a href="/methodology" className="group rounded border border-border/50 p-8 hover:border-amber-400/50 hover:bg-muted/30 transition-all">
              <h3 className="font-semibold text-foreground mb-3 group-hover:text-amber-600">Methodology</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Understand how we source, verify, reconcile, and publish evidence with cryptographic proof.
              </p>
              <span className="text-sm text-primary font-medium">Learn more →</span>
            </a>

            <a href="/sources" className="group rounded border border-border/50 p-8 hover:border-amber-400/50 hover:bg-muted/30 transition-all">
              <h3 className="font-semibold text-foreground mb-3 group-hover:text-amber-600">Evidence Registry</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Inspect primary sources, publication lineage, and complete audit trails for every record.
              </p>
              <span className="text-sm text-primary font-medium">View registry →</span>
            </a>

            <a href="/gaia-analyst" className="group rounded border border-border/50 p-8 hover:border-amber-400/50 hover:bg-muted/30 transition-all">
              <h3 className="font-semibold text-foreground mb-3 group-hover:text-amber-600">Gaia Analyst</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Ask grounded questions and get AI-assisted analysis backed by verified evidence and citations.
              </p>
              <span className="text-sm text-primary font-medium">Ask Gaia →</span>
            </a>
          </div>
        </section>

        {/* FAQ */}
        <section>
          <h2 className="font-serif text-3xl font-bold mb-12 text-foreground">Common Questions</h2>

          <div className="grid gap-8 md:grid-cols-2">
            <div className="space-y-4">
              <div>
                <h3 className="font-semibold text-foreground mb-2">Is GaiaFAAC an official government platform?</h3>
                <p className="text-sm text-muted-foreground">
                  No. GaiaFAAC is an independent, non-governmental research platform. We retain and verify evidence from official primary sources but are not a government service.
                </p>
              </div>

              <div>
                <h3 className="font-semibold text-foreground mb-2">How do I access the API?</h3>
                <p className="text-sm text-muted-foreground">
                  Visit <Link href="/api-access" className="underline text-primary">API Access</Link> to view documentation and request credentials. We support REST endpoints, CSV/Excel exports, and webhooks.
                </p>
              </div>

              <div>
                <h3 className="font-semibold text-foreground mb-2">Can I download historical data?</h3>
                <p className="text-sm text-muted-foreground">
                  Yes. Data Exports include historical snapshots, custom date ranges, evidence metadata, and SHA-256 verification in CSV and Excel formats.
                </p>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <h3 className="font-semibold text-foreground mb-2">How is data verified?</h3>
                <p className="text-sm text-muted-foreground">
                  Every record is retained from its primary source, hashed cryptographically, validated deterministically, reconciled against governed evidence, and subjected to mandatory human review before publication.
                </p>
              </div>

              <div>
                <h3 className="font-semibold text-foreground mb-2">What is Fiscal Watch?</h3>
                <p className="text-sm text-muted-foreground">
                  Fiscal Watch is our institutional program offering Decision Packets, audit tools, real-time alerts, and custom analysis for banks, auditors, governments, and development institutions.
                </p>
              </div>

              <div>
                <h3 className="font-semibold text-foreground mb-2">Can academics use GaiaFAAC?</h3>
                <p className="text-sm text-muted-foreground">
                  Absolutely. We support academic research partnerships and data collaboration. Contact research@gaiafaac.org with your project details.
                </p>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}
