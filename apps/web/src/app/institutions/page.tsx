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
      <div className="relative min-h-screen overflow-hidden">
        {/* Gradient background */}
        <div className="absolute inset-0 -z-10">
          <div className="absolute inset-0 bg-gradient-to-br from-blue-900 via-slate-900 to-slate-950" />
          <div className="absolute top-0 right-0 -z-10 h-96 w-96 rounded-full bg-blue-500/20 blur-3xl" />
          <div className="absolute bottom-0 left-0 -z-10 h-96 w-96 rounded-full bg-purple-500/20 blur-3xl" />
        </div>

        <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8">
          {/* Top section with hero content */}
          <div className="grid grid-cols-1 gap-12 lg:grid-cols-2 lg:items-center py-20">
            <div className="space-y-8">
              <div>
                <div className="mb-4 flex items-center gap-2">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-500/20 text-blue-400">
                    <Shield className="h-6 w-6" />
                  </div>
                  <span className="text-sm font-medium text-blue-400">
                    INSTITUTIONAL INTELLIGENCE SYSTEM
                  </span>
                </div>
                <h1 className="text-5xl font-bold text-white lg:text-6xl">
                  Trustworthy decisions,
                  <span className="block text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400">
                    backed by evidence
                  </span>
                </h1>
              </div>

              <p className="text-xl text-slate-300 leading-relaxed max-w-lg">
                AI-powered institutional decision support platform for banks, investors, auditors, and policymakers. Every decision backed by audited fiscal evidence with complete provenance.
              </p>

              {/* Feature highlights */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4">
                <div className="flex gap-3 items-start p-4 rounded-lg bg-blue-500/10 border border-blue-500/20">
                  <CheckCircle2 className="h-5 w-5 text-blue-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="font-semibold text-white">Evidence Provenance</p>
                    <p className="text-sm text-slate-400">Every number traced to source with SHA-256</p>
                  </div>
                </div>
                <div className="flex gap-3 items-start p-4 rounded-lg bg-purple-500/10 border border-purple-500/20">
                  <Zap className="h-5 w-5 text-purple-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="font-semibold text-white">Anomaly Detection</p>
                    <p className="text-sm text-slate-400">AI identifies unusual trends & deviations</p>
                  </div>
                </div>
                <div className="flex gap-3 items-start p-4 rounded-lg bg-green-500/10 border border-green-500/20">
                  <TrendingUp className="h-5 w-5 text-green-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="font-semibold text-white">Peer Benchmarking</p>
                    <p className="text-sm text-slate-400">Compare metrics across jurisdictions</p>
                  </div>
                </div>
                <div className="flex gap-3 items-start p-4 rounded-lg bg-orange-500/10 border border-orange-500/20">
                  <AlertTriangle className="h-5 w-5 text-orange-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="font-semibold text-white">Risk Dashboard</p>
                    <p className="text-sm text-slate-400">Identify critical issues needing attention</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Stats section */}
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <Card className="border-slate-700/50 bg-slate-800/50 backdrop-blur">
                  <CardContent className="pt-6">
                    <div className="text-3xl font-bold text-green-400">37/37</div>
                    <p className="text-sm text-slate-400">Jurisdictions Covered</p>
                  </CardContent>
                </Card>
                <Card className="border-slate-700/50 bg-slate-800/50 backdrop-blur">
                  <CardContent className="pt-6">
                    <div className="text-3xl font-bold text-blue-400">30</div>
                    <p className="text-sm text-slate-400">Published Periods</p>
                  </CardContent>
                </Card>
              </div>

              <Card className="border-slate-700/50 bg-slate-800/50 backdrop-blur col-span-2">
                <CardContent className="pt-6">
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-slate-300">Ready for Publication</span>
                      <span className="text-2xl font-bold text-green-400">24</span>
                    </div>
                    <div className="w-full bg-slate-700/50 rounded-full h-2">
                      <div
                        className="bg-gradient-to-r from-green-500 to-emerald-500 h-2 rounded-full"
                        style={{ width: '65%' }}
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="border-slate-700/50 bg-slate-800/50 backdrop-blur col-span-2">
                <CardContent className="pt-6">
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-slate-300">Proceed with Caution</span>
                      <span className="text-2xl font-bold text-amber-400">10</span>
                    </div>
                    <div className="w-full bg-slate-700/50 rounded-full h-2">
                      <div
                        className="bg-gradient-to-r from-amber-500 to-orange-500 h-2 rounded-full"
                        style={{ width: '27%' }}
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="border-slate-700/50 bg-slate-800/50 backdrop-blur col-span-2">
                <CardContent className="pt-6">
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-slate-300">Requires Review</span>
                      <span className="text-2xl font-bold text-red-400">3</span>
                    </div>
                    <div className="w-full bg-slate-700/50 rounded-full h-2">
                      <div
                        className="bg-gradient-to-r from-red-500 to-rose-500 h-2 rounded-full"
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
      <div className="mx-auto max-w-7xl px-5 lg:px-8 pb-12">
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
      <div className="bg-gradient-to-b from-slate-950 to-blue-950/50 py-16">
        <div className="mx-auto max-w-7xl px-5 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-white mb-4">Built for Decision-Makers</h2>
            <p className="text-slate-400 text-lg max-w-2xl mx-auto">
              Institutional Intelligence serves different stakeholders with tailored decision support
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              {
                role: 'Loan Committees',
                focus: 'Sustainability Assessment',
                icon: '🏦',
                details: ['FAAC dependence', 'Revenue trends', 'Peer comparison'],
              },
              {
                role: 'Investors',
                focus: 'Growth & Risk',
                icon: '📈',
                details: ['Trend analysis', 'Anomaly detection', 'Fiscal positioning'],
              },
              {
                role: 'Auditors',
                focus: 'Controls & Changes',
                icon: '✓',
                details: ['Conflict resolution', 'Audit trails', 'Verification status'],
              },
              {
                role: 'Policymakers',
                focus: 'Fiscal Support',
                icon: '⚖️',
                details: ['Peer benchmarking', 'Policy impact', 'Recommendations'],
              },
            ].map((usecase, idx) => (
              <Card
                key={idx}
                className="border-slate-700/50 bg-slate-900/50 backdrop-blur hover:bg-slate-900/80 transition-colors"
              >
                <CardHeader>
                  <div className="text-4xl mb-3">{usecase.icon}</div>
                  <CardTitle className="text-lg text-white">{usecase.role}</CardTitle>
                  <CardDescription className="text-blue-400">
                    {usecase.focus}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    {usecase.details.map((detail, didx) => (
                      <li key={didx} className="flex items-center gap-2 text-sm text-slate-300">
                        <div className="w-1.5 h-1.5 rounded-full bg-blue-500" />
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
      <div className="mx-auto max-w-7xl px-5 lg:px-8 py-16">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          <div className="space-y-6">
            <div>
              <h2 className="text-3xl font-bold text-white mb-2">
                Enterprise-Grade Intelligence
              </h2>
              <p className="text-slate-400">
                Built on proven institutional frameworks for auditability, compliance, and decision integrity
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
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-500/20 text-blue-400">
                      <CheckCircle2 className="h-5 w-5" />
                    </div>
                  </div>
                  <div>
                    <h3 className="font-semibold text-white">{feature.title}</h3>
                    <p className="text-sm text-slate-400">{feature.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <Card className="border-slate-700/50 bg-slate-900/50 backdrop-blur">
            <CardHeader>
              <CardTitle>API-First Architecture</CardTitle>
              <CardDescription>
                Institutional Intelligence is accessible via REST API for system integration
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 font-mono text-sm">
              <div className="p-3 rounded bg-slate-950/50 text-slate-300">
                GET /api/v1/institutional/readiness-matrix
              </div>
              <div className="p-3 rounded bg-slate-950/50 text-slate-300">
                GET /api/v1/institutional/risk-indicators
              </div>
              <div className="p-3 rounded bg-slate-950/50 text-slate-300">
                POST /api/v1/decisions/decision-packet/&#123;jurisdiction&#125;
              </div>
              <div className="p-3 rounded bg-slate-950/50 text-slate-300">
                GET /api/v1/evidence/provenance/&#123;gaia_id&#125;
              </div>
              <p className="text-xs text-slate-500 pt-2">
                Full API documentation available for enterprise integration
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
