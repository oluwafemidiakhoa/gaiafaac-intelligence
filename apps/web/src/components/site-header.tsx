import Link from 'next/link'

const navigation = [
  { href: '/live', label: 'Live data' },
  { href: '/review/pending', label: 'Review queue' },
  { href: '/overview', label: 'Overview' },
  { href: '/states', label: 'States' },
  { href: '/compare', label: 'Compare' },
  { href: '/sources', label: 'Sources' },
  { href: '/methodology', label: 'Methodology' },
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
          <span className="font-semibold tracking-tight">
            GaiaFAAC Intelligence
          </span>
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
