import { ArrowDown, BellRing, Building2, FileCheck2 } from 'lucide-react'
import type { Metadata } from 'next'

import { PageHeader } from '@/components/page-header'
import { PilotLeadForm } from '@/components/pilot-lead-form'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'

export const metadata: Metadata = {
  title: 'Fiscal Watch — Gaia Fiscal Intelligence',
}

const offers = [
  {
    name: 'Fiscal Watch',
    icon: BellRing,
    audience: 'Banks, investors, insurers, infrastructure teams, and advisers',
    outcome:
      'Monitor selected jurisdictions for evidence-linked allocation movements, source revisions, and governed fiscal signals.',
  },
  {
    name: 'Decision Packets',
    icon: FileCheck2,
    audience: 'Credit, legal, diligence, and research teams',
    outcome:
      'Receive a source-linked fiscal brief for an agreed jurisdiction, period, and decision question.',
  },
  {
    name: 'Institutional Workspace',
    icon: Building2,
    audience: 'Teams that need shared review, alerts, and controlled access',
    outcome:
      'Set up a governed workspace, shared watchlists, and approved evidence access for your organization.',
  },
]

export default function PilotPage() {
  return (
    <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
      <PageHeader
        eyebrow="Gaia Fiscal Watch"
        title="Know what changed before it becomes a surprise."
        description="An institutional monitoring layer for Nigeria’s governed public-finance evidence. Start with the jurisdictions, sources, and decisions your team needs to watch."
      />

      <div className="mt-10 grid gap-5 lg:grid-cols-3">
        {offers.map(({ name, icon: Icon, audience, outcome }) => (
          <Card key={name} className="bg-card/80">
            <CardHeader>
              <Icon className="text-primary size-5" aria-hidden="true" />
              <CardTitle className="pt-3">{name}</CardTitle>
              <CardDescription>{audience}</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground text-sm leading-6">{outcome}</p>
              <Button asChild className="mt-6 w-full">
                <a href="#request-form">
                  Request Fiscal Watch
                  <ArrowDown className="size-4" aria-hidden="true" />
                </a>
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="mt-12 grid gap-8 lg:grid-cols-2">
        <section>
          <h2 className="text-2xl font-semibold tracking-tight">How it works</h2>
          <ol className="text-muted-foreground mt-5 space-y-4 text-sm leading-6">
            <li><span className="text-foreground font-medium">1. Select.</span>{' '}Choose the jurisdictions, reporting periods, and evidence domains that matter.</li>
            <li><span className="text-foreground font-medium">2. Verify.</span>{' '}Gaia monitors retained official records and governed validation outcomes.</li>
            <li><span className="text-foreground font-medium">3. Review.</span>{' '}Your team receives the source trail and a clear statement of what changed.</li>
            <li><span className="text-foreground font-medium">4. Activate.</span>{' '}After scope confirmation, we provision the appropriate workspace, delivery, or API access.</li>
          </ol>
        </section>

        <section className="border-border bg-muted/30 rounded-lg border p-6">
          <h2 className="text-xl font-semibold">What Fiscal Watch does not do</h2>
          <ul className="text-muted-foreground mt-4 space-y-3 text-sm leading-6">
            <li>It does not turn missing public evidence into estimates.</li>
            <li>It does not label a jurisdiction as corrupt, insolvent, or unsafe from a data movement alone.</li>
            <li>It does retain source identity, evidence status, and revision history for serious review.</li>
          </ul>
        </section>
      </div>

      <section id="request-form" className="border-border mt-14 scroll-mt-8 rounded-xl border p-6 sm:p-8">
        <div className="max-w-3xl">
          <p className="text-primary font-mono text-xs font-semibold tracking-[0.18em] uppercase">Institutional request</p>
          <h2 className="mt-3 text-3xl font-semibold tracking-tight">Build your watchlist</h2>
          <p className="text-muted-foreground mt-3 text-sm leading-6">
            Tell us the jurisdictions and evidence you need. Your request is captured for a real commercial follow-up; we confirm the governed coverage and delivery scope before activation.
          </p>
        </div>
        <div className="mt-8 max-w-4xl"><PilotLeadForm /></div>
      </section>

      <p className="text-muted-foreground mt-10 text-sm leading-6">
        Gaia Fiscal Intelligence is an independent research platform, not a government service. Public-source facts remain attributable to their original publishers.
      </p>
    </div>
  )
}
