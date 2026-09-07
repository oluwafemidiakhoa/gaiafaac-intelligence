import {
  ArrowRight,
  Building2,
  Check,
  DatabaseZap,
  FileCheck2,
  ShieldCheck,
  Sparkles,
} from 'lucide-react'
import type { Metadata } from 'next'
import Link from 'next/link'

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
    'Commercial access to governed Nigerian fiscal evidence, historical research, one-time intelligence products, team workflows and APIs.',
}

interface CommercialProduct {
  code: string
  label: string
  billing_mode: string
  description: string
  plan_code: string | null
  price_naira: number | null
}

const subscriptionDefinitions = [
  {
    code: 'public',
    name: 'Free',
    period: '',
    tagline: 'Verify the current public evidence layer.',
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
    code: 'subscription_analyst',
    name: 'Analyst',
    period: '/30 days',
    tagline: 'For researchers, advisers and individual analysts.',
    features: [
      'Historical published evidence',
      'CSV and Excel exports',
      'Source-linked proof objects',
      'Single-user workspace',
    ],
    cta: 'Start Analyst',
    href: '/account/signup?plan=analyst',
    featured: true,
  },
  {
    code: 'subscription_team',
    name: 'Team',
    period: '/30 days',
    tagline: 'For research, risk and advisory teams.',
    features: [
      'Everything in Analyst',
      'Up to 10 organization members',
      'Shared governed workflow',
      'Team administration',
    ],
    cta: 'Start Team',
    href: '/account/signup?plan=team',
    featured: false,
  },
  {
    code: 'subscription_api',
    name: 'API',
    period: '/30 days',
    tagline: 'For products and systems consuming governed evidence.',
    features: [
      'Everything in Team',
      'Programmatic API access',
      '5,000 API requests/day',
      'API keys and integration workflows',
    ],
    cta: 'Start API',
    href: '/account/signup?plan=api',
    featured: false,
  },
]

const oneTimeProductOrder = [
  'decision_pack',
  'multi_state_comparison_pack',
  'historical_evidence_export',
  'due_diligence_snapshot',
]

const institutionalProducts = [
  {
    icon: ShieldCheck,
    name: 'Institutional Intelligence',
    buyer: 'Banks, asset managers, advisers and research teams',
    description:
      'Organization-wide fiscal monitoring, governed evidence support, custom onboarding and licensed internal use.',
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

function apiBaseUrl() {
  return (
    process.env.API_INTERNAL_URL ??
    process.env.NEXT_PUBLIC_API_URL ??
    'http://localhost:8000'
  ).replace(/\/$/, '')
}

async function loadCommercialProducts(): Promise<CommercialProduct[]> {
  try {
    const response = await fetch(`${apiBaseUrl()}/api/v1/commercial/products`, {
      cache: 'no-store',
    })
    if (!response.ok) return []
    return (await response.json()) as CommercialProduct[]
  } catch {
    return []
  }
}

function formatNaira(value: number | null | undefined) {
  if (value === null || value === undefined) return 'Price unavailable'
  return new Intl.NumberFormat('en-NG', {
    style: 'currency',
    currency: 'NGN',
    maximumFractionDigits: 0,
  }).format(value)
}

export default async function PricingPage() {
  const catalog = await loadCommercialProducts()
  const productByCode = new Map(
    catalog.map((product) => [product.code, product]),
  )
  const oneTimeProducts = oneTimeProductOrder
    .map((code) => productByCode.get(code))
    .filter((product): product is CommercialProduct => Boolean(product))

  return (
    <div className="pb-8">
      <section className="relative overflow-hidden border-b border-white/8 bg-[#041915] text-white">
        <div className="absolute top-0 left-1/3 size-[30rem] rounded-full bg-amber-300/[0.06] blur-3xl" />
        <div className="gaia-shell relative grid gap-12 py-16 lg:grid-cols-[1.05fr_.95fr] lg:items-end lg:py-24">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-amber-200/15 bg-amber-200/[0.06] px-3 py-1.5">
              <Sparkles className="size-3.5 text-amber-300" />
              <span className="font-mono text-[0.65rem] font-bold tracking-[0.18em] text-amber-100 uppercase">
                Commercial access / Governed intelligence
              </span>
            </div>
            <h1 className="mt-6 max-w-[14ch] text-5xl leading-[0.96] font-semibold tracking-[-0.06em] text-balance sm:text-6xl lg:text-7xl">
              Pay for the intelligence layer, not the public record.
            </h1>
            <p className="mt-6 max-w-2xl text-lg leading-8 text-emerald-50/65">
              Public evidence stays attributable to its source. Choose ongoing
              subscription access for research workflows, or buy a one-time
              governed intelligence package for a defined decision boundary.
            </p>
          </div>

          <div className="gaia-panel-dark p-6 sm:p-7">
            <p className="font-mono text-[0.62rem] font-semibold tracking-[0.16em] text-emerald-200/45 uppercase">
              Commercial principle
            </p>
            <h2 className="mt-3 text-2xl font-semibold tracking-[-0.035em]">
              Evidence remains inspectable before the customer buys.
            </h2>
            <p className="mt-4 text-sm leading-7 text-white/55">
              The paid moat is the governed evidence graph, historical depth,
              decision workflow and delivery infrastructure—not a paywall around
              government facts.
            </p>
            <div className="mt-6 grid grid-cols-2 gap-3">
              <div className="rounded-2xl border border-white/10 bg-white/[0.035] p-4">
                <p className="font-mono text-[0.58rem] tracking-[0.14em] text-white/35 uppercase">
                  Subscription
                </p>
                <p className="mt-2 text-sm font-semibold text-emerald-100">
                  Ongoing workspace access
                </p>
              </div>
              <div className="rounded-2xl border border-white/10 bg-white/[0.035] p-4">
                <p className="font-mono text-[0.58rem] tracking-[0.14em] text-white/35 uppercase">
                  One-time
                </p>
                <p className="mt-2 text-sm font-semibold text-amber-200">
                  Frozen intelligence package
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <div className="gaia-shell gaia-section">
        <section aria-labelledby="subscription-access">
          <div className="mb-7 max-w-3xl">
            <p className="gaia-kicker">Subscription access</p>
            <h2
              id="subscription-access"
              className="mt-2 text-3xl font-semibold tracking-[-0.04em]"
            >
              Ongoing research, collaboration and API access
            </h2>
            <p className="text-muted-foreground mt-3 leading-7">
              These plans renew every 30 days. They are separate from the
              one-time Decision Pack and other project products below.
            </p>
          </div>

          <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
            {subscriptionDefinitions.map((plan) => {
              const product = productByCode.get(plan.code)
              return (
                <Card
                  key={plan.name}
                  className={`relative overflow-hidden ${
                    plan.featured
                      ? 'border-primary/45 shadow-[0_24px_70px_rgba(3,88,75,0.13)]'
                      : ''
                  }`}
                >
                  {plan.featured ? (
                    <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-emerald-500 via-amber-300 to-emerald-500" />
                  ) : null}
                  <CardHeader>
                    <div className="flex items-center justify-between gap-3">
                      <p className="gaia-kicker">
                        {plan.featured ? 'Recommended' : 'Access tier'}
                      </p>
                      {plan.featured ? (
                        <span className="bg-primary/10 text-primary rounded-full px-2.5 py-1 font-mono text-[0.58rem] font-bold tracking-[0.12em] uppercase">
                          Start here
                        </span>
                      ) : null}
                    </div>
                    <CardTitle className="pt-4 text-2xl">{plan.name}</CardTitle>
                    <div className="flex items-baseline gap-1 pt-1">
                      <span className="font-mono text-3xl font-semibold tracking-[-0.04em]">
                        {formatNaira(product?.price_naira)}
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
                    <ul className="space-y-3 text-sm">
                      {plan.features.map((feature) => (
                        <li key={feature} className="flex items-start gap-2.5">
                          <div className="bg-primary/10 mt-0.5 flex size-4 shrink-0 items-center justify-center rounded-full">
                            <Check className="text-primary size-3" />
                          </div>
                          <span>{feature}</span>
                        </li>
                      ))}
                    </ul>
                    <Button
                      asChild
                      className="mt-7 w-full"
                      variant={plan.featured ? 'default' : 'outline'}
                    >
                      <Link href={plan.href}>
                        {plan.cta} <ArrowRight className="size-4" />
                      </Link>
                    </Button>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        </section>

        <section className="mt-16" aria-labelledby="one-time-products">
          <div className="flex flex-wrap items-end justify-between gap-5">
            <div className="max-w-3xl">
              <p className="gaia-kicker">One-time intelligence products</p>
              <h2
                id="one-time-products"
                className="mt-2 text-3xl font-semibold tracking-[-0.04em]"
              >
                Buy a governed result without starting a subscription
              </h2>
              <p className="text-muted-foreground mt-3 leading-7">
                These are one-time engagements. Gaia validates the requested
                evidence boundary before checkout and freezes the delivered
                result to that order.
              </p>
            </div>
            <Button asChild>
              <Link href="/projects">
                Explore project products <ArrowRight className="size-4" />
              </Link>
            </Button>
          </div>

          <div className="mt-7 grid gap-5 md:grid-cols-2 xl:grid-cols-4">
            {oneTimeProducts.map((product) => (
              <Card key={product.code} className="flex h-full flex-col">
                <CardHeader>
                  <FileCheck2 className="text-primary size-5" />
                  <CardTitle className="pt-3 text-xl">
                    {product.label}
                  </CardTitle>
                  <CardDescription>{product.description}</CardDescription>
                </CardHeader>
                <CardContent className="flex h-full flex-col">
                  <p className="font-mono text-2xl font-semibold tracking-[-0.03em]">
                    {formatNaira(product.price_naira)}
                  </p>
                  <p className="text-muted-foreground mt-1 text-xs">
                    one-time governed intelligence engagement
                  </p>
                  <Button asChild variant="outline" className="mt-6 w-full">
                    <Link href="/projects">
                      {product.code === 'decision_pack'
                        ? 'View sample & buy'
                        : 'Define boundary & buy'}
                      <ArrowRight className="size-4" />
                    </Link>
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>

          <Card className="border-primary/30 bg-primary/[0.035] mt-6">
            <CardContent className="flex flex-wrap items-center justify-between gap-4 py-5">
              <div>
                <p className="font-semibold">Why two ₦50,000 offers?</p>
                <p className="text-muted-foreground mt-1 max-w-3xl text-sm leading-6">
                  Analyst is recurring workspace access for 30 days. The
                  Individual Decision Pack is a one-time frozen intelligence
                  package for one jurisdiction and a defined evidence period.
                </p>
              </div>
              <Button asChild variant="outline">
                <Link href="/projects">See Decision Pack sample</Link>
              </Button>
            </CardContent>
          </Card>
        </section>

        <section className="mt-14 overflow-hidden rounded-3xl border border-white/8 bg-[#061d19] text-white shadow-[0_28px_90px_rgba(0,0,0,.16)]">
          <div className="p-7 sm:p-9">
            <div className="max-w-3xl">
              <p className="font-mono text-[0.65rem] font-semibold tracking-[0.18em] text-amber-200/55 uppercase">
                Enterprise / Contracted
              </p>
              <h2 className="mt-4 text-4xl font-semibold tracking-[-0.045em] text-balance">
                When self-service is too small, buy Gaia as infrastructure.
              </h2>
              <p className="mt-5 max-w-2xl leading-7 text-white/55">
                Institution-wide deployment, redistribution rights, custom data
                delivery and dedicated evidence operations are scoped
                separately.
              </p>
            </div>

            <div className="mt-8 grid gap-4 lg:grid-cols-3">
              {institutionalProducts.map(
                ({ icon: Icon, name, buyer, description }) => (
                  <article
                    key={name}
                    className="rounded-2xl border border-white/10 bg-white/[0.035] p-6"
                  >
                    <div className="flex size-10 items-center justify-center rounded-xl bg-emerald-300/[0.08]">
                      <Icon className="size-5 text-emerald-300" />
                    </div>
                    <h3 className="mt-6 text-lg font-semibold">{name}</h3>
                    <p className="mt-2 text-sm font-medium text-emerald-100/60">
                      {buyer}
                    </p>
                    <p className="mt-4 text-sm leading-6 text-white/50">
                      {description}
                    </p>
                  </article>
                ),
              )}
            </div>

            <div className="mt-8 flex flex-wrap items-center justify-between gap-5 border-t border-white/10 pt-7">
              <div>
                <p className="font-semibold">
                  Need organization-wide deployment?
                </p>
                <p className="mt-1 text-sm text-white/45">
                  Scope workflow, permitted use, data volume and support before
                  pricing the contract.
                </p>
              </div>
              <Button
                asChild
                size="lg"
                className="rounded-full bg-amber-300 font-bold text-teal-950 hover:bg-amber-200"
              >
                <Link href="/pilot?plan=team#request-form">
                  Request institutional pilot <ArrowRight className="size-4" />
                </Link>
              </Button>
            </div>
          </div>
        </section>

        <div className="mt-8 grid gap-5 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>What the customer buys</CardTitle>
            </CardHeader>
            <CardContent className="text-muted-foreground space-y-3 text-sm leading-6">
              <p>
                Human-reviewed publication controls and retained provenance.
              </p>
              <p>
                Historical evidence structured for repeatable research and
                export.
              </p>
              <p>
                Licensed workflow, delivery and API access according to plan or
                a frozen intelligence result according to the project order.
              </p>
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
    </div>
  )
}
