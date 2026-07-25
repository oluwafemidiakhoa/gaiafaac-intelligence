import {
  ArrowRight,
  Database,
  FileCheck2,
  GitCompareArrows,
  Map,
} from 'lucide-react'
import Link from 'next/link'

import { DemoBanner } from '@/components/demo-banner'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'

const destinations = [
  {
    href: '/overview',
    icon: Database,
    title: 'National overview',
    description:
      'Inspect the explicitly partial three-state demo sample and its source status.',
  },
  {
    href: '/states',
    icon: Map,
    title: 'State directory',
    description:
      'Browse all 36 states and the FCT, with unavailable values left blank.',
  },
  {
    href: '/compare',
    icon: GitCompareArrows,
    title: 'State comparison',
    description:
      'Compare two to six jurisdictions without filling missing demo records.',
  },
]

export default function Home() {
  return (
    <>
      <DemoBanner />
      <section className="border-border/80 border-b">
        <div className="mx-auto grid max-w-7xl gap-12 px-5 py-20 lg:grid-cols-[1.3fr_0.7fr] lg:px-8 lg:py-28">
          <div className="max-w-3xl">
            <p className="text-primary mb-5 font-mono text-xs font-semibold tracking-[0.18em] uppercase">
              Independent public-finance research
            </p>
            <h1 className="text-5xl font-semibold tracking-[-0.045em] text-balance sm:text-6xl lg:text-7xl">
              Nigeria’s Public Revenue, Explained
            </h1>
            <p className="text-muted-foreground mt-7 max-w-2xl text-lg leading-8 text-pretty">
              Explore the Milestone 4 interface using a small, synthetic,
              future-dated dataset built to demonstrate traceability without
              representing real FAAC allocations.
            </p>
            <div className="mt-9 flex flex-col gap-3 sm:flex-row">
              <Button asChild size="lg">
                <Link href="/overview">
                  Explore the demo overview
                  <ArrowRight className="size-4" aria-hidden="true" />
                </Link>
              </Button>
              <Button asChild size="lg" variant="outline">
                <Link href="/methodology">Read the methodology</Link>
              </Button>
            </div>
          </div>
          <Card className="bg-muted/30 self-end">
            <CardHeader>
              <FileCheck2 className="text-primary size-5" aria-hidden="true" />
              <p className="text-muted-foreground pt-3 font-mono text-xs tracking-wider uppercase">
                Milestone 04
              </p>
              <CardTitle className="text-2xl">Demo interface available</CardTitle>
              <CardDescription>
                Every visible amount is synthetic, unpublished, and linked to
                the labelled demo source.
              </CardDescription>
            </CardHeader>
          </Card>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-5 py-20 lg:px-8">
        <div className="max-w-2xl">
          <p className="text-primary font-mono text-xs font-semibold tracking-[0.18em] uppercase">
            Explore the interface
          </p>
          <h2 className="mt-4 text-3xl font-semibold tracking-tight sm:text-4xl">
            Missing data stays visibly missing
          </h2>
        </div>
        <div className="mt-10 grid gap-5 md:grid-cols-3">
          {destinations.map(({ href, icon: Icon, title, description }) => (
            <Link key={href} href={href} className="group">
              <Card className="group-hover:border-primary/40 h-full transition-colors">
                <CardHeader>
                  <Icon className="text-primary size-5" aria-hidden="true" />
                  <CardTitle className="pt-3">{title}</CardTitle>
                  <CardDescription>{description}</CardDescription>
                </CardHeader>
              </Card>
            </Link>
          ))}
        </div>
      </section>
    </>
  )
}
