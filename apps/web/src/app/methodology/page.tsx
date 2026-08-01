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
        description="How GaiaFAAC communicates scope, provenance, and reconciliation — so every published figure can be checked against its official source."
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
          <h2 className="text-2xl font-semibold tracking-tight">
            How the pipeline works
          </h2>
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
              publishes only after all 37 jurisdictions validate and a reviewer
              approves it.
            </p>
          </div>
        </div>
        <div>
          <h2 className="text-2xl font-semibold tracking-tight">
            What totals mean, and their limits
          </h2>
          <div className="text-muted-foreground mt-4 space-y-4 leading-7">
            <p>
              Published totals are the exact sum of verified allocations. Where
              a jurisdiction’s figure is not published on a comparable basis —
              for example the FCT’s gross — it is left unavailable, and any
              national total that depends on it is shown as unavailable too.
            </p>
            <p>
              Statistical warnings describe movements only. They do not imply
              corruption, misconduct, or governance performance.
            </p>
          </div>
        </div>
      </section>
    </div>
  )
}
