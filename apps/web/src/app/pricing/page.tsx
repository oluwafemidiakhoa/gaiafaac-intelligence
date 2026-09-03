import {
  Building2,
  Check,
  DatabaseZap,
  ShieldCheck,
  Sparkles,
} from 'lucide-react'
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
    'Self-service and institutional access to reviewed GaiaFAAC fiscal evidence, exports, team workflows and programmatic delivery.',
}

const plans = [
  {
    name: 'Free',
    price: '₦0',
    period: 'Forever free',
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
    name: 'Professional',
    price: '₦50,000',
    period: '/month',
    tagline:
      'For individual researchers and analysts who need historical evidence.',
    features: [
      'Published historical FAAC access',
      'Self-service CSV and XLSX exports',
      'Source-linked evidence and proof objects',
      'Single-user research workspace',
      '100,000 API requests/month',
    ],
    cta: 'Start Free Trial',
    href: '/account/signup?plan=professional',
    featured: true,
  },
  {
    name: 'Enterprise',
    price: '₦500,000',
    period: '/month',
    tagline:
      'For institutions, governments and APIs needing programmatic access.',
    features: [
      'Everything in Professional',
      'Unlimited organization members',
      'Custom team administration',
      'Shared governed evidence workflow',
      'Unlimited API requests',
      'Decision Packets (unlimited)',
      'Webhook integrations',
      'Priority support',
    ],
    cta: 'Contact Sales',
    href: '/account/signup?plan=enterprise',
    featured: false,
  },
]

const institutionalProducts = [
  {
    icon: ShieldCheck,
    name: 'Institutional Intelligence',
    buyer: 'Banks, asset managers, advisers and research teams',
    description:
      'Organization-wide fiscal monitoring, governed exports, decision packets, evidence support and custom onboarding under an annual agreement.',
    capabilities: [
      'Institution-wide licensed use',
      'Priority evidence and research support',
      'Custom jurisdiction and reporting workflows',
      'Team onboarding and governance controls',
    ],
  },
  {
    icon: DatabaseZap,
    name: 'Data & Evidence Feed',
    buyer: 'Fintechs, data companies, media and internal data platforms',
    description:
      'Higher-volume programmatic delivery for products that need governed fiscal records, provenance and change-aware data infrastructure.',
    capabilities: [
      'Higher-volume API agreements',
      'Redistribution and downstream-use licensing',
      'Custom delivery and integration scope',
      'Revision and event-feed roadmap access',
    ],
  },
  {
    icon: Building2,
    name: 'Government Evidence Workspace',
    buyer: 'Public institutions and development organizations',
    description:
      'Dedicated evidence rooms and comparative fiscal workflows for teams that need traceable source material, governed analysis and durable decision records.',
    capabilities: [
      'Dedicated evidence workspace',
      'Comparative jurisdiction intelligence',
      'Governed decision material',
      'Custom implementation and support',
    ],
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
        eyebrow="Access"
        title="Start self-service. Scale into fiscal intelligence infrastructure."
        description="The latest verified public evidence stays open. Paid access funds the governed evidence layer: historical research, reproducible exports, team workflows, programmatic delivery and institutional deployments."
      />

      <div className="mt-8 rounded-lg border border-teal-900/20 bg-teal-900/5 p-5">
        <div className="flex items-start gap-3">
          <Sparkles
            className="mt-0.5 size-5 shrink-0 text-teal-900"
            aria-hidden="true"
          />
          <div>
            <p className="font-medium">Two commercial motions</p>
            <p className="text-muted-foreground mt-1 max-w-4xl text-sm leading-6">
              Self-service plans match GaiaFAAC&apos;s current billing and
              entitlement system. Institution-wide use, redistribution,
              higher-volume data delivery and dedicated evidence workspaces are
              contracted separately so scope, support and permitted use are
              explicit.
            </p>
          </div>
        </div>
      </div>

      <div className="mt-10 flex items-end justify-between gap-4">
        <div>
          <p className="text-primary font-mono text-xs font-semibold tracking-[0.16em] uppercase">
            Self-service
          </p>
          <h2 className="mt-2 text-2xl font-semibold">Start immediately</h2>
        </div>
        <p className="text-muted-foreground hidden max-w-xl text-right text-sm md:block">
          Built for individual analysts, small teams and product evaluation.
        </p>
      </div>

      <div className="mt-5 grid gap-5 md:grid-cols-2 xl:grid-cols-4">
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
                <div className="text-right">
                  <span className="text-2xl font-semibold">{plan.price}</span>
                  {plan.period && (
                    <span className="text-muted-foreground text-sm font-normal">
                      {plan.period}
                    </span>
                  )}
                </div>
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

      <section className="mt-16 rounded-2xl border border-teal-900/10 bg-[radial-gradient(circle_at_top_left,rgba(20,92,102,0.10),transparent_34%)] p-6 sm:p-8">
        <div className="max-w-3xl">
          <p className="font-mono text-xs font-semibold tracking-[0.16em] text-teal-900 uppercase">
            Institutional
          </p>
          <h2
            className="mt-3 text-3xl font-semibold tracking-tight text-teal-900 sm:text-4xl"
            style={{ fontFamily: 'Georgia, serif' }}
          >
            Buy the evidence layer as infrastructure.
          </h2>
          <p className="text-muted-foreground mt-4 text-sm leading-7 sm:text-base">
            Annual institutional agreements are for organizations that need more
            than seats: governed fiscal monitoring, broader licensed use,
            redistribution rights, higher-volume delivery, evidence rooms or
            implementation support.
          </p>
        </div>

        <div className="mt-8 grid gap-5 lg:grid-cols-3">
          {institutionalProducts.map(
            ({ icon: Icon, name, buyer, description, capabilities }) => (
              <Card key={name} className="bg-background/80">
                <CardHeader>
                  <Icon className="size-5 text-teal-900" aria-hidden="true" />
                  <CardTitle className="pt-3">{name}</CardTitle>
                  <CardDescription>{buyer}</CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground text-sm leading-6">
                    {description}
                  </p>
                  <ul className="mt-5 space-y-2.5 text-sm">
                    {capabilities.map((capability) => (
                      <li key={capability} className="flex items-start gap-2">
                        <Check
                          className="text-primary mt-0.5 size-4 shrink-0"
                          aria-hidden="true"
                        />
                        <span>{capability}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            ),
          )}
        </div>

        <div className="mt-6 flex flex-wrap items-center justify-between gap-5 rounded-xl border border-teal-200 bg-teal-50 p-5">
          <div>
            <p className="font-semibold text-teal-900">
              Institutional scope is contract-priced
            </p>
            <p className="mt-1 max-w-3xl text-sm leading-6 text-teal-700">
              GaiaFAAC does not publish fictional enterprise prices before the
              required data coverage, permitted use, delivery volume and support
              scope are understood.
            </p>
          </div>
          <Button
            asChild
            size="lg"
            className="bg-teal-900 text-white hover:bg-teal-800"
          >
            <Link href="/pilot?plan=team#request-form">
              Request institutional review
            </Link>
          </Button>
        </div>
      </section>

      <div className="mt-12 grid gap-6 lg:grid-cols-2">
        <Card className="border-teal-200">
          <CardHeader>
            <ShieldCheck className="size-5 text-teal-900" aria-hidden="true" />
            <CardTitle className="pt-3 text-teal-900">
              What customers are paying for
            </CardTitle>
            <CardDescription className="text-teal-700">
              Public-source facts remain attributable to their original
              publishers. GaiaFAAC charges for the governed evidence layer
              around those facts.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="space-y-3 text-sm">
              {paidValue.map((item) => (
                <li key={item} className="flex items-start gap-2">
                  <Check
                    className="mt-0.5 size-4 shrink-0 text-teal-900"
                    aria-hidden="true"
                  />
                  <span className="text-teal-900">{item}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>

        <Card className="border-amber-200 bg-amber-50">
          <CardHeader>
            <DatabaseZap className="size-5 text-amber-900" aria-hidden="true" />
            <CardTitle className="pt-3 text-amber-900">
              Commercial boundary
            </CardTitle>
            <CardDescription className="text-amber-700">
              Public evidence stays attributable. Commercial value comes from
              verification, structuring, monitoring, workflow, delivery and
              licensed use—not from claiming ownership of government records.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm leading-6 text-amber-800">
              Start with Team or API when self-service is enough. Move to an
              institutional agreement when the use case includes organization-
              wide deployment, downstream redistribution, custom data delivery
              or dedicated evidence operations.
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="text-muted-foreground mt-10 max-w-4xl space-y-2 text-sm leading-6">
        <p>
          Monthly self-service prices are in Nigerian Naira (₦). Checkout,
          billing management and plan entitlements are handled through the
          GaiaFAAC customer account with Paystack.
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
