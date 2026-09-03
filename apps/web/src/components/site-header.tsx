import { Menu } from 'lucide-react'
import Link from 'next/link'

import { ThemeToggle } from '@/components/theme-toggle'
import { Button } from '@/components/ui/button'
import { formatDate } from '@/lib/format'
import { getPublishedOverview } from '@/lib/published-api'

const navigation = [
  { href: '/terminal', label: 'Terminal' },
  { href: '/institutional', label: 'Institutions' },
  { href: '/live', label: 'Live data' },
  { href: '/fiscal-pulse', label: 'Intelligence' },
  { href: '/sources', label: 'Evidence' },
  { href: '/review', label: 'Review' },
]

export async function SiteHeader() {
  const overview = await getPublishedOverview()
  const data = overview.data

  return (
    <header className="sticky top-0 z-50 border-b border-teal-900/20 bg-gradient-to-r from-teal-950 to-teal-900 text-white">
      <div className="border-b border-teal-900/50 bg-teal-900/40">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-5 py-2 text-xs lg:px-8">
          <p className="min-w-0 truncate text-amber-100">
            <span className="font-semibold text-amber-50">
              Governed public evidence
            </span>
            {data ? (
              <>
                {' '}
                · Latest verified {formatDate(data.period.revenue_month)} ·{' '}
                <span className="font-medium">{data.covered_states}/{data.expected_states} jurisdictions</span>
              </>
            ) : (
              <> · Human review required before publication</>
            )}
          </p>
          <Link
            href="/sources"
            className="shrink-0 font-medium text-amber-200 hover:text-amber-100 transition-colors"
          >
            Evidence registry →
          </Link>
        </div>
      </div>

      <div className="mx-auto flex min-h-16 max-w-7xl items-center gap-5 px-5 py-3 lg:px-8">
        <Link
          href="/"
          className="flex shrink-0 items-center gap-3 group"
          aria-label="Gaia Fiscal Intelligence home"
        >
          <div className="flex size-10 items-center justify-center rounded-lg bg-amber-400 text-teal-950 font-bold text-sm font-mono group-hover:bg-amber-300 transition-colors">
            GF
          </div>
          <span>
            <span className="block font-bold tracking-tight text-white">
              Gaia
            </span>
            <span className="text-amber-100/80 text-[0.75rem] font-medium">
              Fiscal Intelligence
            </span>
          </span>
        </Link>

        <nav
          className="ml-auto hidden items-center gap-6 lg:flex"
          aria-label="Primary navigation"
        >
          {navigation.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="text-amber-50/90 hover:text-amber-200 text-sm font-medium whitespace-nowrap transition-colors"
            >
              {item.label}
            </Link>
          ))}
        </nav>

        <div className="hidden items-center gap-2 lg:flex">
          <Button asChild size="sm" className="bg-amber-400 text-teal-950 hover:bg-amber-300 font-medium">
            <Link href="/gaia-analyst">Ask Gaia</Link>
          </Button>
          <Button asChild size="sm" className="bg-teal-800 hover:bg-teal-700 border border-teal-600 text-white">
            <Link href="/pilot">Request Watch</Link>
          </Button>
          <ThemeToggle />
        </div>

        <details className="relative ml-auto lg:hidden">
          <summary className="hover:bg-teal-800 flex h-9 cursor-pointer list-none items-center gap-2 rounded-md border border-teal-600 px-3 text-sm font-medium text-white [&::-webkit-details-marker]:hidden">
            <Menu className="size-4" aria-hidden="true" />
            Menu
          </summary>
          <div className="absolute right-0 z-50 mt-3 w-72 rounded-lg border border-teal-700 bg-teal-900 p-3 shadow-xl">
            <nav className="grid gap-1" aria-label="Mobile navigation">
              {navigation.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className="hover:bg-teal-800 rounded-md px-3 py-2 text-sm text-amber-50 transition-colors font-medium"
                >
                  {item.label}
                </Link>
              ))}
              <Link
                href="/gaia-analyst"
                className="hover:bg-teal-800 rounded-md px-3 py-2 text-sm text-amber-50 transition-colors font-medium"
              >
                Ask Gaia
              </Link>
              <Link
                href="/pilot"
                className="bg-amber-400 text-teal-950 mt-2 rounded-md px-3 py-2 text-center text-sm font-bold"
              >
                Request Fiscal Watch
              </Link>
            </nav>
            <div className="border-teal-700 mt-3 flex justify-end border-t pt-3">
              <ThemeToggle />
            </div>
          </div>
        </details>
      </div>
    </header>
  )
}
