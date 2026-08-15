import { ArrowDown, Building2, Code2, FileSpreadsheet } from 'lucide-react'
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

export const metadata: Metadata = { title: 'Pilot access' }

const pilots = [
  {
    name: 'Analyst Pilot',
    icon: FileSpreadsheet,
    audience: 'Journalists, researchers, analysts, and independent consultants',
    outcome:
      'Evaluate published historical GaiaFAAC evidence for an agreed set of months and jurisdictions, with source lineage preserved.',
  },
  {
    name: 'Team Pilot',
    icon: Building2,
    audience:
      'Newsrooms, consultancies, NGOs, universities, and research teams',
    outcome:
      'Evaluate reviewed historical evidence in an agreed internal research workflow with manual commercial support.',
  },
  {
    name: 'API Evaluation',
    icon: Code2,
    audience:
      'Data teams, fintechs, research platforms, and institutional users',
    outcome:
      'Evaluate entitled access to published month and allocation endpoints with a manually issued GaiaFAAC API key.',
  },
]

export default function PilotPage() {
  return (
    <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
      <PageHeader
        eyebrow="Commercial pilot"
        title="Evaluate GaiaFAAC with your real research workflow"
        description="Paid access is manually provisioned so we can verify that the requested published evidence and delivery method are actually available before payment. The latest verified month remains free to inspect."
      />

      <div className="mt-10 grid gap-5 lg:grid-cols-3">
        {pilots.map(({ name, icon: Icon, audience, outcome }) => (
          <Card key={name}>
            <CardHeader>
              <Icon className="text-primary size-5" aria-hidden="true" />
              <CardTitle className="pt-3">{name}</CardTitle>
              <CardDescription>{audience}</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground text-sm leading-6">
                {outcome}
              </p>
              <Button asChild className="mt-6 w-full">
                <a href="#request-form">
                  Request access
                  <ArrowDown className="size-4" aria-hidden="true" />
                </a>
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="mt-12 grid gap-8 lg:grid-cols-2">
        <section>
          <h2 className="text-2xl font-semibold tracking-tight">
            What happens next
          </h2>
          <ol className="text-muted-foreground mt-5 space-y-4 text-sm leading-6">
            <li>
              <span className="text-foreground font-medium">
                1. Coverage check.
              </span>{' '}
              We confirm which published months, jurisdictions, and retained
              source documents are actually available.
            </li>
            <li>
              <span className="text-foreground font-medium">
                2. Delivery check.
              </span>{' '}
              We confirm whether your requested format can be delivered during
              the pilot. No self-service export capability is implied.
            </li>
            <li>
              <span className="text-foreground font-medium">
                3. Written scope.
              </span>{' '}
              We agree the users, permitted use, evidence scope, support, price,
              and limitations before payment.
            </li>
            <li>
              <span className="text-foreground font-medium">
                4. Provisioning.
              </span>{' '}
              Approved evidence or API access is provisioned manually. API
              customers receive an entitled key for the implemented published
              data endpoints.
            </li>
          </ol>
        </section>

        <section className="border-border bg-muted/30 rounded-lg border p-6">
          <h2 className="text-xl font-semibold">Before requesting access</h2>
          <ul className="text-muted-foreground mt-4 space-y-3 text-sm leading-6">
            <li>Identify the states and reporting periods you need.</li>
            <li>
              Tell us your preferred delivery format. We will confirm support
              before including it in an offer.
            </li>
            <li>
              Explain whether the output is for internal research, publication,
              or integration.
            </li>
            <li>Provide the number of intended users.</li>
            <li>
              Do not send payment until coverage, permitted use, and delivery
              have been confirmed in writing.
            </li>
          </ul>
        </section>
      </div>

      <section
        id="request-form"
        className="border-border mt-14 scroll-mt-8 rounded-xl border p-6 sm:p-8"
      >
        <div className="max-w-3xl">
          <p className="text-primary font-mono text-xs font-semibold tracking-[0.18em] uppercase">
            Pilot request
          </p>
          <h2 className="mt-3 text-3xl font-semibold tracking-tight">
            Tell us what you need
          </h2>
          <p className="text-muted-foreground mt-3 text-sm leading-6">
            Your request is stored securely for commercial follow-up. A request
            is not a purchase and does not guarantee a feature or data period;
            we confirm the available scope first.
          </p>
        </div>
        <div className="mt-8 max-w-4xl">
          <PilotLeadForm />
        </div>
      </section>

      <p className="text-muted-foreground mt-10 text-sm leading-6">
        GaiaFAAC is an independent research platform, not a government service.
        Public-source facts remain attributable to their original publishers.
        Commercial access covers reviewed compilation, structured access,
        support, and controlled API use—not ownership of public records.
      </p>
    </div>
  )
}
