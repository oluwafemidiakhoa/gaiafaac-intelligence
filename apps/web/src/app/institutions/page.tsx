import type { Metadata } from 'next'
import {
  Shield,
  TrendingUp,
  AlertTriangle,
  CheckCircle2,
  Zap,
} from 'lucide-react'

import { PageHeader } from '@/components/page-header'
import { InstitutionalIntelligenceDashboard } from '@/components/institutional-intelligence-dashboard'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'

export const metadata: Metadata = {
  title: 'Institutional Intelligence',
  description:
    'Comprehensive institutional decision support, data integrity audits, and fiscal intelligence for Nigerian jurisdictions.',
}
export const dynamic = 'force-dynamic'

export default function InstitutionsPage() {
  return (
    <div className="space-y-12">
      {/* Hero Section */}
      <div className="relative min-h-screen overflow-hidden bg-stone-50">
        {/* Teal gradient background */}
        <div className="absolute inset-0 -z-10">
          <div className="absolute inset-0 bg-gradient-to-br from-teal-900 via-teal-800 to-teal-950" />
          <div className="absolute top-0 right-0 -z-10 h-96 w-96 rounded-full bg-amber-500/10 blur-3xl" />
          <div className="absolute bottom-0 left-0 -z-10 h-96 w-96 rounded-full bg-teal-500/10 blur-3xl" />
        </div>

        <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8">
          {/* Top section with hero content */}
          <div className="grid grid-cols-1 gap-12 py-20 lg:grid-cols-2 lg:items-center">
            <div className="space-y-8">
              <div>
                <div className="mb-4 flex items-center gap-2">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-amber-500/20 text-amber-300">
                    <Shield className="h-6 w-6" />
                  </div>
                  <span className="text-sm font-medium text-amber-300">
                    INSTITUTIONAL INTELLIGENCE SYSTEM
                  </span>
                </div>
                <h1
                  className="text-5xl font-bold text-white lg:text-6xl"
                  style={{ fontFamily: 'Georgia, serif' }}
                >
                  Trustworthy decisions,
                  <span className="block bg-gradient-to-r from-amber-300 to-amber-200 bg-clip-text text-transparent">
                    backed by evidence
                  </span>
                </h1>
              </div>

              <p className="max-w-lg text-xl leading-relaxed text-slate-300">
                AI-powered institutional decision support platform for banks,
                investors, auditors, and policymakers. Every decision backed by
                audited fiscal evidence with complete provenance.
              </p>

              {/* Feature highlights */}
              <div className="grid grid-cols-1 gap-4 pt-4 md:grid-cols-2">
                <div className="flex items-start gap-3 rounded-lg border border-amber-500/20 bg-amber-500/10 p-4">
                  <CheckCircle2 className="mt-0.5 h-5 w-5 flex-shrink-0 text-amber-300" />
                  <div>
                    <p className="font-semibold text-white">
                      Evidence Provenance
                    </p>
                    <p className="text-sm text-slate-300">
                      Every number traced to source with SHA-256
                    </p>
                  </div>
                </div>
                <div className="flex items-start gap-3 rounded-lg border border-amber-500/20 bg-amber-500/10 p-4">
                  <Zap className="mt-0.5 h-5 w-5 flex-shrink-0 text-amber-300" />
                  <div>
                    <p className="font-semibold text-white">
                      Anomaly Detection
                    </p>
                    <p className="text-sm text-slate-300">
                      AI identifies unusual trends & deviations
                    </p>
                  </div>
                </div>
                <div className="flex items-start gap-3 rounded-lg border border-teal-500/20 bg-teal-500/10 p-4">
                  <TrendingUp className="mt-0.5 h-5 w-5 flex-shrink-0 text-teal-300" />
                  <div>
                    <p className="font-semibold text-white">
                      Peer Benchmarking
                    </p>
                    <p className="text-sm text-slate-300">
                      Compare metrics across jurisdictions
                    </p>
                  </div>
                </div>
                <div className="flex items-start gap-3 rounded-lg border border-teal-500/20 bg-teal-500/10 p-4">
                  <AlertTriangle className="mt-0.5 h-5 w-5 flex-shrink-0 text-teal-300" />
                  <div>
                    <p className="font-semibold text-white">Risk Dashboard</p>
                    <p className="text-sm text-slate-300">
                      Identify critical issues needing attention
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Stats section */}
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <Card className="border-teal-200 bg-teal-50">
                  <CardContent className="pt-6">
                    <div className="text-3xl font-bold text-teal-900">
                      37/37
                    </div>
                    <p className="text-sm text-teal-700">
                      Jurisdictions Covered
                    </p>
                  </CardContent>
                </Card>
                <Card className="border-amber-200 bg-amber-50">
                  <CardContent className="pt-6">
                    <div className="text-3xl font-bold text-amber-900">30</div>
                    <p className="text-sm text-amber-700">Published Periods</p>
                  </CardContent>
                </Card>
              </div>

              <Card className="col-span-2 border-teal-200 bg-teal-50">
                <CardContent className="pt-6">
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-teal-800">
                        Ready for Publication
                      </span>
                      <span className="text-2xl font-bold text-teal-900">
                        24
                      </span>
                    </div>
                    <div className="h-2 w-full rounded-full bg-teal-200">
                      <div
                        className="h-2 rounded-full bg-gradient-to-r from-teal-600 to-teal-500"
                        style={{ width: '65%' }}
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="col-span-2 border-amber-200 bg-amber-50">
                <CardContent className="pt-6">
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-amber-800">
                        Proceed with Caution
                      </span>
                      <span className="text-2xl font-bold text-amber-900">
                        10
                      </span>
                    </div>
                    <div className="h-2 w-full rounded-full bg-amber-200">
                      <div
                        className="h-2 rounded-full bg-gradient-to-r from-amber-600 to-amber-500"
                        style={{ width: '27%' }}
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="col-span-2 border-red-200 bg-red-50">
                <CardContent className="pt-6">
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-red-800">Requires Review</span>
                      <span className="text-2xl font-bold text-red-900">3</span>
                    </div>
                    <div className="h-2 w-full rounded-full bg-red-200">
                      <div
                        className="h-2 rounded-full bg-gradient-to-r from-red-600 to-red-500"
                        style={{ width: '8%' }}
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </div>

      {/* Dashboard Section */}
      <div className="mx-auto max-w-7xl px-5 pb-12 lg:px-8">
        <PageHeader
          eyebrow="Institutional Decision Support"
          title="Jurisdiction Readiness Matrix"
          description="Real-time assessment of institutional readiness for publication and decision-making across all Nigerian jurisdictions."
        />

        <div className="mt-12">
          <InstitutionalIntelligenceDashboard />
        </div>
      </div>

      {/* Use Cases Section */}
      <div className="bg-gradient-to-b from-teal-900 to-teal-800 py-16">
        <div className="mx-auto max-w-7xl px-5 lg:px-8">
          <div className="mb-12 text-center">
            <h2
              className="mb-4 text-3xl font-bold text-white"
              style={{ fontFamily: 'Georgia, serif' }}
            >
              Built for Decision-Makers
            </h2>
            <p className="mx-auto max-w-2xl text-lg text-teal-100">
              Institutional Intelligence serves different stakeholders with
              tailored decision support
            </p>
          </div>

          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
            {[
              {
                role: 'Loan Committees',
                focus: 'Sustainability Assessment',
                icon: '🏦',
                details: [
                  'FAAC dependence',
                  'Revenue trends',
                  'Peer comparison',
                ],
              },
              {
                role: 'Investors',
                focus: 'Growth & Risk',
                icon: '📈',
                details: [
                  'Trend analysis',
                  'Anomaly detection',
                  'Fiscal positioning',
                ],
              },
              {
                role: 'Auditors',
                focus: 'Controls & Changes',
                icon: '✓',
                details: [
                  'Conflict resolution',
                  'Audit trails',
                  'Verification status',
                ],
              },
              {
                role: 'Policymakers',
                focus: 'Fiscal Support',
                icon: '⚖️',
                details: [
                  'Peer benchmarking',
                  'Policy impact',
                  'Recommendations',
                ],
              },
            ].map((usecase, idx) => (
              <Card
                key={idx}
                className="border-teal-600/30 bg-teal-50/50 backdrop-blur transition-colors hover:bg-teal-50"
              >
                <CardHeader>
                  <div className="mb-3 text-4xl">{usecase.icon}</div>
                  <CardTitle className="text-lg text-teal-900">
                    {usecase.role}
                  </CardTitle>
                  <CardDescription className="text-amber-700">
                    {usecase.focus}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    {usecase.details.map((detail, didx) => (
                      <li
                        key={didx}
                        className="flex items-center gap-2 text-sm text-teal-700"
                      >
                        <div className="h-1.5 w-1.5 rounded-full bg-amber-600" />
                        {detail}
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </div>

      {/* Technology Section */}
      <div className="mx-auto max-w-7xl px-5 py-16 lg:px-8">
        <div className="grid grid-cols-1 items-center gap-12 lg:grid-cols-2">
          <div className="space-y-6">
            <div>
              <h2
                className="mb-2 text-3xl font-bold text-teal-900"
                style={{ fontFamily: 'Georgia, serif' }}
              >
                Enterprise-Grade Intelligence
              </h2>
              <p className="text-teal-700">
                Built on proven institutional frameworks for auditability,
                compliance, and decision integrity
              </p>
            </div>

            <div className="space-y-4">
              {[
                {
                  title: 'SHA-256 Proof Chains',
                  desc: 'Every figure immutably linked to source document with cryptographic proof',
                },
                {
                  title: 'Four-Eyes Control',
                  desc: 'Separate review and approval roles for institutional compliance',
                },
                {
                  title: 'AI Anomaly Detection',
                  desc: 'Automatic identification of unusual trends, peer deviations, and conflicts',
                },
                {
                  title: 'Revision History',
                  desc: 'Complete version tracking with reason codes and approvers',
                },
              ].map((feature, idx) => (
                <div key={idx} className="flex gap-4">
                  <div className="flex-shrink-0">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-amber-200/50 text-amber-700">
                      <CheckCircle2 className="h-5 w-5" />
                    </div>
                  </div>
                  <div>
                    <h3 className="font-semibold text-teal-900">
                      {feature.title}
                    </h3>
                    <p className="text-sm text-teal-700">{feature.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <Card className="border-teal-200 bg-teal-50">
            <CardHeader>
              <CardTitle className="text-teal-900">
                API-First Architecture
              </CardTitle>
              <CardDescription className="text-teal-700">
                Institutional Intelligence is accessible via REST API for system
                integration
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 font-mono text-sm">
              <div className="rounded bg-teal-100 p-3 text-teal-900">
                GET /api/v1/institutional/readiness-matrix
              </div>
              <div className="rounded bg-teal-100 p-3 text-teal-900">
                GET /api/v1/institutional/risk-indicators
              </div>
              <div className="rounded bg-teal-100 p-3 text-teal-900">
                POST /api/v1/decisions/decision-packet/&#123;jurisdiction&#125;
              </div>
              <div className="rounded bg-teal-100 p-3 text-teal-900">
                GET /api/v1/evidence/provenance/&#123;gaia_id&#125;
              </div>
              <p className="pt-2 text-xs text-teal-600">
                Full API documentation available for enterprise integration
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
