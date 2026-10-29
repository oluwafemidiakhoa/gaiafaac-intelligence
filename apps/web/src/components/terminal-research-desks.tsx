import Link from 'next/link'

const desks = [
  { href: '/insights', title: 'Explore trends' },
  { href: '/compare', title: 'Compare jurisdictions' },
  { href: '/watchlist', title: 'Your fiscal watchlist' },
  { href: '/national-reconciliation', title: 'National reconciliation' },
] as const

export function TerminalResearchDesks() {
  return (
    <section aria-labelledby="research-desks-heading" className="mt-10">
      <h2 id="research-desks-heading" className="text-3xl font-semibold">
        Fiscal research desks
      </h2>
      <p className="text-muted-foreground mt-3 text-sm">
        Research published fiscal evidence, not stock quotes or trading signals.
      </p>
      <div className="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {desks.map((desk) => (
          <Link
            key={desk.href}
            href={desk.href}
            className="gaia-panel p-5 font-semibold hover:underline"
          >
            {desk.title}
          </Link>
        ))}
      </div>
      <p className="text-muted-foreground mt-4 text-xs">
        Data freshness and availability are shown in each research destination.
        Missing evidence is not zero.
      </p>
      <Link href="/sources" className="text-primary mt-4 inline-block">
        Audit source registry
      </Link>
    </section>
  )
}
