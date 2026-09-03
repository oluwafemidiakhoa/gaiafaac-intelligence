import type { Metadata } from 'next'
import Link from 'next/link'

import { PageHeader } from '@/components/page-header'

export const metadata: Metadata = {
  title: 'Documentation',
  description:
    'Complete guides for using GaiaFAAC Intelligence, APIs, and institutional workflows.',
}

export default function DocumentationPage() {
  const docs = [
    {
      num: '01',
      title: 'Getting Started',
      description: 'Introduction to GaiaFAAC and key concepts',
      href: '/methodology',
    },
    {
      num: '02',
      title: 'API Reference',
      description: 'Complete REST API documentation and examples',
      href: '/api-access',
    },
    {
      num: '03',
      title: 'Institutional Workflows',
      description: 'Guides for banks, auditors, and government agencies',
      href: '/institutional',
    },
    {
      num: '04',
      title: 'Data & Analysis',
      description: 'Understanding fiscal signals and metrics',
      href: '/fiscal-pulse',
    },
    {
      num: '05',
      title: 'Methodology',
      description: 'How data is sourced, verified, and published',
      href: '/methodology',
    },
    {
      num: '06',
      title: 'Integration',
      description: 'Embed GaiaFAAC data in your applications',
      href: '/api-access',
    },
  ]

  return (
    <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
      <div className="mt-8 space-y-20">
        {/* Hero */}
        <section className="grid gap-12 lg:grid-cols-2 lg:gap-16 items-center">
          <div>
            <h1 className="font-serif text-5xl lg:text-6xl font-bold leading-tight mb-6 text-foreground">
              Complete documentation
            </h1>
            <p className="text-lg text-muted-foreground mb-4 leading-relaxed">
              Everything you need to understand and use GaiaFAAC Intelligence—from platform overview to institutional workflows and technical API integration.
            </p>
          </div>
          <div className="space-y-4">
            <div className="border-l-4 border-teal-600 pl-6 py-4">
              <div className="text-xs font-bold text-teal-600 tracking-widest mb-2">TOTAL DOCS</div>
              <div className="text-4xl font-bold text-foreground mb-1">6</div>
              <div className="text-sm text-muted-foreground">Complete documentation guides</div>
            </div>
            <div className="border-l-4 border-amber-400 pl-6 py-4">
              <div className="text-xs font-bold text-amber-600 tracking-widest mb-2">SECTIONS</div>
              <div className="text-4xl font-bold text-foreground mb-1">20+</div>
              <div className="text-sm text-muted-foreground">Detailed reference topics</div>
            </div>
            <div className="border-l-4 border-emerald-600 pl-6 py-4">
              <div className="text-xs font-bold text-emerald-700 tracking-widest mb-2">EXAMPLES</div>
              <div className="text-4xl font-bold text-foreground mb-1">30+</div>
              <div className="text-sm text-muted-foreground">Code samples & workflows</div>
            </div>
          </div>
        </section>

        {/* Docs Grid */}
        <section>
          <div className="mb-12">
            <div className="text-xs font-bold text-amber-400 tracking-widest mb-3">GUIDES</div>
            <h2 className="font-serif text-4xl font-bold leading-tight text-foreground">
              Browse topics
            </h2>
          </div>
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {docs.map((doc) => (
              <Link key={doc.num} href={doc.href} className="group border-l-4 border-teal-600 pl-6 py-6 hover:border-amber-400 transition-colors">
                <div className="text-xs font-bold text-amber-400 tracking-widest mb-2">{doc.num}</div>
                <div className="font-semibold text-foreground group-hover:text-amber-600 transition-colors mb-2">{doc.title}</div>
                <div className="text-sm text-muted-foreground">{doc.description}</div>
              </Link>
            ))}
          </div>
        </section>

        {/* Key Resources */}
        <section className="border-t border-border pt-16">
          <div className="mb-12">
            <div className="text-xs font-bold text-amber-400 tracking-widest mb-3">RESOURCES</div>
            <h2 className="font-serif text-4xl font-bold leading-tight text-foreground">
              Primary references
            </h2>
          </div>
          <div className="grid gap-6 md:grid-cols-2">
            <Link href="/methodology" className="group border-l-4 border-teal-600 pl-6 py-6 hover:border-amber-400 transition-colors">
              <div className="font-semibold text-foreground group-hover:text-amber-600 transition-colors">Methodology</div>
              <div className="text-sm text-muted-foreground mt-2">Complete evidence chain and verification process →</div>
            </Link>
            <Link href="/sources" className="group border-l-4 border-teal-600 pl-6 py-6 hover:border-amber-400 transition-colors">
              <div className="font-semibold text-foreground group-hover:text-amber-600 transition-colors">Evidence Registry</div>
              <div className="text-sm text-muted-foreground mt-2">Inspect primary sources and publication lineage →</div>
            </Link>
          </div>
        </section>

        {/* Support */}
        <section className="border-t border-b border-border py-12">
          <div className="text-center space-y-6">
            <h2 className="font-serif text-3xl font-bold text-foreground">Can't find what you need?</h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              Our support team provides detailed guidance on implementing GaiaFAAC in your workflows.
            </p>
            <Link href="/contact" className="text-primary font-medium hover:underline">
              Contact support →
            </Link>
          </div>
        </section>
      </div>
    </div>
  )
}
