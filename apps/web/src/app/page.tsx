import {
  ArrowRight,
  DatabaseZap,
  FileCheck2,
  GitCompareArrows,
  History,
  ShieldCheck,
  Zap,
  TrendingUp,
  AlertTriangle,
  CheckCircle2,
  Lock,
  BarChart3,
  Eye,
  Shield,
} from 'lucide-react'
import type { Metadata } from 'next'
import Link from 'next/link'

import { ResearchCommandCenter } from '@/components/research-command-center'
import { StatusPill } from '@/components/status-pill'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { getPublishedAnalytics } from '@/lib/analytics-api'
import { formatDate, formatNaira } from '@/lib/format'
import { getNationalDistributionHistory } from '@/lib/national-distribution-api'
import { getPublishedOverview } from '@/lib/published-api'

export const metadata: Metadata = {
  title:
    'Gaia Fiscal Intelligence — Verified public-finance evidence for Nigeria',
  description:
    'Verified public-finance data, evidence and fiscal events for Nigeria, with source fingerprints, human review and versioned records.',
}
export const dynamic = 'force-dynamic'

function compactNaira(value: string | null) {
  if (!value) return 'Unavailable'
  const amount = Number(value)
  if (!Number.isFinite(amount)) return formatNaira(value)
  if (Math.abs(amount) >= 1_000_000_000_000)
    return `₦${(amount / 1_000_000_000_000).toFixed(2)}T`
  if (Math.abs(amount) >= 1_000_000_000)
    return `₦${(amount / 1_000_000_000).toFixed(2)}B`
  return formatNaira(value)
}

export default async function Home() {
  const [overviewResult, analyticsResult, nationalHistoryResult] =
    await Promise.all([
      getPublishedOverview(),
      getPublishedAnalytics(),
      getNationalDistributionHistory(12),
    ])
  const data = overviewResult.data
  const analytics = analyticsResult.data

  return (
    <>
      {/* Hero Section */}
      <section className="relative overflow-hidden">
        {/* Animated background gradient */}
        <div className="absolute inset-0 -z-10">
          <div className="absolute inset-0 bg-gradient-to-br from-blue-900 via-slate-900 to-slate-950" />
          <div className="absolute top-20 right-0 -z-10 h-96 w-96 rounded-full bg-blue-500/20 blur-3xl animate-pulse" />
          <div className="absolute bottom-0 left-20 -z-10 h-96 w-96 rounded-full bg-emerald-500/20 blur-3xl animate-pulse" />
        </div>

        <div className="relative mx-auto max-w-7xl px-5 py-24 lg:px-8 lg:py-32">
          <div className="grid gap-16 lg:grid-cols-[1.2fr_0.8fr] lg:items-center">
            {/* Left side - Hero content */}
            <div className="space-y-8 text-white">
              <div className="space-y-4">
                <div className="flex items-center gap-2">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-500/20 text-blue-300">
                    <ShieldCheck className="h-5 w-5" />
                  </div>
                  <span className="text-sm font-semibold text-blue-300">
                    VERIFIED FISCAL INTELLIGENCE
                  </span>
                </div>
                <h1 className="text-6xl font-bold tracking-tight lg:text-7xl leading-tight">
                  Nigeria's fiscal numbers,{' '}
                  <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-cyan-400">
                    with the evidence attached.
                  </span>
                </h1>
              </div>

              <p className="text-xl text-slate-300 max-w-2xl leading-relaxed">
                Verified public-finance data for Nigeria with complete provenance. Every figure
                traces to its source, reviewed by humans, versioned over time, and designed so
                serious analysts can audit the entire chain.
              </p>

              <div className="flex flex-wrap gap-3 pt-4">
                <Button asChild size="lg" className="bg-blue-600 hover:bg-blue-700 text-white">
                  <Link href="/terminal">
                    Explore the Data
                    <ArrowRight className="size-4 ml-2" />
                  </Link>
                </Button>
                <Button
                  asChild
                  size="lg"
                  className="border border-white/25 bg-white/10 text-white hover:bg-white/20"
                >
                  <Link href="/institutions">
                    <Shield className="size-4 mr-2" />
                    Institutional Intelligence
                  </Link>
                </Button>
                <Button
                  asChild
                  size="lg"
                  variant="outline"
                  className="border-white/25 text-white hover:bg-white/5"
                >
                  <Link href="/pricing">View Plans</Link>
                </Button>
              </div>
            </div>

            {/* Right side - Key metrics */}
            <div className="space-y-4">
              <Card className="border-slate-700/50 bg-slate-800/50 backdrop-blur-xl hover:bg-slate-800/70 transition-all">
                <CardHeader>
                  <p className="text-xs text-slate-400 font-semibold uppercase tracking-widest">
                    Latest Published
                  </p>
                  <p className="mt-2 text-4xl font-bold text-white">
                    {data ? compactNaira(data.total_net) : '—'}
                  </p>
                  <p className="text-sm text-slate-400 mt-2">
                    {data
                      ? `${data.covered_states}/${data.expected_states} jurisdictions • ${data.period.reporting_label}`
                      : 'Awaiting publication'}
                  </p>
                </CardHeader>
              </Card>

              <div className="grid grid-cols-2 gap-4">
                <Card className="border-slate-700/50 bg-slate-800/50 backdrop-blur-xl">
                  <CardHeader className="space-y-2">
                    <CheckCircle2 className="h-5 w-5 text-green-400" />
                    <p className="text-sm text-slate-400">Coverage</p>
                    <p className="text-2xl font-bold text-white">
                      {data ? `${data.covered_states}/37` : '—'}
                    </p>
                  </CardHeader>
                </Card>

                <Card className="border-slate-700/50 bg-slate-800/50 backdrop-blur-xl">
                  <CardHeader className="space-y-2">
                    <TrendingUp className="h-5 w-5 text-blue-400" />
                    <p className="text-sm text-slate-400">Periods</p>
                    <p className="text-2xl font-bold text-white">
                      {analytics?.months_published ?? '—'}
                    </p>
                  </CardHeader>
                </Card>
              </div>

              {data && (
                <Card className="border-slate-700/50 bg-slate-800/50 backdrop-blur-xl">
                  <CardHeader className="space-y-3">
                    <div className="flex items-center justify-between">
                      <p className="text-xs text-slate-400 font-semibold">
                        EVIDENCE FINGERPRINT
                      </p>
                      <StatusPill tone="success">Verified</StatusPill>
                    </div>
                    <p className="font-mono text-xs text-slate-300 break-all">
                      {data.source.sha256.substring(0, 32)}...
                    </p>
                  </CardHeader>
                </Card>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* Core Principles */}
      <section className="border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950">
        <div className="mx-auto max-w-7xl px-5 py-16 lg:px-8">
          <div className="mb-12">
            <h2 className="text-3xl font-bold text-slate-900 dark:text-white mb-3">
              Built on institutional principles
            </h2>
            <p className="text-slate-600 dark:text-slate-400 text-lg">
              Every feature designed for auditability, compliance, and trustworthy decision-making
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            {[
              {
                icon: FileCheck2,
                title: 'Source-backed',
                description:
                  'Published records retain source organization, document identity and SHA-256 fingerprint.',
              },
              {
                icon: Eye,
                title: 'Human-reviewed',
                description:
                  'Automated validation happens first. Publication requires explicit human verification.',
              },
              {
                icon: History,
                title: 'Version-aware',
                description:
                  'Revisions, superseded claims and history are modeled instead of silently overwritten.',
              },
            ].map(({ icon: Icon, title, description }) => (
              <Card key={title}>
                <CardHeader>
                  <Icon className="text-blue-600 dark:text-blue-400 size-6" aria-hidden="true" />
                  <CardTitle className="pt-3">{title}</CardTitle>
                  <CardDescription>{description}</CardDescription>
                </CardHeader>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Institutional Intelligence Section */}
      <section className="border-t border-slate-200 dark:border-slate-800 bg-gradient-to-b from-slate-50 to-white dark:from-slate-950 dark:to-slate-900">
        <div className="mx-auto max-w-7xl px-5 py-20 lg:px-8">
          <div className="mb-16">
            <div className="flex items-center gap-2 mb-4">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-purple-500/20 text-purple-500">
                <Zap className="h-5 w-5" />
              </div>
              <span className="text-sm font-semibold text-purple-600 dark:text-purple-400 uppercase">
                Institutional Decision Support
              </span>
            </div>
            <h2 className="text-4xl font-bold text-slate-900 dark:text-white mb-4">
              Institutional Intelligence Platform
            </h2>
            <p className="text-xl text-slate-600 dark:text-slate-400 max-w-3xl">
              AI-powered decision support for banks, investors, auditors, and policymakers. Real-time
              institutional readiness assessment with complete fiscal intelligence and anomaly detection.
            </p>
          </div>

          <div className="grid lg:grid-cols-3 gap-6 mb-12">
            <Card className="border-slate-700/50 dark:bg-slate-900/50 hover:shadow-lg transition-shadow">
              <CardHeader>
                <CheckCircle2 className="h-6 w-6 text-green-500 mb-2" />
                <CardTitle>Readiness Matrix</CardTitle>
                <CardDescription>
                  Real-time institutional readiness assessment for all 37 jurisdictions with integrity
                  scoring and publication status.
                </CardDescription>
                <Button asChild size="sm" className="mt-4 w-full">
                  <Link href="/institutions">View Dashboard</Link>
                </Button>
              </CardHeader>
            </Card>

            <Card className="border-slate-700/50 dark:bg-slate-900/50 hover:shadow-lg transition-shadow">
              <CardHeader>
                <AlertTriangle className="h-6 w-6 text-amber-500 mb-2" />
                <CardTitle>Anomaly Detection</CardTitle>
                <CardDescription>
                  AI identifies unusual trends (50%+ changes), peer deviations (z-score anomalies),
                  and source conflicts automatically.
                </CardDescription>
                <Button asChild size="sm" className="mt-4 w-full" variant="outline">
                  <Link href="/institutions">Learn More</Link>
                </Button>
              </CardHeader>
            </Card>

            <Card className="border-slate-700/50 dark:bg-slate-900/50 hover:shadow-lg transition-shadow">
              <CardHeader>
                <BarChart3 className="h-6 w-6 text-blue-500 mb-2" />
                <CardTitle>Decision Packets</CardTitle>
                <CardDescription>
                  Generate institutional decision support reports for loans, investments, audits,
                  and policy decisions.
                </CardDescription>
                <Button asChild size="sm" className="mt-4 w-full" variant="outline">
                  <Link href="/institutions">Explore</Link>
                </Button>
              </CardHeader>
            </Card>
          </div>

          <div className="bg-slate-800/30 dark:bg-slate-800/50 border border-slate-700/50 rounded-xl p-8">
            <h3 className="text-xl font-bold text-white mb-6">Institutional Use Cases</h3>
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
              {[
                { role: '🏦 Loan Committees', focus: 'Sustainability, FAAC dependence, peer comparison' },
                { role: '📈 Investors', focus: 'Growth trends, anomalies, fiscal positioning' },
                { role: '✓ Auditors', focus: 'Controls, changes, conflict resolution' },
                { role: '⚖️ Policymakers', focus: 'Benchmarking, support needs, trends' },
              ].map((usecase, idx) => (
                <div key={idx} className="space-y-2">
                  <p className="font-semibold text-white">{usecase.role}</p>
                  <p className="text-sm text-slate-300">{usecase.focus}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Research and Data Section */}
      {data ? (
        <ResearchCommandCenter
          overview={data}
          analytics={analytics}
          analyticsError={analyticsResult.error}
          nationalHistory={nationalHistoryResult.data ?? []}
          nationalHistoryError={nationalHistoryResult.error}
        />
      ) : (
        <section className="border-t border-slate-200 dark:border-slate-800">
          <div className="mx-auto max-w-7xl px-5 py-16 lg:px-8">
            <Card className="bg-slate-50 dark:bg-slate-900/50">
              <CardHeader>
                <StatusPill tone="neutral">Awaiting governed data</StatusPill>
                <CardTitle className="pt-3">Research workspace unavailable</CardTitle>
                <CardDescription>
                  Gaia Fiscal Intelligence does not synthesize replacement values when no governed
                  publication is available.
                </CardDescription>
              </CardHeader>
            </Card>
          </div>
        </section>
      )}

      {/* Features and Access Section */}
      <section className="border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-950">
        <div className="mx-auto max-w-7xl px-5 py-20 lg:px-8">
          <div className="grid lg:grid-cols-3 gap-8">
            <Card className="lg:col-span-2 hover:shadow-lg transition-shadow">
              <CardHeader>
                <DatabaseZap className="text-blue-600 dark:text-blue-400 size-6" aria-hidden="true" />
                <CardTitle className="pt-3 text-2xl">
                  Follow the evidence chain
                </CardTitle>
                <CardDescription className="text-base">
                  Start with a published figure, inspect its source fingerprint, compare jurisdictions,
                  track revisions over time, and export governed records for your research workflow.
                </CardDescription>
                <div className="flex flex-wrap gap-3 pt-6">
                  <Button asChild size="sm" className="gap-2">
                    <Link href="/terminal">
                      <DatabaseZap className="size-4" />
                      Open Terminal
                    </Link>
                  </Button>
                  <Button asChild size="sm" variant="outline" className="gap-2">
                    <Link href="/compare">
                      <GitCompareArrows className="size-4" />
                      Compare Jurisdictions
                    </Link>
                  </Button>
                  <Button asChild size="sm" variant="outline" className="gap-2">
                    <Link href="/sources">
                      <Lock className="size-4" />
                      Inspect Evidence
                    </Link>
                  </Button>
                </div>
              </CardHeader>
            </Card>

            <Card className="bg-gradient-to-br from-blue-50 to-purple-50 dark:from-blue-950/30 dark:to-purple-950/30 border-blue-200 dark:border-blue-900/50 hover:shadow-lg transition-shadow">
              <CardHeader>
                <CardTitle>Unlock Full Access</CardTitle>
                <CardDescription>
                  Commercial plans unlock historical data exports, team workflows, institutional
                  decision support, and REST API access.
                </CardDescription>
                <div className="pt-6 space-y-2">
                  <div className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
                    <CheckCircle2 className="size-4 text-green-600" />
                    Institutional Intelligence
                  </div>
                  <div className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
                    <CheckCircle2 className="size-4 text-green-600" />
                    Unlimited API calls
                  </div>
                  <div className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
                    <CheckCircle2 className="size-4 text-green-600" />
                    Decision Packets
                  </div>
                  <div className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
                    <CheckCircle2 className="size-4 text-green-600" />
                    Custom Integrations
                  </div>
                </div>
                <Button asChild size="sm" className="w-full mt-6 gap-2">
                  <Link href="/pricing">
                    View Pricing
                    <ArrowRight className="size-4" />
                  </Link>
                </Button>
              </CardHeader>
            </Card>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="border-t border-slate-200 dark:border-slate-800 bg-gradient-to-r from-blue-600 to-purple-600 dark:from-blue-900 dark:to-purple-900">
        <div className="mx-auto max-w-4xl px-5 py-20 lg:px-8 text-center">
          <h2 className="text-4xl font-bold text-white mb-4">
            Ready to make evidence-backed decisions?
          </h2>
          <p className="text-xl text-blue-100 mb-8">
            Explore Nigeria's verified fiscal intelligence platform powered by institutional
            oversight and AI-driven analysis.
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <Button asChild size="lg" className="bg-white text-blue-600 hover:bg-blue-50">
              <Link href="/terminal">
                Start Exploring
                <ArrowRight className="size-4 ml-2" />
              </Link>
            </Button>
            <Button
              asChild
              size="lg"
              className="border border-white/30 text-white hover:bg-white/10"
            >
              <Link href="/institutions">Institutional Dashboard</Link>
            </Button>
          </div>
        </div>
      </section>
    </>
  )
}
