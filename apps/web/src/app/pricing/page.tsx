import { Check } from 'lucide-react'
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

export const metadata: Metadata = { title: 'Pricing' }

const CONTACT = 'mailto:ethagagroalliedltd@gmail.com?subject=GaiaFAAC%20plan'

const plans = [
  {
    name: 'Free',
    price: '$0',
    tagline: 'Official source access, always free.',
    features: [
      'Latest verified FAAC month',
      'All 37 jurisdictions, source-linked',
      'National overview, states & comparison',
      'Insights: trend, rankings, movers',
    ],
    cta: 'Start free',
    featured: false,
  },
  {
    name: 'Analyst',
    price: '$49',
    tagline: 'Full history for serious analysis.',
    features: [
      'Everything in Free',
      'Full published history',
      'CSV / XLSX / JSON downloads',
      'Saved state comparisons',
    ],
    cta: 'Choose Analyst',
    featured: true,
  },
  {
    name: 'Team',
    price: '$199',
    tagline: 'For newsrooms and research teams.',
    features: [
      'Everything in Analyst',
      'Email alerts on new months',
      'Monthly analyst report',
      'Up to 10 seats',
    ],
    cta: 'Choose Team',
    featured: false,
  },
  {
    name: 'API',
    price: '$299',
    tagline: 'Programmatic, source-verified data.',
    features: [
      'Everything in Team',
      'REST API access (API keys)',
      '5,000 requests / day',
      'Bulk historical endpoints',
    ],
    cta: 'Get API access',
    featured: false,
  },
]

export default function PricingPage() {
  return (
    <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
      <PageHeader
        eyebrow="Pricing"
        title="Source-verified FAAC data, priced to use"
        description="The latest verified month is always free. Paid plans unlock full history, downloads, alerts, reports, and API access. Basic official-source access is never behind a paywall."
      />

      <div className="mt-10 grid gap-5 md:grid-cols-2 xl:grid-cols-4">
        {plans.map((plan) => (
          <Card
            key={plan.name}
            className={plan.featured ? 'border-primary shadow-sm' : ''}
          >
            <CardHeader>
              <CardTitle className="flex items-baseline justify-between">
                <span>{plan.name}</span>
                <span className="text-2xl font-semibold">
                  {plan.price}
                  {plan.price !== '$0' ? (
                    <span className="text-muted-foreground text-sm font-normal">
                      /mo
                    </span>
                  ) : null}
                </span>
              </CardTitle>
              <CardDescription>{plan.tagline}</CardDescription>
            </CardHeader>
            <CardContent className="flex h-full flex-col">
              <ul className="space-y-2.5 text-sm">
                {plan.features.map((feature) => (
                  <li key={feature} className="flex items-start gap-2">
                    <Check
                      className="text-primary mt-0.5 size-4 shrink-0"
                      aria-hidden="true"
                    />
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>
              <Button
                asChild
                className="mt-6 w-full"
                variant={plan.featured ? 'default' : 'outline'}
              >
                <a href={CONTACT}>{plan.cta}</a>
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      <p className="text-muted-foreground mt-10 text-sm">
        Prices in USD. Custom cuts (specific states, longer history, on-prem)
        are available — just{' '}
        <a href={CONTACT} className="hover:text-foreground underline">
          get in touch
        </a>
        .
      </p>
    </div>
  )
}
