import { Calculator, CircleSlash2, FileSearch, ShieldCheck } from 'lucide-react'
import type { Metadata } from 'next'

import { PageHeader } from '@/components/page-header'
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'

export const metadata: Metadata = { title: 'Methodology' }

const principles = [
  {
    icon: FileSearch,
    title: 'Source lineage first',
    description:
      'Every published allocation carries its reporting period, the SHA-256 of the exact OAGF document it came from, and its verification status.',
  },
  {
    icon: Calculator,
    title: 'Exact monetary storage',
    description:
      'Amounts are parsed with Decimal and stored as fixed-precision NUMERIC — never floating point. Original text and reported units are retained.',
  },
  {
    icon: ShieldCheck,
    title: 'Approval is not publication',
    description:
      'Automated validation and explicit human approval are distinct steps. Nothing reaches the public site without a reviewer approving it.',
  },
  {
    icon: CircleSlash2,
    title: 'No inferred values',
    description:
      'A value we cannot verify is shown as unavailable. It is never estimated, copied from another period, or replaced with zero.',
  },
]

export default function MethodologyPage() {
  return (
    <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
      <PageHeader
        eyebrow="Methodology"
        title="Evidence before interpretation"
        description="How GaiaFAAC communicates scope, provenance, reconciliation and derived fiscal signals—so every published figure can be checked against its official source."
      />

      <div className="mt-10 grid gap-5 md:grid-cols-2">
        {principles.map(({ icon: Icon, title, description }) => (
          <Card key={title}>
            <CardHeader>
              <Icon className="text-primary size-5" aria-hidden="true" />
              <CardTitle className="pt-3">{title}</CardTitle>
              <CardDescription>{description}</CardDescription>
            </CardHeader>
          </Card>
        ))}
      </div>

      <section className="border-border mt-12 grid gap-8 border-t pt-10 lg:grid-cols-2">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight">How the pipeline works</h2>
          <div className="text-muted-foreground mt-4 space-y-4 leading-7">
            <p>
              The official OAGF monthly disbursement report is downloaded and
              hashed. State allocations are read from Table III; the FCT total
              is reconciled from Table I. Every figure keeps its link to the
              source document.
            </p>
            <p>
              Each state must satisfy gross − deductions = net, and a total that
              cannot be reconciled is refused rather than guessed. A month
              publishes only after all required records validate and a reviewer
              approves it.
            </p>
          </div>
        </div>
        <div>
          <h2 className="text-2xl font-semibold tracking-tight">What totals mean, and their limits</h2>
          <div className="text-muted-foreground mt-4 space-y-4 leading-7">
            <p>
              Published totals are the exact sum of verified allocations. Where
              a jurisdiction’s figure is not published on a comparable basis —
              for example the FCT’s gross — it is left unavailable, and any
              derived metric that requires it is also unavailable.
            </p>
            <p>
              Statistical warnings describe movements only. They do not imply
              corruption, misconduct, governance performance or credit quality.
            </p>
          </div>
        </div>
      </section>

      <section className="border-border mt-12 border-t pt-10">
        <h2 className="text-2xl font-semibold tracking-tight">Fiscal Pulse indicators</h2>
        <div className="mt-6 grid gap-5 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Deduction burden & net retention</CardTitle>
              <CardDescription>
                Deduction burden = annual deductions ÷ annual gross allocation.
                Net retention = annual net allocation ÷ annual gross allocation.
                Both are withheld when a complete comparable gross/deduction
                series is unavailable.
              </CardDescription>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Allocation momentum</CardTitle>
              <CardDescription>
                The latest three available monthly net allocations are averaged
                and compared with the preceding three. Above +5% is Improving,
                below −5% is Weakening, and the range between is Stable. Fewer
                than six valid months produces Insufficient data.
              </CardDescription>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Allocation volatility</CardTitle>
              <CardDescription>
                Population coefficient of variation is calculated over valid
                monthly net allocations. Low is below 10%, Moderate is 10% to
                under 25%, and High is 25% or above. Fewer than three valid
                months produces Insufficient data.
              </CardDescription>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Evidence status</CardTitle>
              <CardDescription>
                Verified means every published month has net, gross and
                deduction values for the jurisdiction. Partial means the net
                series is complete but one or more comparable financial inputs
                are unavailable. Review required means the published-year series
                itself is incomplete.
              </CardDescription>
            </CardHeader>
          </Card>
        </div>
        <div className="text-muted-foreground mt-6 max-w-4xl space-y-3 text-sm leading-6">
          <p>
            Fiscal Pulse is not a credit rating, solvency test or prediction of
            default. FAAC is only one component of a state’s fiscal capacity.
          </p>
          <p>
            Broader fiscal-risk assessment would require additional evidence such
            as internally generated revenue, debt service, debt stock,
            expenditure, liabilities and other economic variables.
          </p>
        </div>
      </section>
    </div>
  )
}
