import Link from 'next/link'

const navigation = [
  { href: '/events', label: 'Fiscal Events' },
  { href: '/gaia-analyst', label: 'Gaia Analyst' },
  { href: '/fiscal-design', label: 'Fiscal Design Lab' },
  { href: '/fiscal-watch', label: 'Fiscal Watch' },
  { href: '/fiscal-pulse', label: 'Fiscal Pulse' },
  { href: '/decision-packets', label: 'Decision Packets' },
  { href: '/live', label: 'Live data' },
  { href: '/insights', label: 'Insights' },
  { href: '/overview', label: 'Overview' },
  { href: '/states', label: 'Jurisdictions' },
  { href: '/compare', label: 'Compare' },
  { href: '/sources', label: 'Sources' },
  { href: '/methodology', label: 'Methodology' },
  { href: '/pricing', label: 'Pricing' },
  { href: '/pilot', label: 'Pilot access' },
]

export function SiteHeader() {
  return (
    <header className="border-border/80 border-b">
      <div className="mx-auto flex min-h-16 max-w-7xl flex-wrap items-center justify-between gap-3 px-5 py-3 lg:px-8">
        <Link
          href="/"
          className="flex items-center gap-3"
          aria-label="GaiaFAAC home"
        >
          <span className="bg-primary text-primary-foreground flex size-9 items-center justify-center rounded-md font-mono text-sm font-semibold">
            GF
          </span>
          <span className="font-semibold tracking-tight">GaiaFAAC</span>
        </Link>
        <nav
          className="order-last flex w-full items-center gap-5 overflow-x-auto pt-1 md:order-none md:w-auto md:gap-7 md:pt-0"
          aria-label="Primary navigation"
        >
          {navigation.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="text-muted-foreground hover:text-foreground text-sm transition-colors"
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  )
}
