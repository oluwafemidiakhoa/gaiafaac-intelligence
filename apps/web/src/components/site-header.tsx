import { CircleDollarSign, Menu, ShieldCheck, Sparkles } from 'lucide-react'
import Link from 'next/link'

import { ThemeToggle } from '@/components/theme-toggle'
import { Button } from '@/components/ui/button'
import { formatDate } from '@/lib/format'
import { getPublishedOverview } from '@/lib/published-api'

const productNavigation = [
  { href: '/terminal', label: 'Terminal' },
  { href: '/decision-rooms', label: 'Rooms' },
  { href: '/live', label: 'Live' },
  { href: '/fiscal-pulse', label: 'Intelligence' },
  { href: '/sources', label: 'Evidence' },
  { href: '/review', label: 'Review' },
  { href: '/institutional', label: 'Institutions' },
]

const commercialNavigation = [
  { href: '/pricing', label: 'Pricing' },
  { href: '/account', label: 'Account' },
]

export async function SiteHeader() {
  const overview = await getPublishedOverview()
  const data = overview.data

  return (
    <header className="sticky top-0 z-50 border-b border-white/10 bg-[#041915]/95 text-white shadow-[0_10px_40px_rgba(0,0,0,0.12)] backdrop-blur-2xl">
      <div className="border-b border-white/8 bg-black/10">
        <div className="gaia-shell flex min-h-8 items-center justify-between gap-4 text-[0.7rem]">
          <div className="flex min-w-0 items-center gap-3 text-emerald-100/70">
            <span className="inline-flex items-center gap-1.5 font-semibold text-emerald-100">
              <span className="size-1.5 rounded-full bg-emerald-300 shadow-[0_0_12px_rgba(110,231,183,0.9)]" />
              CONTROL PLANE
            </span>
            <span className="hidden text-white/20 sm:inline">/</span>
            <p className="truncate">
              {data ? (
                <>
                  Verified {formatDate(data.period.revenue_month)} ·{' '}
                  {data.covered_states}/{data.expected_states} jurisdictions
                </>
              ) : (
                <>Publication remains review-gated</>
              )}
            </p>
          </div>

          <div className="flex shrink-0 items-center gap-4">
            {commercialNavigation.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="hidden font-medium text-white/55 transition-colors hover:text-white md:inline"
              >
                {item.label}
              </Link>
            ))}
            <Link
              href="/sources"
              className="inline-flex items-center gap-1.5 font-semibold text-amber-200 transition-colors hover:text-amber-100"
            >
              <ShieldCheck className="size-3.5" aria-hidden="true" />
              Verify evidence
            </Link>
          </div>
        </div>
      </div>

      <div className="gaia-shell flex min-h-[72px] items-center gap-3 py-3">
        <Link
          href="/"
          className="group flex shrink-0 items-center gap-3"
          aria-label="Gaia Fiscal Intelligence home"
        >
          <div className="relative flex size-10 items-center justify-center overflow-hidden rounded-xl border border-amber-200/20 bg-amber-300 font-mono text-xs font-black text-teal-950 shadow-[0_8px_30px_rgba(251,191,36,0.15)] transition-transform group-hover:-translate-y-0.5">
            GF
          </div>
          <span className="hidden 2xl:block">
            <span className="block text-sm font-bold tracking-tight text-white">
              Gaia Fiscal Intelligence
            </span>
            <span className="mt-0.5 block font-mono text-[0.58rem] tracking-[0.16em] text-emerald-200/55 uppercase">
              Public finance operating system
            </span>
          </span>
        </Link>

        <nav
          className="ml-auto hidden items-center gap-0.5 lg:flex"
          aria-label="Primary product navigation"
        >
          {productNavigation.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="rounded-lg px-2.5 py-2 text-sm font-medium whitespace-nowrap text-white/72 transition hover:bg-white/[0.07] hover:text-white"
            >
              {item.label}
            </Link>
          ))}
        </nav>

        <div className="hidden items-center gap-2 lg:flex">
          <Button
            asChild
            size="sm"
            variant="outline"
            className="border-white/12 bg-white/[0.04] text-white hover:bg-white/[0.09] hover:text-white"
          >
            <Link href="/pilot">
              <CircleDollarSign className="size-4" />
              Request Watch
            </Link>
          </Button>
          <Button
            asChild
            size="sm"
            className="bg-amber-300 font-bold text-teal-950 shadow-[0_8px_28px_rgba(251,191,36,0.14)] hover:bg-amber-200"
          >
            <Link href="/gaia-analyst">
              <Sparkles className="size-4" />
              Ask Gaia
            </Link>
          </Button>
          <ThemeToggle />
        </div>

        <details className="relative ml-auto lg:hidden">
          <summary className="flex h-10 cursor-pointer list-none items-center gap-2 rounded-xl border border-white/12 bg-white/[0.05] px-3 text-sm font-medium text-white hover:bg-white/10 [&::-webkit-details-marker]:hidden">
            <Menu className="size-4" aria-hidden="true" />
            Menu
          </summary>
          <div className="absolute right-0 z-50 mt-3 w-80 overflow-hidden rounded-2xl border border-white/10 bg-[#08211d] p-3 shadow-2xl">
            <p className="px-3 pt-2 pb-1 font-mono text-[0.6rem] font-semibold tracking-[0.18em] text-emerald-200/50 uppercase">
              Product
            </p>
            <nav className="grid gap-1" aria-label="Mobile product navigation">
              {productNavigation.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className="rounded-lg px-3 py-2.5 text-sm font-medium text-white/80 transition-colors hover:bg-white/[0.07] hover:text-white"
                >
                  {item.label === 'Rooms' ? 'Decision Rooms' : item.label}
                </Link>
              ))}
            </nav>

            <div className="my-3 border-t border-white/10" />
            <p className="px-3 pb-1 font-mono text-[0.6rem] font-semibold tracking-[0.18em] text-amber-200/55 uppercase">
              Commercial
            </p>
            <div className="grid grid-cols-2 gap-1">
              {commercialNavigation.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className="rounded-lg px-3 py-2.5 text-sm font-medium text-white/75 transition-colors hover:bg-white/[0.07] hover:text-white"
                >
                  {item.label}
                </Link>
              ))}
            </div>

            <div className="mt-3 grid gap-2 border-t border-white/10 pt-3">
              <Link
                href="/gaia-analyst"
                className="rounded-lg bg-amber-300 px-3 py-2.5 text-center text-sm font-bold text-teal-950"
              >
                Ask Gaia
              </Link>
              <Link
                href="/pilot"
                className="rounded-lg border border-white/10 bg-white/[0.04] px-3 py-2.5 text-center text-sm font-semibold text-white"
              >
                Request Fiscal Watch
              </Link>
            </div>
            <div className="mt-3 flex justify-end border-t border-white/10 pt-3">
              <ThemeToggle />
            </div>
          </div>
        </details>
      </div>
    </header>
  )
}
