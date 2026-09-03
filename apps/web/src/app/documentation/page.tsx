import type { Metadata } from 'next'
import Link from 'next/link'

import { PageHeader } from '@/components/page-header'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'

export const metadata: Metadata = {
  title: 'Documentation',
  description:
    'Complete guides for using GaiaFAAC Intelligence, APIs, and institutional workflows.',
}

export default function DocumentationPage() {
  const docs = [
    {
      title: 'Getting Started',
      description: 'Introduction to GaiaFAAC and key concepts',
      links: [
        { label: 'Platform Overview', href: '/methodology' },
        { label: 'Key Terminology', href: '/methodology' },
        { label: 'Data Structure', href: '/methodology' },
      ],
    },
    {
      title: 'API Reference',
      description: 'Complete REST API documentation and examples',
      links: [
        { label: 'Authentication', href: '/api-access' },
        { label: 'Endpoints', href: '/api-access' },
        { label: 'Response Formats', href: '/api-access' },
      ],
    },
    {
      title: 'Institutional Workflows',
      description: 'Guides for banks, auditors, and government agencies',
      links: [
        { label: 'Evidence Rooms', href: '/evidence-rooms' },
        { label: 'Decision Packets', href: '/decision-packets' },
        { label: 'Audit Tools', href: '/review' },
      ],
    },
    {
      title: 'Data & Analysis',
      description: 'Understanding fiscal signals and metrics',
      links: [
        { label: 'Fiscal Pulse Signals', href: '/fiscal-pulse' },
        { label: 'Allocation Analysis', href: '/insights' },
        { label: 'State Profiles', href: '/overview' },
      ],
    },
    {
      title: 'Methodology',
      description: 'How data is sourced, verified, and published',
      links: [
        { label: 'Evidence Chain', href: '/methodology' },
        { label: 'Review Process', href: '/review' },
        { label: 'Data Quality', href: '/methodology' },
      ],
    },
    {
      title: 'Integration',
      description: 'Embed GaiaFAAC data in your applications',
      links: [
        { label: 'API Integration', href: '/api-access' },
        { label: 'Data Exports', href: '/api-access' },
        { label: 'Webhooks', href: '/api-access' },
      ],
    },
  ]

  return (
    <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
      <PageHeader
        eyebrow="Help & Reference"
        title="Documentation"
        description="Everything you need to understand and use GaiaFAAC Intelligence."
      />

      <div className="mt-16 space-y-20">
        <section>
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {docs.map((doc, idx) => (
              <div key={doc.title} className="group rounded-lg border border-border/50 p-8 hover:border-amber-400/50 hover:bg-muted/30 transition-all">
                <div className="text-sm font-semibold text-amber-400 tracking-widest mb-3">
                  {String(idx + 1).padStart(2, '0')}
                </div>
                <h3 className="font-semibold text-lg text-foreground mb-2">{doc.title}</h3>
                <p className="text-sm text-muted-foreground mb-6">{doc.description}</p>
                <nav className="space-y-2 border-t border-border/30 pt-6">
                  {doc.links.map((link) => (
                    <Link
                      key={link.label}
                      href={link.href}
                      className="flex items-center justify-between text-sm text-muted-foreground hover:text-primary transition-colors py-1"
                    >
                      <span>{link.label}</span>
                      <span className="text-xs">→</span>
                    </Link>
                  ))}
                </nav>
              </div>
            ))}
          </div>
        </section>

        {/* Search & Navigate */}
        <section className="border-t border-border pt-16">
          <h2 className="font-serif text-3xl font-bold mb-12 text-foreground">Navigation Guides</h2>
          <div className="grid gap-6 md:grid-cols-2">
            <a href="/methodology" className="group border border-border/50 rounded-lg p-8 hover:border-amber-400/50 hover:bg-muted/30 transition-all">
              <div className="font-semibold text-foreground mb-3 group-hover:text-amber-600">Methodology & Evidence</div>
              <p className="text-sm text-muted-foreground mb-4">Learn how we source, verify, reconcile, and publish fiscal data with cryptographic proof and human review.</p>
              <span className="text-sm text-primary">Read full methodology →</span>
            </a>
            <a href="/sources" className="group border border-border/50 rounded-lg p-8 hover:border-amber-400/50 hover:bg-muted/30 transition-all">
              <div className="font-semibold text-foreground mb-3 group-hover:text-amber-600">Evidence Registry</div>
              <p className="text-sm text-muted-foreground mb-4">Access primary source documents, publication certificates, revision history, and complete lineage for all published records.</p>
              <span className="text-sm text-primary">Inspect sources →</span>
            </a>
          </div>
        </section>

        {/* Support */}
        <section className="bg-muted/40 rounded-lg border border-border p-12 text-center">
          <h2 className="font-serif text-3xl font-bold mb-4 text-foreground">Need Help?</h2>
          <p className="text-muted-foreground max-w-2xl mx-auto mb-8">
            Can't find what you're looking for? Our support team provides detailed guidance on implementing GaiaFAAC in your workflows, research, or institutional systems.
          </p>
          <Link href="/contact" className="text-primary font-medium hover:underline">
            Contact support →
          </Link>
        </section>
      </div>
    </div>
  )
}
