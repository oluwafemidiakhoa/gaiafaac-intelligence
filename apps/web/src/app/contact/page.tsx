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
      <div className="mt-8 space-y-20">
        {/* Hero */}
        <section className="grid gap-12 lg:grid-cols-2 lg:gap-16 items-center">
          <div>
            <h1 className="font-serif text-5xl lg:text-6xl font-bold leading-tight mb-6 text-foreground">
              Get in touch with our team
            </h1>
            <p className="text-lg text-muted-foreground mb-4 leading-relaxed">
              Contact us for API credentials, institutional access, research partnerships, or general support.
            </p>
          </div>
          <div className="space-y-4">
            <div className="border-l-4 border-blue-500 pl-6 py-4">
              <div className="text-xs font-bold text-blue-600 tracking-widest mb-2">DEVELOPERS</div>
              <div className="font-semibold text-foreground mb-1">API Access</div>
              <div className="text-sm text-muted-foreground">REST endpoints, webhooks, exports</div>
            </div>
            <div className="border-l-4 border-amber-400 pl-6 py-4">
              <div className="text-xs font-bold text-amber-600 tracking-widest mb-2">INSTITUTIONS</div>
              <div className="font-semibold text-foreground mb-1">Fiscal Watch</div>
              <div className="text-sm text-muted-foreground">Decision Packets, audit tools</div>
            </div>
            <div className="border-l-4 border-emerald-600 pl-6 py-4">
              <div className="text-xs font-bold text-emerald-700 tracking-widest mb-2">RESEARCH</div>
              <div className="font-semibold text-foreground mb-1">Partnerships</div>
              <div className="text-sm text-muted-foreground">Academic & media collaboration</div>
            </div>
          </div>
        </section>

        {/* Contact Channels */}
        <section>
          <div className="mb-12">
            <div className="text-xs font-bold text-amber-400 tracking-widest mb-3">SUPPORT CHANNELS</div>
            <h2 className="font-serif text-4xl font-bold leading-tight text-foreground">
              How to reach us
            </h2>
          </div>
          <div className="grid gap-6 md:grid-cols-2">
            <a href="mailto:support@gaiafaac.org" className="group border-l-4 border-slate-400 pl-6 py-6 hover:border-amber-400 transition-colors">
              <div className="text-xs font-bold text-slate-600 group-hover:text-amber-600 tracking-widest mb-2 transition-colors">GENERAL</div>
              <div className="font-semibold text-foreground mb-1">General Support</div>
              <div className="text-sm text-muted-foreground group-hover:text-foreground transition-colors">support@gaiafaac.org</div>
            </a>
            <a href="mailto:research@gaiafaac.org" className="group border-l-4 border-emerald-600 pl-6 py-6 hover:border-amber-400 transition-colors">
              <div className="text-xs font-bold text-emerald-700 group-hover:text-amber-600 tracking-widest mb-2 transition-colors">RESEARCH</div>
              <div className="font-semibold text-foreground mb-1">Academic & Partnerships</div>
              <div className="text-sm text-muted-foreground group-hover:text-foreground transition-colors">research@gaiafaac.org</div>
            </a>
            <Link href="/api-access" className="group border-l-4 border-blue-500 pl-6 py-6 hover:border-amber-400 transition-colors">
              <div className="text-xs font-bold text-blue-600 group-hover:text-amber-600 tracking-widest mb-2 transition-colors">DEVELOPERS</div>
              <div className="font-semibold text-foreground mb-1">API Documentation</div>
              <div className="text-sm text-muted-foreground group-hover:text-foreground transition-colors">View API docs →</div>
            </Link>
            <Link href="/pilot" className="group border-l-4 border-amber-400 pl-6 py-6 hover:border-teal-600 transition-colors">
              <div className="text-xs font-bold text-amber-600 group-hover:text-teal-600 tracking-widest mb-2 transition-colors">INSTITUTIONS</div>
              <div className="font-semibold text-foreground mb-1">Fiscal Watch Access</div>
              <div className="text-sm text-muted-foreground group-hover:text-foreground transition-colors">Request access →</div>
            </Link>
          </div>
        </section>

        {/* Quick Links */}
        <section className="border-t border-border pt-16">
          <div className="mb-12">
            <div className="text-xs font-bold text-amber-400 tracking-widest mb-3">EXPLORE</div>
            <h2 className="font-serif text-4xl font-bold leading-tight text-foreground">
              Browse GaiaFAAC
            </h2>
          </div>
          <div className="grid gap-6 md:grid-cols-2">
            <Link href="/live" className="group border-l-4 border-teal-600 pl-6 py-6 hover:border-amber-400 transition-colors">
              <div className="font-semibold text-foreground group-hover:text-amber-600 transition-colors">Live Fiscal Data</div>
              <div className="text-sm text-muted-foreground mt-2">Browse FAAC allocations and state profiles →</div>
            </Link>
            <Link href="/methodology" className="group border-l-4 border-teal-600 pl-6 py-6 hover:border-amber-400 transition-colors">
              <div className="font-semibold text-foreground group-hover:text-amber-600 transition-colors">Methodology</div>
              <div className="text-sm text-muted-foreground mt-2">Learn how we verify and publish evidence →</div>
            </Link>
            <Link href="/sources" className="group border-l-4 border-teal-600 pl-6 py-6 hover:border-amber-400 transition-colors">
              <div className="font-semibold text-foreground group-hover:text-amber-600 transition-colors">Evidence Registry</div>
              <div className="text-sm text-muted-foreground mt-2">Inspect sources and publication lineage →</div>
            </Link>
            <Link href="/gaia-analyst" className="group border-l-4 border-teal-600 pl-6 py-6 hover:border-amber-400 transition-colors">
              <div className="font-semibold text-foreground group-hover:text-amber-600 transition-colors">Ask Gaia</div>
              <div className="text-sm text-muted-foreground mt-2">Get AI-assisted analysis with evidence →</div>
            </Link>
          </div>
        </section>
      </div>
    </div>
  )
}
