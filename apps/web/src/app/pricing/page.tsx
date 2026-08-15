import { Check, Clock3, ShieldCheck } from 'lucide-react'
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

export const metadata: Metadata = {
  title: 'Pricing',
  description:
    'Commercial access to reviewed GaiaFAAC historical evidence and controlled API delivery.',
}

const plans = [
  {
    name: 'Free',
    price: '$0',
    tagline: 'Verify the latest public evidence before you buy anything.',
    availableNow: true,
    features: [
      'Latest verified FAAC month',
      'All 36 states and the FCT',
      'State pages, comparisons, and public Fiscal Pulse',
      'Published source registry with SHA-256 fingerprints',
    ],
    cta: 'Explore live data',
    href: '/live',
    featured: false,
  },
  {
    name: 'Analyst Pilot',
    price: '$49',
    tagline: 'For an individual researcher who needs published history.',
    availableNow: true,
    features: [
      'Manually provisioned access to published historical periods',
      'Source-linked evidence for the agreed research scope',
      'State comparison and published intelligence support',
      'Manual onboarding and delivery during the pilot',
    ],
    cta: 'Request analyst pilot',
    href: '/pilot?plan=analyst#request-form',
    featured: true,
  },
  {
    name: 'Team Pilot',
    price: '$199',
    tagline: 'For an organization evaluating GaiaFAAC in a real workflow.',
    availableNow: true,
    features: [
      'Reviewed historical evidence for an agreed organizational scope',
      'Coverage and permitted use confirmed before payment',
      'Shared delivery for an internal research workflow',
      'Direct commercial support during the pilot',
    ],
    cta: 'Discuss a team pilot',
    href: '/pilot?plan=team#request-form',
    featured: false,
  },
  {
    name: 'API Pilot',
    price: '$299',
    tagline: 'Controlled programmatic access to published GaiaFAAC records.',
    availableNow: true,
    features: [
      'Manually issued GaiaFAAC API key',
      'Published month index through /api/v1/data/months',
      'Published allocations through /api/v1/data/allocations',
      '5,000 authenticated requests per rolling 24 hours',
    ],
    cta: 'Request API evaluation',
    href: '/pilot?plan=api#request-form',
    featured: false,
  },
]

const paidValue = [
  'Reviewed compilation of published fiscal evidence',
  'Document provenance and retained source fingerprints',
  'Historical structuring for an agreed research scope',
  'Controlled programmatic access where the API plan applies',
  'Commercial scoping, permitted-use agreement, and onboarding',
]

const notYetSelfService = [
  'Automated checkout or recurring card billing',
  'Customer login and subscription management',
  'Self-service licensed CSV or XLSX download portal',
  'Self-service team-member administration',
]

export default function PricingPage() {
  return (
    <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
      <PageHeader
        eyebrow="Pricing"
        title="Pay for verified access and workflow, not public records"
        description="GaiaFAAC keeps the latest verified public evidence open. Paid pilots cover reviewed historical delivery, commercial support, and controlled API access that are already operational today."
      />

      <div className="border-primary/20 bg-primary/5 mt-8 rounded-lg border p-5">
        <div className="flex items-start gap-3">
          <Clock3
            className="text-primary mt-0.5 size-5 shrink-0"
            aria-hidden="true"
          />
          <div>
            <p className="font-medium">Paid access is manually provisioned</p>
            <p className="text-muted-foreground mt-1 max-w-4xl text-sm leading-6">
              We confirm the required months, jurisdictions, permitted use, and
              delivery method before taking payment. The prices below are pilot
              starting points, not automatic subscriptions.
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
                  {plan.availableNow ? 'Available now' : 'Planned'}
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

      <div className="mt-12 grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <ShieldCheck className="text-primary size-5" aria-hidden="true" />
            <CardTitle className="pt-3">What the paid value actually is</CardTitle>
            <CardDescription>
              Public-source facts remain attributable to their original
              publishers. GaiaFAAC charges for the governed evidence workflow
              around those facts.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="space-y-3 text-sm">
              {paidValue.map((item) => (
                <li key={item} className="flex items-start gap-2">
                  <Check
                    className="text-primary mt-0.5 size-4 shrink-0"
                    aria-hidden="true"
                  />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>

        <Card className="bg-muted/30">
          <CardHeader>
            <CardTitle>Current product boundaries</CardTitle>
            <CardDescription>
              We do not represent unfinished self-service functionality as an
              available paid feature.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="text-muted-foreground space-y-3 text-sm">
              {notYetSelfService.map((item) => (
                <li key={item}>• {item}</li>
              ))}
            </ul>
            <p className="text-muted-foreground mt-5 text-sm leading-6">
              These workflows remain manual during the commercial pilot. API
              access is the exception: entitled keys, published historical
              endpoints, request recording, and rate limits are already
              implemented.
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="border-border mt-12 rounded-xl border p-6 sm:p-8">
        <div className="max-w-3xl">
          <p className="text-primary font-mono text-xs font-semibold tracking-[0.18em] uppercase">
            Institutional scope
          </p>
          <h2 className="mt-3 text-2xl font-semibold tracking-tight">
            Need a larger internal research or licensing arrangement?
          </h2>
          <p className="text-muted-foreground mt-3 text-sm leading-6">
            Start with the Team Pilot. We will confirm the evidence coverage,
            intended users, permitted use, delivery method, and price in writing
            before any payment is requested.
          </p>
          <Button asChild className="mt-5">
            <Link href="/pilot?plan=team#request-form">
              Request institutional scope
            </Link>
          </Button>
        </div>
      </div>

      <div className="text-muted-foreground mt-10 max-w-4xl space-y-2 text-sm leading-6">
        <p>
          Pilot prices are starting points in USD and may change with historical
          coverage, permitted use, delivery requirements, and support needs.
        </p>
        <p>
          GaiaFAAC is an independent research platform, not a government service.
          Paid access does not transfer ownership of public records.
        </p>
      </div>
    </div>
  )
}
