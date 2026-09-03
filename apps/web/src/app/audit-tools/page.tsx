import type { Metadata } from 'next'
import Link from 'next/link'

import { PageHeader } from '@/components/page-header'
import { Button } from '@/components/ui/button'

export const metadata: Metadata = {
  title: 'Audit Tools',
  description:
    'Comprehensive audit and compliance tools for financial institutions, auditors, and regulators.',
}

export default function AuditToolsPage() {
  return (
    <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
      <div className="mt-8 space-y-20">
        {/* Hero */}
        <section className="grid gap-12 lg:grid-cols-2 lg:gap-16 items-center">
          <div>
            <h1 className="font-serif text-5xl lg:text-6xl font-bold leading-tight mb-6 text-foreground">
              Audit and compliance tools
            </h1>
            <p className="text-lg text-muted-foreground mb-4 leading-relaxed">
              Verify fiscal allocations, reconcile accounts, track revisions, and generate audit reports with complete evidence lineage and four-eyes approval controls.
            </p>
          </div>
          <div className="space-y-4">
            <div className="border-l-4 border-blue-500 pl-6 py-4">
              <div className="text-xs font-bold text-blue-600 tracking-widest mb-2">EVIDENCE LINEAGE</div>
              <div className="text-2xl font-bold text-foreground mb-1">Complete trail</div>
              <div className="text-sm text-muted-foreground">Source to publication with SHA-256</div>
            </div>
            <div className="border-l-4 border-emerald-600 pl-6 py-4">
              <div className="text-xs font-bold text-emerald-700 tracking-widest mb-2">RECONCILIATION</div>
              <div className="text-2xl font-bold text-foreground mb-1">Automated matching</div>
              <div className="text-sm text-muted-foreground">Multi-source alignment and conflict detection</div>
            </div>
            <div className="border-l-4 border-amber-400 pl-6 py-4">
              <div className="text-xs font-bold text-amber-600 tracking-widest mb-2">APPROVAL CONTROL</div>
              <div className="text-2xl font-bold text-foreground mb-1">Four-eyes</div>
              <div className="text-sm text-muted-foreground">Separate review and publication authority</div>
            </div>
          </div>
        </section>

        {/* Core Audit Tools */}
        <section>
          <div className="mb-12">
            <div className="text-xs font-bold text-amber-400 tracking-widest mb-3">CAPABILITIES</div>
            <h2 className="font-serif text-4xl font-bold leading-tight text-foreground">
              Built-in audit workflow
            </h2>
          </div>
          <div className="grid gap-8 md:grid-cols-2">
            <div className="border-l-4 border-teal-600 pl-6 py-6">
              <div className="text-sm font-bold text-teal-600 tracking-widest mb-3">RECONCILIATION ENGINE</div>
              <p className="text-muted-foreground text-sm mb-4 leading-relaxed">
                Match FAAC allocations across multiple sources with automatic conflict detection, variance analysis, and detailed reconciliation reports showing source divergences and resolution status.
              </p>
              <ul className="space-y-2 text-sm">
                <li className="flex items-start gap-2">
                  <span className="text-emerald-600 font-bold">✓</span>
                  <span className="text-muted-foreground">Multi-source matching</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-emerald-600 font-bold">✓</span>
                  <span className="text-muted-foreground">Variance thresholds</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-emerald-600 font-bold">✓</span>
                  <span className="text-muted-foreground">Conflict flagging</span>
                </li>
              </ul>
            </div>
            <div className="border-l-4 border-blue-500 pl-6 py-6">
              <div className="text-sm font-bold text-blue-600 tracking-widest mb-3">EVIDENCE VERIFICATION</div>
              <p className="text-muted-foreground text-sm mb-4 leading-relaxed">
                Trace every published figure to its original source document with retained bytes, cryptographic hashes, extraction method, and validation results for complete audit trail and reproducibility.
              </p>
              <ul className="space-y-2 text-sm">
                <li className="flex items-start gap-2">
                  <span className="text-emerald-600 font-bold">✓</span>
                  <span className="text-muted-foreground">Source document archive</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-emerald-600 font-bold">✓</span>
                  <span className="text-muted-foreground">SHA-256 verification</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-emerald-600 font-bold">✓</span>
                  <span className="text-muted-foreground">Extraction audit logs</span>
                </li>
              </ul>
            </div>
            <div className="border-l-4 border-emerald-600 pl-6 py-6">
              <div className="text-sm font-bold text-emerald-700 tracking-widest mb-3">REVISION TRACKING</div>
              <p className="text-muted-foreground text-sm mb-4 leading-relaxed">
                Monitor allocation revisions, reversals, and corrections across periods with detailed revision history, change justifications, and impact analysis on dependent calculations and reports.
              </p>
              <ul className="space-y-2 text-sm">
                <li className="flex items-start gap-2">
                  <span className="text-emerald-600 font-bold">✓</span>
                  <span className="text-muted-foreground">Revision history</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-emerald-600 font-bold">✓</span>
                  <span className="text-muted-foreground">Change justifications</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-emerald-600 font-bold">✓</span>
                  <span className="text-muted-foreground">Impact analysis</span>
                </li>
              </ul>
            </div>
            <div className="border-l-4 border-amber-400 pl-6 py-6">
              <div className="text-sm font-bold text-amber-600 tracking-widest mb-3">REPORT GENERATION</div>
              <p className="text-muted-foreground text-sm mb-4 leading-relaxed">
                Export audit-ready reports with embedded evidence lineage, reconciliation findings, exception flags, and certification metadata for regulatory submission and institutional records.
              </p>
              <ul className="space-y-2 text-sm">
                <li className="flex items-start gap-2">
                  <span className="text-emerald-600 font-bold">✓</span>
                  <span className="text-muted-foreground">PDF & Excel formats</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-emerald-600 font-bold">✓</span>
                  <span className="text-muted-foreground">Embedded lineage</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-emerald-600 font-bold">✓</span>
                  <span className="text-muted-foreground">Certification data</span>
                </li>
              </ul>
            </div>
          </div>
        </section>

        {/* Publication Control */}
        <section className="border-t border-border pt-16">
          <div className="mb-12">
            <div className="text-xs font-bold text-amber-400 tracking-widest mb-3">GOVERNANCE</div>
            <h2 className="font-serif text-4xl font-bold leading-tight text-foreground">
              Four-eyes publication control
            </h2>
          </div>
          <div className="grid gap-6 md:grid-cols-3">
            <div className="border-l-4 border-teal-600 pl-6 py-4">
              <div className="text-xs font-bold text-teal-600 tracking-widest mb-2">REVIEW QUEUE</div>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Pending allocations await human review. Reviewer examines lineage, reconciliation findings, and source conflicts before marking ready for publication.
              </p>
            </div>
            <div className="border-l-4 border-teal-600 pl-6 py-4">
              <div className="text-xs font-bold text-teal-600 tracking-widest mb-2">APPROVAL AUTHORITY</div>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Separate approver (never the reviewer) grants final publication authority. Both reviewers and approvers are logged with timestamp and justification.
              </p>
            </div>
            <div className="border-l-4 border-teal-600 pl-6 py-4">
              <div className="text-xs font-bold text-teal-600 tracking-widest mb-2">AUDIT TRAIL</div>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Complete log of all review decisions, approvals, and rejections with rationale. Every published record carries publication metadata and approval lineage.
              </p>
            </div>
          </div>
        </section>

        {/* Use Cases */}
        <section className="border-t border-border pt-16">
          <div className="mb-12">
            <div className="text-xs font-bold text-amber-400 tracking-widest mb-3">APPLICATIONS</div>
            <h2 className="font-serif text-4xl font-bold leading-tight text-foreground">
              Common audit scenarios
            </h2>
          </div>
          <div className="grid gap-6 md:grid-cols-2">
            <div className="border-l-4 border-teal-600 pl-6 py-6">
              <div className="font-semibold text-foreground mb-2">FAAC Allocation Audit</div>
              <div className="text-sm text-muted-foreground">
                Verify federal allocations to states and LGAs against official OAGF disbursement records. Reconcile FAAC distribution amounts with state treasury receipts and detect shortfalls or misallocations.
              </div>
            </div>
            <div className="border-l-4 border-teal-600 pl-6 py-6">
              <div className="font-semibold text-foreground mb-2">Regulatory Compliance</div>
              <div className="text-sm text-muted-foreground">
                Generate audit reports for central bank, SEC, and other regulators requiring verified fiscal data lineage. Export certified records with evidence chains for submission and archival.
              </div>
            </div>
            <div className="border-l-4 border-teal-600 pl-6 py-6">
              <div className="font-semibold text-foreground mb-2">Period Reconciliation</div>
              <div className="text-sm text-muted-foreground">
                Compare allocations across monthly, quarterly, and annual periods. Identify pattern breaks, anomalies, and revisions requiring investigation or escalation.
              </div>
            </div>
            <div className="border-l-4 border-teal-600 pl-6 py-6">
              <div className="font-semibold text-foreground mb-2">Conflict Resolution</div>
              <div className="text-sm text-muted-foreground">
                Review source conflicts flagged by the reconciliation engine. Access conflicting values with source context, publication dates, and methodology to support dispute resolution.
              </div>
            </div>
          </div>
        </section>

        {/* CTA */}
        <section className="border-t border-b border-border py-12">
          <div className="text-center space-y-6">
            <h2 className="font-serif text-3xl font-bold text-foreground">Ready to audit?</h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              Request institutional access to unlock audit workflows, reconciliation reports, and evidence verification tools.
            </p>
            <div className="flex gap-4 justify-center flex-wrap">
              <Button asChild>
                <Link href="/pilot">Request Fiscal Watch Access</Link>
              </Button>
              <Button asChild variant="outline">
                <Link href="/contact">Contact Support</Link>
              </Button>
            </div>
          </div>
        </section>
      </div>
    </div>
  )
}
