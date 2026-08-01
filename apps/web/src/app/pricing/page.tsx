import { Check, Clock3 } from 'lucide-react'
import type { Metadata } from 'next'
import Link from 'next/link'

import { PageHeader } from '@/components/page-header'
import { StatusPill } from '@/components/status-pill'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'

export const metadata: Metadata = { title: 'Pricing' }

const plans = [
  {
    name: 'Free',
    price: '$0',
    tagline: 'Inspect the latest verified month.',
    availableNow: true,
    features: [
      'Latest verified FAAC month',
      'All 37 jurisdictions, source-linked',
      'National overview, states, and comparison',
      'Public insights and source registry',
    ],
    cta: 'Explore live data',
    href: '/live',
    featured: false,
  },
  {
    name: 'Analyst Pilot',
    price: '$49',
    tagline: 'Historical analysis for an individual researcher.',
    availableNow: false,
    features: [
      'Manually provisioned historical access',
      'CSV or XLSX delivery where available',
      'One customized state comparison',
      'Direct pilot feedback channel',
    ],
    cta: 'Request pilot access',
    href: '/pilot?plan=analyst',
    featured: true,
  },
  {
    name: 'Team Pilot',
    price: '$199',
    tagline: 'For a newsroom, consultancy, or research team.',
    availableNow: false,
    features: [
      'Everything in Analyst Pilot',
      'Monthly analyst brief during the pilot',
      'Up to 10 named users',
      'Priority support and onboarding',
    ],
    cta: 'Discuss a team pilot',
    href: '/pilot?plan=team',
    featured: false,
  },
  {
    name: 'API Pilot',
    price: '$299',
    tagline: 'Controlled programmatic access for evaluation.',
    availableNow: false,
    features: [
      'Entitled API key issued manually',
      'Published historical endpoints',
      'Usage recording and daily limits',
      'Technical onboarding session',
    ],
    cta: 'Request API evaluation',
    href: '/pilot?plan=api',
    featured: false,
  },
]

export default function PricingPage() {
  return (
    <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
      <PageHeader
        eyebrow="Pricing"
        title="Start free. Join a paid pilot when you need more."
        description="The latest verified month and its original sources remain publicly accessible. Historical delivery, reports, team access, and API keys are currently provisioned through a limited pilot while automated checkout and customer accounts are being completed."
      />

      <div className="border-primary/20 bg-primary/5 mt-8 rounded-lg border p-5">
        <div className="flex items-start gap-3">
          <Clock3
            className="text-primary mt-0.5 size-5 shrink-0"
            aria-hidden="true"
          />
          <div>
            <p className="font-medium">Paid access is currently pilot-based</p>
            <p className="text-muted-foreground mt-1 text-sm leading-6">
              We confirm data coverage and delivery requirements before accepting
              payment. No automated subscription is created from this page.
            </p>
          </div>
        </div>
      </div>

      <div className="mt-10 grid gap-5 md:grid-cols-2 xl:grid-cols-4">
        {plans.map((plan) => (
          <Card
            key={plan.name}
            className={plan.featured ? 'border-primary shadow-sm' : ''}
          >
            <CardHeader>
              <div className="mb-3">
                <StatusPill tone={plan.availableNow ? 'success' : 'neutral'}>
                  {plan.availableNow ? 'Available now' : 'Limited pilot'}
                </StatusPill>
              </div>
              <CardTitle className="flex items-baseline justify-between gap-3">
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
                <Link href={plan.href}>{plan.cta}</Link>
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="text-muted-foreground mt-10 max-w-3xl space-y-2 text-sm leading-6">
        <p>
          Prices are pilot starting points in USD and may vary with historical
          coverage, export format, onboarding, and custom research requirements.
        </p>
        <p>
          Public-source facts remain attributable to their original publishers.
          Paid value comes from reviewed compilation, structured delivery,
          analysis, support, and controlled API access.
        </p>
      </div>
    </div>
  )
}
