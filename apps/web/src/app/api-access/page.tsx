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
      <div className="mt-8 space-y-20">
        {/* Hero */}
        <section className="grid gap-12 lg:grid-cols-2 lg:gap-16 items-center">
          <div>
            <h1 className="font-serif text-5xl lg:text-6xl font-bold leading-tight mb-6 text-foreground">
              Integrate verified fiscal data
            </h1>
            <p className="text-lg text-muted-foreground mb-4 leading-relaxed">
              Build institutional workflows and applications with governed evidence from GaiaFAAC. REST API, data exports, and webhooks with full audit lineage.
            </p>
          </div>
          <div className="space-y-4">
            <div className="border-l-4 border-teal-600 pl-6 py-4">
              <div className="text-xs font-bold text-teal-600 tracking-widest mb-2">REST API</div>
              <div className="text-2xl font-bold text-foreground mb-1">Real-time</div>
              <div className="text-sm text-muted-foreground">JSON endpoints with lineage tracking</div>
            </div>
            <div className="border-l-4 border-teal-600 pl-6 py-4">
              <div className="text-xs font-bold text-teal-600 tracking-widest mb-2">DATA EXPORTS</div>
              <div className="text-2xl font-bold text-foreground mb-1">CSV & Excel</div>
              <div className="text-sm text-muted-foreground">Historical snapshots with verification</div>
            </div>
            <div className="border-l-4 border-teal-600 pl-6 py-4">
              <div className="text-xs font-bold text-teal-600 tracking-widest mb-2">WEBHOOKS</div>
              <div className="text-2xl font-bold text-foreground mb-1">Event streams</div>
              <div className="text-sm text-muted-foreground">Subscriptions for new allocations</div>
            </div>
          </div>
        </section>

        {/* Integration Methods */}
        <section>
          <div className="mb-12">
            <div className="text-xs font-bold text-amber-400 tracking-widest mb-3">METHODS</div>
            <h2 className="font-serif text-4xl font-bold leading-tight text-foreground">
              Access options
            </h2>
          </div>
          <div className="grid gap-8 md:grid-cols-2">
            <div className="border-l-4 border-blue-500 pl-6 py-6">
              <div className="text-sm font-bold text-blue-600 tracking-widest mb-3">REST API</div>
              <p className="text-muted-foreground text-sm mb-4 leading-relaxed">
                Query published FAAC allocations, state profiles, fiscal events, and institutional evidence through comprehensive REST endpoints with pagination, filtering, and full audit trail lineage.
              </p>
              <ul className="space-y-2 text-sm">
                <li className="flex items-start gap-2">
                  <span className="text-emerald-600 font-bold">✓</span>
                  <span className="text-muted-foreground">Real-time verified data</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-emerald-600 font-bold">✓</span>
                  <span className="text-muted-foreground">Complete audit lineage</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-emerald-600 font-bold">✓</span>
                  <span className="text-muted-foreground">Webhook subscriptions</span>
                </li>
              </ul>
            </div>
            <div className="border-l-4 border-amber-400 pl-6 py-6">
              <div className="text-sm font-bold text-amber-600 tracking-widest mb-3">DATA EXPORTS</div>
              <p className="text-muted-foreground text-sm mb-4 leading-relaxed">
                Download complete datasets in CSV and Excel formats for offline analysis, institutional reporting, and historical research with verified integrity.
              </p>
              <ul className="space-y-2 text-sm">
                <li className="flex items-start gap-2">
                  <span className="text-emerald-600 font-bold">✓</span>
                  <span className="text-muted-foreground">Historical snapshots</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-emerald-600 font-bold">✓</span>
                  <span className="text-muted-foreground">Custom date ranges</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-emerald-600 font-bold">✓</span>
                  <span className="text-muted-foreground">SHA-256 verification</span>
                </li>
              </ul>
            </div>
          </div>
        </section>

        {/* Security */}
        <section className="border-t border-border pt-16">
          <div className="mb-12">
            <div className="text-xs font-bold text-amber-400 tracking-widest mb-3">SECURITY</div>
            <h2 className="font-serif text-4xl font-bold leading-tight text-foreground">
              Authentication & rate limits
            </h2>
          </div>
          <div className="grid gap-6 md:grid-cols-3">
            <div className="border-l-4 border-teal-600 pl-6 py-4">
              <div className="text-xs font-bold text-teal-600 tracking-widest mb-2">API KEYS</div>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Request credentials through institutional access program. Keys issued with scoped permissions.
              </p>
            </div>
            <div className="border-l-4 border-teal-600 pl-6 py-4">
              <div className="text-xs font-bold text-teal-600 tracking-widest mb-2">RATE LIMITS</div>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Standard: 100 req/min. Enterprise: custom. All requests tracked with usage headers.
              </p>
            </div>
            <div className="border-l-4 border-teal-600 pl-6 py-4">
              <div className="text-xs font-bold text-teal-600 tracking-widest mb-2">ENCRYPTION</div>
              <p className="text-sm text-muted-foreground leading-relaxed">
                TLS 1.3 for all traffic. Responses include cryptographic proof of source and authority.
              </p>
            </div>
          </div>
        </section>

        {/* CTA */}
        <section className="border-t border-b border-border py-12">
          <div className="text-center space-y-6">
            <h2 className="font-serif text-3xl font-bold text-foreground">Ready to integrate?</h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              Request API credentials and receive dedicated developer support for your institution.
            </p>
            <div className="flex gap-4 justify-center flex-wrap">
              <Button asChild>
                <Link href="/pilot">Request API Access</Link>
              </Button>
              <Button asChild variant="outline">
                <Link href="/documentation">View Docs</Link>
              </Button>
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}
