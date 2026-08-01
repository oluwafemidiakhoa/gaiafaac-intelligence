import { ArrowRight, Building2, Code2, FileSpreadsheet } from 'lucide-react'
import type { Metadata } from 'next'

import { PageHeader } from '@/components/page-header'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'

export const metadata: Metadata = { title: 'Pilot access' }

const CONTACT_EMAIL = 'partnerships@gailabai.com'

const pilots = [
  {
    name: 'Analyst Pilot',
    icon: FileSpreadsheet,
    audience: 'Journalists, researchers, analysts, and independent consultants',
    outcome:
      'Evaluate reviewed historical data, structured exports, and one customized state comparison.',
    subject: 'GaiaFAAC Analyst Pilot',
  },
  {
    name: 'Team Pilot',
    icon: Building2,
    audience: 'Newsrooms, consultancies, NGOs, universities, and research teams',
    outcome:
      'Test a shared monthly intelligence workflow with onboarding, reports, and priority support.',
    subject: 'GaiaFAAC Team Pilot',
  },
  {
    name: 'API Evaluation',
    icon: Code2,
    audience: 'Data teams, fintechs, research platforms, and institutional users',
    outcome:
      'Evaluate controlled access to published historical endpoints with an entitled API key.',
    subject: 'GaiaFAAC API Evaluation',
  },
]

function mailto(subject: string) {
  const body = [
    'Hello GaiaFAAC team,',
    '',
    `I am interested in the ${subject}.`,
    '',
    'Name:',
    'Organization:',
    'Role:',
    'Country:',
    'Primary use case:',
    'States or periods of interest:',
    'Preferred delivery format:',
    'Expected number of users:',
    '',
    'Please contact me about availability, coverage, and pricing.',
  ].join('\n')

  return `mailto:${CONTACT_EMAIL}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`
}

export default function PilotPage() {
  return (
    <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
      <PageHeader
        eyebrow="Commercial pilot"
        title="Evaluate GaiaFAAC with your real research workflow"
        description="Paid access is currently provisioned manually so we can confirm data coverage, delivery requirements, and appropriate licensing before payment. The latest verified month remains free to inspect."
      />

      <div className="mt-10 grid gap-5 lg:grid-cols-3">
        {pilots.map(({ name, icon: Icon, audience, outcome, subject }) => (
          <Card key={name}>
            <CardHeader>
              <Icon className="text-primary size-5" aria-hidden="true" />
              <CardTitle className="pt-3">{name}</CardTitle>
              <CardDescription>{audience}</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground text-sm leading-6">{outcome}</p>
              <Button asChild className="mt-6 w-full">
                <a href={mailto(subject)}>
                  Request access
                  <ArrowRight className="size-4" aria-hidden="true" />
                </a>
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="mt-12 grid gap-8 lg:grid-cols-2">
        <section>
          <h2 className="text-2xl font-semibold tracking-tight">What happens next</h2>
          <ol className="text-muted-foreground mt-5 space-y-4 text-sm leading-6">
            <li>
              <span className="text-foreground font-medium">1. Coverage check.</span>{' '}
              We confirm which months, jurisdictions, exports, and source documents are available.
            </li>
            <li>
              <span className="text-foreground font-medium">2. Pilot scope.</span>{' '}
              We agree on users, delivery format, support, permitted use, and the evaluation period.
            </li>
            <li>
              <span className="text-foreground font-medium">3. Written offer.</span>{' '}
              You receive the exact deliverables, limitations, price, and licensing terms before paying.
            </li>
            <li>
              <span className="text-foreground font-medium">4. Provisioning.</span>{' '}
              Approved data, reports, or API access are delivered and onboarding is scheduled.
            </li>
          </ol>
        </section>

        <section className="border-border bg-muted/30 rounded-lg border p-6">
          <h2 className="text-xl font-semibold">Before requesting access</h2>
          <ul className="text-muted-foreground mt-4 space-y-3 text-sm leading-6">
            <li>Identify the states and reporting periods you need.</li>
            <li>State whether you require CSV, XLSX, JSON, a written report, or API access.</li>
            <li>Explain whether the output is for internal research, publication, or integration.</li>
            <li>Provide the number of intended users.</li>
            <li>Do not send payment until coverage and delivery have been confirmed in writing.</li>
          </ul>
        </section>
      </div>

      <p className="text-muted-foreground mt-10 text-sm leading-6">
        GaiaFAAC is an independent research platform, not a government service. Public-source facts remain attributable to their original publishers. Commercial access covers reviewed compilation, structured delivery, analysis, support, and controlled access—not ownership of public records.
      </p>
    </div>
  )
}
