import { ChevronDown, Menu } from 'lucide-react'
import Link from 'next/link'

import { Button } from '@/components/ui/button'
import { formatDate } from '@/lib/format'
import { getPublishedOverview } from '@/lib/published-api'

const primaryNavigation = [
  { href: '/live', label: 'Live data' },
  { href: '/states', label: 'Jurisdictions' },
  { href: '/fiscal-pulse', label: 'Fiscal Pulse' },
  { href: '/sources', label: 'Sources' },
]

const moreNavigation = [
  { href: '/overview', label: 'Overview' },
  { href: '/insights', label: 'Insights' },
  { href: '/events', label: 'Fiscal Events' },
  { href: '/compare', label: 'Compare jurisdictions' },
  { href: '/gaia-analyst', label: 'Gaia Analyst' },
  { href: '/fiscal-design', label: 'Fiscal Design Lab' },
  { href: '/fiscal-watch', label: 'Fiscal Watch' },
  { href: '/decision-packets', label: 'Decision Packets' },
  { href: '/methodology', label: 'Methodology' },
  { href: '/pricing', label: 'Pricing' },
]

export async function SiteHeader() {
  const overview = await getPublishedOverview()
  const data = overview.data

  return (
    <header className="border-border/80 bg-background/95 sticky top-0 z-50 border-b backdrop-blur">
      <div className="border-border/70 bg-muted/30 border-b">
        <div className="text-muted-foreground mx-auto flex max-w-7xl items-center justify-between gap-4 px-5 py-2 text-xs lg:px-8">
          <p className="min-w-0 truncate">
            <span className="text-foreground font-medium">
              Governed public evidence
            </span>
            {data ? (
              <>
                {' '}
                · Latest verified {formatDate(data.period.revenue_month)} ·{' '}
                {data.covered_states}/{data.expected_states} jurisdictions
              </>
            ) : (
              <> · Human review required before publication</>
            )}
          </p>
          <Link
            href="/sources"
            className="text-foreground hover:text-primary shrink-0 font-medium transition-colors"
          >
            Evidence registry
          </Link>
        </div>
      </div>

      <div className="mx-auto flex min-h-16 max-w-7xl items-center gap-6 px-5 py-3 lg:px-8">
        <Link
          href="/"
          className="flex shrink-0 items-center gap-3"
          aria-label="GaiaFAAC home"
        >
          <span className="bg-primary text-primary-foreground flex size-9 items-center justify-center rounded-md font-mono text-sm font-semibold">
            GF
          </span>
          <span>
            <span className="block font-semibold tracking-tight">GaiaFAAC</span>
            <span className="text-muted-foreground hidden text-[0.68rem] xl:block">
              Nigeria fiscal evidence ledger
            </span>
          </span>
        </Link>

        <nav
          className="ml-auto hidden items-center gap-6 lg:flex"
          aria-label="Primary navigation"
        >
          {primaryNavigation.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="text-muted-foreground hover:text-foreground whitespace-nowrap text-sm transition-colors"
            >
              {item.label}
            </Link>
          ))}
          <details className="relative">
            <summary className="text-muted-foreground hover:text-foreground flex cursor-pointer list-none items-center gap-1 whitespace-nowrap text-sm transition-colors [&::-webkit-details-marker]:hidden">
              More
              <ChevronDown className="size-3.5" aria-hidden="true" />
            </summary>
            <div className="border-border bg-background absolute right-0 z-50 mt-3 w-64 rounded-lg border p-2 shadow-lg">
              {moreNavigation.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className="hover:bg-muted block rounded-md px-3 py-2 text-sm transition-colors"
                >
                  {item.label}
                </Link>
              ))}
            </div>
          </details>
        </nav>

        <Button asChild size="sm" className="hidden lg:inline-flex">
          <Link href="/pilot">Pilot access</Link>
        </Button>

        <details className="relative ml-auto lg:hidden">
          <summary className="border-border hover:bg-muted flex h-9 cursor-pointer list-none items-center gap-2 rounded-md border px-3 text-sm font-medium [&::-webkit-details-marker]:hidden">
            <Menu className="size-4" aria-hidden="true" />
            Menu
          </summary>
          <div className="border-border bg-background absolute right-0 z-50 mt-3 w-72 rounded-lg border p-3 shadow-lg">
            <nav className="grid gap-1" aria-label="Mobile navigation">
              {[...primaryNavigation, ...moreNavigation].map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className="hover:bg-muted rounded-md px-3 py-2 text-sm transition-colors"
                >
                  {item.label}
                </Link>
              ))}
              <Link
                href="/pilot"
                className="bg-primary text-primary-foreground mt-2 rounded-md px-3 py-2 text-center text-sm font-medium"
              >
                Pilot access
              </Link>
            </nav>
          </div>
        </details>
      </div>
    </header>
  )
}
