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

      <div className="mt-12 grid gap-12 md:grid-cols-2 md:gap-16">
        {/* Contact Info */}
        <section>
          <h2 className="font-bold text-xl mb-8">How to Reach Us</h2>

          <div className="space-y-8">
            {/* API & Development */}
            <div>
              <h3 className="font-semibold text-lg mb-3">API & Integration</h3>
              <p className="text-sm text-muted-foreground mb-4">
                For developer documentation, API key requests, data export setup, and technical integration support:
              </p>
              <Button asChild variant="outline" size="sm">
                <Link href="/api-access">View API Documentation</Link>
              </Button>
            </div>

            {/* Institutional Access */}
            <div>
              <h3 className="font-semibold text-lg mb-3">Institutional Programs</h3>
              <p className="text-sm text-muted-foreground mb-4">
                For banks, auditors, government agencies, and development institutions seeking Decision Packets, audit tools, and institutional workflows:
              </p>
              <Button asChild variant="outline" size="sm">
                <Link href="/pilot">Request Fiscal Watch Access</Link>
              </Button>
            </div>

            {/* Research & Partnership */}
            <div>
              <h3 className="font-semibold text-lg mb-3">Research & Partnerships</h3>
              <p className="text-sm text-muted-foreground mb-4">
                For academic research, media partnerships, data collaboration, and methodology inquiries, contact our research team.
              </p>
              <Button asChild variant="outline" size="sm">
                <a href="mailto:research@gaiafaac.org">Email: research@gaiafaac.org</a>
              </Button>
            </div>

            {/* General Inquiry */}
            <div>
              <h3 className="font-semibold text-lg mb-3">General Inquiry</h3>
              <p className="text-sm text-muted-foreground mb-4">
                For other inquiries, feedback, or general support:
              </p>
              <Button asChild variant="outline" size="sm">
                <a href="mailto:support@gaiafaac.org">Email: support@gaiafaac.org</a>
              </Button>
            </div>
          </div>
        </section>

        {/* Quick Contact Options */}
        <section>
          <h2 className="font-bold text-xl mb-8">Quick Actions</h2>

          <div className="space-y-4">
            <div className="rounded-lg border border-border p-6">
              <h3 className="font-semibold mb-2">Explore the Platform</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Dive into live FAAC data, state profiles, and fiscal analysis.
              </p>
              <Button asChild size="sm">
                <Link href="/live">Browse Live Data</Link>
              </Button>
            </div>

            <div className="rounded-lg border border-border p-6">
              <h3 className="font-semibold mb-2">Learn Our Methodology</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Understand how we source, verify, and publish evidence.
              </p>
              <Button asChild size="sm" variant="outline">
                <Link href="/methodology">Read Methodology</Link>
              </Button>
            </div>

            <div className="rounded-lg border border-border p-6">
              <h3 className="font-semibold mb-2">Review Evidence Registry</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Inspect primary sources and publication lineage.
              </p>
              <Button asChild size="sm" variant="outline">
                <Link href="/sources">View Evidence Registry</Link>
              </Button>
            </div>

            <div className="rounded-lg border border-border p-6">
              <h3 className="font-semibold mb-2">Ask Gaia</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Get AI-assisted analysis grounded in verified evidence.
              </p>
              <Button asChild size="sm" variant="outline">
                <Link href="/gaia-analyst">Use Gaia Analyst</Link>
              </Button>
            </div>
          </div>
        </section>
      </div>

      {/* FAQ Section */}
      <section className="mt-16">
        <h2 className="font-bold text-2xl mb-8">Frequently Asked Questions</h2>

        <div className="grid gap-6 md:grid-cols-2">
          <div className="rounded-lg border border-border p-6">
            <h3 className="font-semibold mb-3">Is GaiaFAAC an official government platform?</h3>
            <p className="text-sm text-muted-foreground">
              No. GaiaFAAC Fiscal Intelligence is an independent, non-governmental research platform. We retain and verify evidence from official primary sources, but we are not a government service.
            </p>
          </div>

          <div className="rounded-lg border border-border p-6">
            <h3 className="font-semibold mb-3">How do I access the API?</h3>
            <p className="text-sm text-muted-foreground">
              Visit the <Link href="/api-access" className="underline text-primary">API Access</Link> page to view documentation and request credentials. We support REST endpoints, data exports in CSV and Excel, and webhook subscriptions.
            </p>
          </div>

          <div className="rounded-lg border border-border p-6">
            <h3 className="font-semibold mb-3">Can I download historical data?</h3>
            <p className="text-sm text-muted-foreground">
              Yes. Data Exports provide historical snapshots, custom date ranges, and evidence metadata in CSV and Excel formats with SHA-256 verification for integrity.
            </p>
          </div>

          <div className="rounded-lg border border-border p-6">
            <h3 className="font-semibold mb-3">How is data verified?</h3>
            <p className="text-sm text-muted-foreground">
              Every record is retained from its primary source, preserved with SHA-256 proof, validated deterministically, reconciled against other governed evidence, and subjected to mandatory human review before publication.
            </p>
          </div>

          <div className="rounded-lg border border-border p-6">
            <h3 className="font-semibold mb-3">What is Fiscal Watch?</h3>
            <p className="text-sm text-muted-foreground">
              Fiscal Watch is our institutional program offering Decision Packets, audit tools, real-time alerts, and custom analysis for banks, auditors, governments, and development institutions.
            </p>
          </div>

          <div className="rounded-lg border border-border p-6">
            <h3 className="font-semibold mb-3">Can academic researchers use GaiaFAAC?</h3>
            <p className="text-sm text-muted-foreground">
              Absolutely. We support academic research partnerships and data collaboration. Contact our research team at research@gaiafaac.org to discuss your project.
            </p>
          </div>
        </div>
      </section>
    </div>
  )
}
