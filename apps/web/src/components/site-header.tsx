'use client'

import { ChevronDown, Menu } from 'lucide-react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useEffect, useState } from 'react'

import { ThemeToggle } from '@/components/theme-toggle'
import { Button } from '@/components/ui/button'

const navigation = [
  { href: '/terminal', label: 'Terminal' },
  { href: '/institutional', label: 'Institutions' },
  { href: '/live', label: 'Live data' },
  {
    label: 'Intelligence',
    submenu: [
      { href: '/overview', label: 'National overview' },
      { href: '/insights', label: 'Insights' },
      { href: '/fiscal-pulse', label: 'Fiscal Pulse' },
    ],
  },
  { href: '/sources', label: 'Evidence' },
  { href: '/review', label: 'Review' },
]

function NavLink({ href, label, isActive }: { href: string; label: string; isActive: boolean }) {
  return (
    <Link
      href={href}
      className={`text-sm font-medium whitespace-nowrap transition-all ${
        isActive
          ? 'text-amber-300 border-b-2 border-amber-300 pb-1'
          : 'text-amber-50/90 hover:text-amber-200'
      }`}
    >
      {label}
    </Link>
  )
}

export function SiteHeader({ publishedData }: { publishedData?: any }) {
  const pathname = usePathname()
  const [mounted, setMounted] = useState(false)
  const [openSubmenu, setOpenSubmenu] = useState<string | null>(null)

  useEffect(() => {
    setMounted(true)
  }, [])

  const isActive = (href: string) => {
    if (href === '/') return pathname === '/'
    return pathname.startsWith(href)
  }

  const isSubmenuActive = (submenu: any[]) => {
    return submenu.some((item) => isActive(item.href))
  }

  return (
    <header className="sticky top-0 z-50 border-b border-teal-900/20 bg-gradient-to-r from-teal-950 to-teal-900 text-white">
      <div className="border-b border-teal-900/50 bg-teal-900/40">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-5 py-2 text-xs lg:px-8">
          <p className="min-w-0 truncate text-amber-100">
            <span className="font-semibold text-amber-50">
              Governed public evidence
            </span>
            {publishedData ? (
              <>
                {' '}
                · Latest verified {publishedData.period_label} ·{' '}
                <span className="font-medium">{publishedData.covered_states}/{publishedData.expected_states} jurisdictions</span>
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
          {mounted &&
            navigation.map((item) => {
              if ('submenu' in item) {
                const isActive = isSubmenuActive(item.submenu)
                return (
                  <div key={item.label} className="relative group">
                    <button
                      className={`text-sm font-medium whitespace-nowrap transition-all flex items-center gap-1 ${
                        isActive
                          ? 'text-amber-300 border-b-2 border-amber-300 pb-1'
                          : 'text-amber-50/90 hover:text-amber-200'
                      }`}
                    >
                      {item.label}
                      <ChevronDown className="size-3.5" />
                    </button>
                    <div className="absolute left-0 top-full hidden group-hover:block pt-2">
                      <div className="bg-teal-900 border border-teal-700 rounded-lg shadow-lg overflow-hidden w-48">
                        {item.submenu.map((subitem) => (
                          <Link
                            key={subitem.href}
                            href={subitem.href}
                            className={`block px-4 py-2.5 text-sm transition-colors ${
                              isActive(subitem.href)
                                ? 'bg-amber-400 text-teal-950 font-medium'
                                : 'text-amber-50/90 hover:bg-teal-800 hover:text-amber-200'
                            }`}
                          >
                            {subitem.label}
                          </Link>
                        ))}
                      </div>
                    </div>
                  </div>
                )
              }
              return (
                <NavLink
                  key={item.href}
                  href={item.href}
                  label={item.label}
                  isActive={isActive(item.href)}
                />
              )
            })}
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
              {mounted &&
                navigation.map((item) => {
                  if ('submenu' in item) {
                    const isOpen = openSubmenu === item.label
                    const isActive = isSubmenuActive(item.submenu)
                    return (
                      <div key={item.label}>
                        <button
                          onClick={() => setOpenSubmenu(isOpen ? null : item.label)}
                          className={`w-full text-left rounded-md px-3 py-2 text-sm font-medium transition-colors flex items-center justify-between ${
                            isActive
                              ? 'bg-amber-400 text-teal-950'
                              : 'text-amber-50 hover:bg-teal-800'
                          }`}
                        >
                          {item.label}
                          <ChevronDown className={`size-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
                        </button>
                        {isOpen && (
                          <div className="pl-2 space-y-1">
                            {item.submenu.map((subitem) => (
                              <Link
                                key={subitem.href}
                                href={subitem.href}
                                className={`block rounded-md px-3 py-2 text-xs transition-colors ${
                                  isActive(subitem.href)
                                    ? 'bg-amber-400 text-teal-950 font-medium'
                                    : 'text-amber-50 hover:bg-teal-800'
                                }`}
                              >
                                {subitem.label}
                              </Link>
                            ))}
                          </div>
                        )}
                      </div>
                    )
                  }
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      className={`rounded-md px-3 py-2 text-sm transition-colors font-medium ${
                        isActive(item.href)
                          ? 'bg-amber-400 text-teal-950'
                          : 'text-amber-50 hover:bg-teal-800'
                      }`}
                    >
                      {item.label}
                    </Link>
                  )
                })}
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
