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

      <div className="mt-12 grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {docs.map((doc) => (
          <Card key={doc.title}>
            <CardHeader>
              <CardTitle>{doc.title}</CardTitle>
              <CardDescription>{doc.description}</CardDescription>
            </CardHeader>
            <CardContent>
              <nav className="space-y-2">
                {doc.links.map((link) => (
                  <Link
                    key={link.label}
                    href={link.href}
                    className="block text-sm text-primary hover:underline"
                  >
                    {link.label} →
                  </Link>
                ))}
              </nav>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="mt-12 rounded-lg border border-border bg-muted/50 p-8">
        <h2 className="font-bold text-xl mb-4">Can't find what you need?</h2>
        <p className="text-muted-foreground">
          Contact our support team for detailed guidance on implementing GaiaFAAC in your workflows.
        </p>
        <Link href="/contact" className="text-primary font-medium mt-4 inline-block hover:underline">
          Get Support →
        </Link>
      </div>
    </div>
  )
}
