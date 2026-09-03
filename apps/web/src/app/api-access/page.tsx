import type { Metadata } from 'next'
import Link from 'next/link'

import { PageHeader } from '@/components/page-header'
import { Button } from '@/components/ui/button'

export const metadata: Metadata = {
  title: 'API Access',
  description:
    'Integrate verified Nigerian fiscal data into your systems with our robust REST API.',
}

export default function APIAccessPage() {
  return (
    <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
      <PageHeader
        eyebrow="Developer Access"
        title="Integrate verified fiscal data via API"
        description="Build institutional workflows and applications with governed evidence from GaiaFAAC."
      />

      <div className="mt-16 space-y-20">
        {/* API Methods */}
        <section>
          <h2 className="font-serif text-3xl font-bold mb-12 text-foreground">Integration Methods</h2>

          <div className="grid gap-8 md:grid-cols-2">
            <div className="border border-border rounded-lg p-8 hover:border-amber-400/50 transition-colors">
              <div className="flex items-start justify-between mb-6">
                <div>
                  <h3 className="font-semibold text-xl text-foreground">REST API</h3>
                  <p className="text-xs text-muted-foreground mt-1">JSON endpoints</p>
                </div>
                <div className="text-3xl text-amber-400 font-bold opacity-20">◇</div>
              </div>
              <p className="text-muted-foreground mb-6 leading-relaxed">
                Query published FAAC allocations, state profiles, fiscal events, and institutional evidence through comprehensive REST endpoints with full lineage tracking.
              </p>
              <ul className="space-y-2 text-sm mb-8">
                <li className="flex items-start gap-3">
                  <span className="text-emerald-600 font-bold text-lg leading-none">✓</span>
                  <span className="text-muted-foreground">Real-time verified data access with pagination</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-emerald-600 font-bold text-lg leading-none">✓</span>
                  <span className="text-muted-foreground">Full audit trail and source lineage included</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-emerald-600 font-bold text-lg leading-none">✓</span>
                  <span className="text-muted-foreground">Advanced filtering and date range support</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-emerald-600 font-bold text-lg leading-none">✓</span>
                  <span className="text-muted-foreground">Webhook subscriptions for event notifications</span>
                </li>
              </ul>
              <Button asChild>
                <Link href="/documentation">View Endpoints</Link>
              </Button>
            </div>

            <div className="border border-border rounded-lg p-8 hover:border-amber-400/50 transition-colors">
              <div className="flex items-start justify-between mb-6">
                <div>
                  <h3 className="font-semibold text-xl text-foreground">Data Exports</h3>
                  <p className="text-xs text-muted-foreground mt-1">CSV & Excel</p>
                </div>
                <div className="text-3xl text-amber-400 font-bold opacity-20">▦</div>
              </div>
              <p className="text-muted-foreground mb-6 leading-relaxed">
                Download complete datasets in CSV and Excel formats for offline analysis, institutional reporting, and historical research with verified integrity.
              </p>
              <ul className="space-y-2 text-sm mb-8">
                <li className="flex items-start gap-3">
                  <span className="text-emerald-600 font-bold text-lg leading-none">✓</span>
                  <span className="text-muted-foreground">Historical data snapshots by period</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-emerald-600 font-bold text-lg leading-none">✓</span>
                  <span className="text-muted-foreground">Custom date ranges and jurisdiction filters</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-emerald-600 font-bold text-lg leading-none">✓</span>
                  <span className="text-muted-foreground">Evidence metadata and revision history included</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-emerald-600 font-bold text-lg leading-none">✓</span>
                  <span className="text-muted-foreground">SHA-256 verification for data integrity</span>
                </li>
              </ul>
              <Button asChild variant="outline">
                <Link href="/pilot">Request Export Access</Link>
              </Button>
            </div>
          </div>
        </section>

        {/* Authentication & Security */}
        <section className="border-t border-border pt-16">
          <h2 className="font-serif text-3xl font-bold mb-12 text-foreground">Authentication & Security</h2>

          <div className="grid gap-8 md:grid-cols-3">
            <div className="space-y-4">
              <div className="text-2xl font-bold text-amber-400">01</div>
              <h3 className="font-semibold text-foreground">API Keys</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Request API credentials through our institutional access program. Keys are issued with scoped permissions and usage limits.
              </p>
            </div>
            <div className="space-y-4">
              <div className="text-2xl font-bold text-amber-400">02</div>
              <h3 className="font-semibold text-foreground">Rate Limiting</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Standard tier: 100 requests/minute. Enterprise tier: custom limits. All requests include usage headers and quota tracking.
              </p>
            </div>
            <div className="space-y-4">
              <div className="text-2xl font-bold text-amber-400">03</div>
              <h3 className="font-semibold text-foreground">HTTPS & Verification</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                All API traffic encrypted over TLS 1.3. Response payloads include cryptographic proof of source and publication authority.
              </p>
            </div>
          </div>
        </section>

        {/* Example Usage */}
        <section className="bg-muted/40 rounded-lg border border-border p-12">
          <h2 className="font-serif text-2xl font-bold mb-6 text-foreground">Example: Query FAAC Allocations</h2>
          <div className="bg-foreground/5 rounded border border-border/50 p-6 font-mono text-xs overflow-x-auto">
            <code className="text-muted-foreground">
              <div>curl -H "Authorization: Bearer YOUR_API_KEY" \</div>
              <div>  "https://api.gaiafaac.org/v1/allocations?period=2024-06&state=Lagos"</div>
              <div className="mt-4 text-emerald-600">
                <div>{"{"}</div>
                <div>  "allocations": [</div>
                <div>    {"{"}</div>
                <div>      "state": "Lagos",</div>
                <div>      "period": "2024-06",</div>
                <div>      "amount": 15700000000,</div>
                <div>      "source_url": "https://...",</div>
                <div>      "sha256": "abc123...",</div>
                <div>      "published_at": "2024-06-15T10:30:00Z",</div>
                <div>      "reviewer": "team@gaiafaac.org"</div>
                <div>    {"}"}</div>
                <div>  ]</div>
                <div>{"}"}</div>
              </div>
            </code>
          </div>
        </section>

        {/* CTA Section */}
        <section className="border-t border-b border-border py-16">
          <div className="text-center space-y-6">
            <h2 className="font-serif text-3xl font-bold text-foreground">Ready to integrate?</h2>
            <p className="text-muted-foreground max-w-2xl mx-auto leading-relaxed">
              Request API credentials and receive dedicated developer support for your institution. We provide documentation, sandbox environments, and implementation assistance.
            </p>
            <div className="flex gap-4 justify-center flex-wrap">
              <Button asChild size="lg">
                <Link href="/pilot">Request API Access</Link>
              </Button>
              <Button asChild variant="outline" size="lg">
                <Link href="/documentation">View Full Docs</Link>
              </Button>
            </div>
          </div>
        </section>

        {/* Support */}
        <section>
          <h2 className="font-serif text-3xl font-bold mb-8 text-foreground">Technical Support</h2>
          <div className="grid gap-8 md:grid-cols-2">
            <div className="border border-border/50 rounded p-8">
              <h3 className="font-semibold text-foreground mb-4">Developer Documentation</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Complete API reference, code examples in multiple languages, and integration guides available on our documentation site.
              </p>
              <Link href="/documentation" className="text-sm text-primary font-medium hover:underline">
                Read documentation →
              </Link>
            </div>
            <div className="border border-border/50 rounded p-8">
              <h3 className="font-semibold text-foreground mb-4">Get Help</h3>
              <p className="text-sm text-muted-foreground mb-4">
                Contact our support team for questions, troubleshooting, or implementation guidance.
              </p>
              <a href="mailto:support@gaiafaac.org" className="text-sm text-primary font-medium hover:underline">
                Email support@gaiafaac.org →
              </a>
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}
