import { Check, ShieldCheck, Sparkles } from 'lucide-react'
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
    'Self-service access to reviewed GaiaFAAC historical evidence, exports, team workflows and API delivery.',
}

const plans = [
  {
    name: 'Free',
    price: '$0',
    tagline: 'Verify the latest governed public evidence.',
    features: [
      'Latest verified FAAC month',
      'All 36 states and the FCT',
      'Public comparisons and Fiscal Pulse',
      'Source registry and SHA-256 fingerprints',
    ],
    cta: 'Explore live data',
    href: '/live',
    featured: false,
  },
  {
    name: 'Analyst',
    price: '$49',
    tagline:
      'For individual researchers who need governed historical evidence.',
    features: [
      'Published historical FAAC access',
      'Self-service CSV and XLSX exports',
      'Source-linked evidence and proof objects',
      'Single-user research workspace',
    ],
    cta: 'Start Analyst',
    href: '/account/signup?plan=analyst',
    featured: true,
  },
  {
    name: 'Team',
    price: '$199',
    tagline:
      'For research, policy and advisory teams working from one evidence base.',
    features: [
      'Everything in Analyst',
      'Up to 10 organization members',
      'Self-service invitations and team administration',
      'Shared governed evidence workflow',
    ],
    cta: 'Start Team',
    href: '/account/signup?plan=team',
    featured: false,
  },
  {
    name: 'API',
    price: '$299',
    tagline:
      'For products and analysts that need governed data programmatically.',
    features: [
      'Everything in Team',
      'Self-service API key creation and revocation',
      'Published months and allocation endpoints',
      '5,000 authenticated requests per rolling 24 hours',
    ],
    cta: 'Start API',
    href: '/account/signup?plan=api',
    featured: false,
  },
]

const paidValue = [
  'Human-reviewed publication workflow',
  'Document provenance and retained SHA-256 fingerprints',
  'Historical evidence structured for research use',
  'Deterministic fiscal proof and reconciliation controls',
  'Licensed exports or API delivery according to plan',
]

export default function PricingPage() {
  return (
    <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
      <PageHeader
        eyebrow="Pricing"
        title="Pay for governed evidence infrastructure, not public records"
        description="The latest verified public evidence stays open. Paid plans unlock historical access, governed exports, team workflows and programmatic delivery through the self-service account system."
      />

      <div className="border-primary/20 bg-primary/5 mt-8 rounded-lg border p-5">
        <div className="flex items-start gap-3">
          <Sparkles
            className="text-primary mt-0.5 size-5 shrink-0"
            aria-hidden="true"
          />
          <div>
            <p className="font-medium">Founding self-service pricing</p>
            <p className="text-muted-foreground mt-1 max-w-4xl text-sm leading-6">
              These monthly prices match GaiaFAAC&apos;s current billing and
              entitlement system. As the ledger expands into additional governed
              source families, new institutional and higher-volume API tiers can
              be introduced without changing what existing plans promise today.
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
                <StatusPill tone="success">Available now</StatusPill>
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
            <CardTitle className="pt-3">
              What customers are paying for
            </CardTitle>
            <CardDescription>
              Public-source facts remain attributable to their original
              publishers. GaiaFAAC charges for the governed evidence layer around
              those facts.
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
            <CardTitle>Institutional and redistribution use</CardTitle>
            <CardDescription>
              Large internal deployments, redistribution, white-label delivery,
              custom onboarding and substantially higher API volume should be
              separately licensed rather than bundled into the $299 plan.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground text-sm leading-6">
              Start with the Team or API plan to evaluate the product. For wider
              organizational or downstream commercial use, request an
              institutional scope so permitted use, support and pricing can be
              agreed explicitly.
            </p>
            <Button asChild variant="outline" className="mt-5">
              <Link href="/pilot?plan=team#request-form">
                Request institutional scope
              </Link>
            </Button>
          </CardContent>
        </Card>
      </div>

      <div className="text-muted-foreground mt-10 max-w-4xl space-y-2 text-sm leading-6">
        <p>
          Monthly prices are in USD. Checkout, billing management and plan
          entitlements are handled through the GaiaFAAC customer account.
        </p>
        <p>
          GaiaFAAC is an independent research platform, not a government
          service. Paid access does not transfer ownership of public records or
          imply endorsement by the original publisher.
        </p>
      </div>
    </div>
  )
}
