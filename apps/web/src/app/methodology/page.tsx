import {
  Calculator,
  CircleSlash2,
  FileSearch,
  ShieldCheck,
} from 'lucide-react'
import type { Metadata } from 'next'

import { DemoBanner } from '@/components/demo-banner'
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
      'Every displayed demo allocation carries its reporting period, source-document identifier, and verification status.',
  },
  {
    icon: Calculator,
    title: 'Exact monetary storage',
    description:
      'Amounts are parsed with Decimal and stored as fixed-precision NUMERIC values. Original text and reported units are retained.',
  },
  {
    icon: ShieldCheck,
    title: 'Approval is not publication',
    description:
      'Automated validation and human verification are distinct. Milestone 4 still serves only unpublished demo records.',
  },
  {
    icon: CircleSlash2,
    title: 'No inferred values',
    description:
      'A missing state allocation is shown as unavailable. It is never estimated, copied from another period, or replaced with zero.',
  },
]

export default function MethodologyPage() {
  return (
    <>
      <DemoBanner />
      <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
        <PageHeader
          eyebrow="Methodology"
          title="Evidence before interpretation"
          description="This interface demonstrates how GaiaFAAC will communicate scope, provenance, reconciliation, and unavailable data."
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
              What the demo totals mean
            </h2>
            <div className="text-muted-foreground mt-4 space-y-4 leading-7">
              <p>
                The overview sums three synthetic records for Lagos, Kano, and
                Rivers. The result is a demo-sample total, not a national FAAC
                distribution.
              </p>
              <p>
                The other 34 jurisdictions remain visible with unavailable
                values, making the coverage limitation explicit.
              </p>
            </div>
          </div>
          <div>
            <h2 className="text-2xl font-semibold tracking-tight">
              Verification language
            </h2>
            <div className="text-muted-foreground mt-4 space-y-4 leading-7">
              <p>
                The demo seed remains pending unless it is processed through the
                controlled validation workflow. The UI reports the stored status
                verbatim.
              </p>
              <p>
                Statistical warnings describe movements only. They do not imply
                corruption, misconduct, or governance performance.
              </p>
            </div>
          </div>
        </section>
      </div>
    </>
  )
}
