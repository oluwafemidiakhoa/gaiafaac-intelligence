import { Building2, Check, DatabaseZap, ShieldCheck } from 'lucide-react'
import type { Metadata } from 'next'
import Link from 'next/link'

import { PageHeader } from '@/components/page-header'
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
    'Commercial access to governed Nigerian fiscal evidence, historical research, team workflows and APIs.',
}

const plans = [
  {
    name: 'Free',
    price: '₦0',
    period: '',
    tagline: 'Verify current governed public evidence.',
    features: [
      'Latest verified FAAC publication',
      '36 states and the FCT',
      'Public comparisons',
      'Source registry and fingerprints',
    ],
    cta: 'Explore public data',
    href: '/live',
    featured: false,
  },
  {
    name: 'Analyst',
    price: '₦50,000',
    period: '/30 days',
    tagline: 'For researchers, advisers and individual analysts.',
    features: [
      'Historical published evidence',
      'CSV and Excel exports',
      'Source-linked proof objects',
      'Single-user workspace',
    ],
    cta: 'Buy Analyst access',
    href: '/account/signup?plan=analyst',
    featured: true,
  },
  {
    name: 'Team',
    price: '₦200,000',
    period: '/30 days',
    tagline: 'For research, risk and advisory teams.',
    features: [
      'Everything in Analyst',
      'Up to 10 organization members',
      'Shared governed workflow',
      'Team administration',
    ],
    cta: 'Buy Team access',
    href: '/account/signup?plan=team',
    featured: false,
  },
  {
    name: 'API',
    price: '₦300,000',
    period: '/30 days',
    tagline: 'For products and systems consuming governed evidence.',
    features: [
      'Everything in Team',
      'Programmatic API access',
      '5,000 API requests/day',
      'API keys and integration workflows',
    ],
    cta: 'Buy API access',
    href: '/account/signup?plan=api',
    featured: false,
  },
]

const institutionalProducts = [
  {
    icon: ShieldCheck,
    name: 'Institutional Intelligence',
    buyer: 'Banks, asset managers, advisers and research teams',
    description:
      'Annual organization-wide fiscal monitoring, governed evidence support, custom onboarding and licensed internal use.',
  },
  {
    icon: DatabaseZap,
    name: 'Data & Evidence Feed',
    buyer: 'Fintechs, data companies and internal data platforms',
    description:
      'Higher-volume delivery, downstream-use licensing, revision-aware feeds and integration support.',
  },
  {
    icon: Building2,
    name: 'Government Evidence Workspace',
    buyer: 'Public institutions and development organizations',
    description:
      'Dedicated evidence rooms, comparative fiscal workflows and durable decision records.',
  },
]

export default function PricingPage() {
  return (
    <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
      <PageHeader
        eyebrow="Commercial access"
        title="Pay for the governed evidence layer—not for public records."
        description="Current public evidence remains open. Paid plans unlock the work institutions actually spend money on: historical research, reproducible exports, team workflows, API delivery and governed decision infrastructure."
      />

      <div className="mt-10 grid gap-5 md:grid-cols-2 xl:grid-cols-4">
        {plans.map((plan) => (
          <Card
            key={plan.name}
            className={plan.featured ? 'border-primary shadow-md' : ''}
          >
            <CardHeader>
              {plan.featured ? (
                <p className="text-primary font-mono text-xs font-semibold tracking-[0.15em] uppercase">
                  Best starting point
                </p>
              ) : null}
              <CardTitle className="pt-2 text-2xl">{plan.name}</CardTitle>
              <div className="flex items-baseline gap-1">
                <span className="text-3xl font-semibold tracking-tight">
                  {plan.price}
                </span>
                {plan.period ? (
                  <span className="text-muted-foreground text-xs">
                    {plan.period}
                  </span>
                ) : null}
              </div>
              <CardDescription>{plan.tagline}</CardDescription>
            </CardHeader>
            <CardContent className="flex h-full flex-col">
              <ul className="space-y-2.5 text-sm">
                {plan.features.map((feature) => (
                  <li key={feature} className="flex items-start gap-2">
                    <Check className="text-primary mt-0.5 size-4 shrink-0" />
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

      <section className="mt-16 rounded-2xl border border-teal-900/10 bg-teal-950 p-7 text-white sm:p-10">
        <div className="max-w-3xl">
          <p className="font-mono text-xs font-semibold tracking-[0.16em] text-emerald-300 uppercase">
            Larger contracts
          </p>
          <h2 className="mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">
            When self-service is too small, buy Gaia as infrastructure.
          </h2>
          <p className="mt-4 leading-7 text-teal-50/70">
            Institution-wide deployment, redistribution rights, custom data
            delivery and dedicated evidence operations are contracted
            separately.
          </p>
        </div>

        <div className="mt-8 grid gap-5 lg:grid-cols-3">
          {institutionalProducts.map(
            ({ icon: Icon, name, buyer, description }) => (
              <article
                key={name}
                className="rounded-2xl border border-white/10 bg-white/[0.05] p-6"
              >
                <Icon className="size-5 text-emerald-300" />
                <h3 className="mt-5 text-lg font-semibold">{name}</h3>
                <p className="mt-2 text-sm font-medium text-teal-100/70">
                  {buyer}
                </p>
                <p className="mt-4 text-sm leading-6 text-teal-50/65">
                  {description}
                </p>
              </article>
            ),
          )}
        </div>

        <div className="mt-8 flex flex-wrap items-center justify-between gap-5 border-t border-white/10 pt-7">
          <div>
            <p className="font-semibold">Need organization-wide use?</p>
            <p className="mt-1 text-sm text-teal-50/60">
              Scope the workflow, permitted use, data volume and support before
              pricing the contract.
            </p>
          </div>
          <Button
            asChild
            size="lg"
            className="bg-amber-300 text-teal-950 hover:bg-amber-200"
          >
            <Link href="/pilot?plan=team#request-form">
              Request institutional pilot
            </Link>
          </Button>
        </div>
      </section>

      <div className="mt-10 grid gap-5 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>What the customer buys</CardTitle>
          </CardHeader>
          <CardContent className="text-muted-foreground space-y-2 text-sm leading-6">
            <p>Human-reviewed publication controls and retained provenance.</p>
            <p>
              Historical evidence structured for repeatable research and export.
            </p>
            <p>Licensed workflow, delivery and API access according to plan.</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Commercial boundary</CardTitle>
          </CardHeader>
          <CardContent className="text-muted-foreground text-sm leading-6">
            Public-source facts remain attributable to their publishers. Gaia
            charges for verification, structuring, monitoring, workflow,
            delivery and licensed use around those facts.
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
