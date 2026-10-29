import {
  ArrowUpRight,
  BellRing,
  ChartNoAxesCombined,
  GitCompareArrows,
  Landmark,
  ShieldCheck,
} from 'lucide-react'
import Link from 'next/link'

const researchDesks = [
  {
    href: '/insights',
    title: 'Explore trends',
    description: 'Published allocation history, rankings and movements.',
    icon: ChartNoAxesCombined,
    label: 'Historical research',
  },
  {
    href: '/compare',
    title: 'Compare jurisdictions',
    description: 'Compare two to six jurisdictions using governed data.',
    icon: GitCompareArrows,
    label: 'Relative analysis',
  },
  {
    href: '/watchlist',
    title: 'Your fiscal watchlist',
    description: 'Follow jurisdictions and review evidence-linked alerts.',
    icon: BellRing,
    label: 'Monitoring',
  },
  {
    href: '/national-reconciliation',
    title: 'National reconciliation',
    description:
      'Inspect independent national sources and reconciliation status.',
    icon: Landmark,
    label: 'Evidence review',
  },
] as const

/** Navigation only: this component never computes or implies financial figures. */
export function TerminalResearchDesks() {
  return (
    <section aria-labelledby="terminal-research-title" className="mt-10">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="gaia-kicker">Research desks</p>
          <h2
            id="terminal-research-title"
            className="mt-3 text-3xl font-semibold tracking-[-0.04em]"
          >
            One terminal. Four research paths.
          </h2>
          <p className="text-muted-foreground mt-3 max-w-3xl text-sm leading-6">
            Market-terminal convenience for public-finance research, grounded
            in published Nigerian fiscal evidence—not stock quotes, trades or
            investment recommendations.
          </p>
        </div>
        <Link
          href="/sources"
          className="text-primary inline-flex items-center gap-2 text-sm font-semibold hover:underline"
        >
          <ShieldCheck aria-hidden="true" className="size-4" /> Audit source
          registry
        </Link>
      </div>
      <div className="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {researchDesks.map(({ href, title, description, icon: Icon, label }) => (
          <Link
            key={href}
            href={href}
            className="gaia-panel group flex h-full flex-col p-5 transition hover:-translate-y-1 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-500"
          >
            <div className="flex items-center justify-between">
              <span className="bg-primary/[0.07] flex size-10 items-center justify-center rounded-xl">
                <Icon aria-hidden="true" className="text-primary size-5" />
              </span>
              <ArrowUpRight
                aria-hidden="true"
                className="text-muted-foreground size-4 transition group-hover:translate-x-0.5 group-hover:-translate-y-0.5"
              />
            </div>
            <p className="text-muted-foreground mt-5 font-mono text-[0.65rem] font-semibold tracking-[0.14em] uppercase">
              {label}
            </p>
            <h3 className="mt-2 text-lg font-semibold tracking-tight">
              {title}
            </h3>
            <p className="text-muted-foreground mt-2 flex-1 text-sm leading-6">
              {description}
            </p>
            <span className="text-primary mt-5 text-sm font-semibold">
              Open research desk
            </span>
          </Link>
        ))}
      </div>
      <p className="text-muted-foreground mt-4 text-xs leading-5">
        Availability and freshness are established inside each destination
        from its governed records. Missing evidence is not treated as zero.
      </p>
    </section>
  )
}
