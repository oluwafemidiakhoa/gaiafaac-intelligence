'use client'

import { ChevronDown, Menu } from 'lucide-react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useEffect, useState } from 'react'

import { ThemeToggle } from '@/components/theme-toggle'
import { Button } from '@/components/ui/button'

interface NavItem {
  href?: string
  label: string
  submenu?: Array<{ href: string; label: string }>
}

const navigation: NavItem[] = [
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

function NavLink({
  href,
  label,
  isActive,
}: {
  href: string
  label: string
  isActive: boolean
}) {
  return (
    <Link
      href={href}
      className={`text-sm font-medium whitespace-nowrap transition-all ${
        isActive
          ? 'border-b-2 border-amber-300 pb-1 text-amber-300'
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
                <span className="font-medium">
                  {publishedData.covered_states}/{publishedData.expected_states}{' '}
                  jurisdictions
                </span>
              </>
            ) : (
              <> · Human review required before publication</>
            )}
          </p>
          <Link
            href="/sources"
            className="shrink-0 font-medium text-amber-200 transition-colors hover:text-amber-100"
          >
            Evidence registry →
          </Link>
        </div>
      </div>

      <div className="mx-auto flex min-h-16 max-w-7xl items-center gap-5 px-5 py-3 lg:px-8">
        <Link
          href="/"
          className="group flex shrink-0 items-center gap-3"
          aria-label="Gaia Fiscal Intelligence home"
        >
          <div className="flex size-10 items-center justify-center rounded-lg bg-amber-400 font-mono text-sm font-bold text-teal-950 transition-colors group-hover:bg-amber-300">
            GF
          </div>
          <span>
            <span className="block font-bold tracking-tight text-white">
              Gaia
            </span>
            <span className="text-[0.75rem] font-medium text-amber-100/80">
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
              if (item.submenu) {
                const submenuActive = isSubmenuActive(item.submenu)
                return (
                  <div key={item.label} className="group relative">
                    <button
                      className={`flex items-center gap-1 text-sm font-medium whitespace-nowrap transition-all ${
                        submenuActive
                          ? 'border-b-2 border-amber-300 pb-1 text-amber-300'
                          : 'text-amber-50/90 hover:text-amber-200'
                      }`}
                    >
                      {item.label}
                      <ChevronDown className="size-3.5" />
                    </button>
                    <div className="absolute top-full left-0 hidden pt-2 group-hover:block">
                      <div className="w-48 overflow-hidden rounded-lg border border-teal-700 bg-teal-900 shadow-lg">
                        {item.submenu.map((subitem) => (
                          <Link
                            key={subitem.href}
                            href={subitem.href}
                            className={`block px-4 py-2.5 text-sm transition-colors ${
                              isActive(subitem.href)
                                ? 'bg-amber-400 font-medium text-teal-950'
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
                  key={item.href!}
                  href={item.href!}
                  label={item.label}
                  isActive={isActive(item.href!)}
                />
              )
            })}
        </nav>

        <div className="hidden items-center gap-2 lg:flex">
          <Button
            asChild
            size="sm"
            className="bg-amber-400 font-medium text-teal-950 hover:bg-amber-300"
          >
            <Link href="/gaia-analyst">Ask Gaia</Link>
          </Button>
          <Button
            asChild
            size="sm"
            className="border border-teal-600 bg-teal-800 text-white hover:bg-teal-700"
          >
            <Link href="/pilot">Request Watch</Link>
          </Button>
          <ThemeToggle />
        </div>

        <details className="relative ml-auto lg:hidden">
          <summary className="flex h-9 cursor-pointer list-none items-center gap-2 rounded-md border border-teal-600 px-3 text-sm font-medium text-white hover:bg-teal-800 [&::-webkit-details-marker]:hidden">
            <Menu className="size-4" aria-hidden="true" />
            Menu
          </summary>
          <div className="absolute right-0 z-50 mt-3 w-72 rounded-lg border border-teal-700 bg-teal-900 p-3 shadow-xl">
            <nav className="grid gap-1" aria-label="Mobile navigation">
              {mounted &&
                navigation.map((item) => {
                  if (item.submenu) {
                    const isOpen = openSubmenu === item.label
                    const submenuActive = isSubmenuActive(item.submenu)
                    return (
                      <div key={item.label}>
                        <button
                          onClick={() =>
                            setOpenSubmenu(isOpen ? null : item.label)
                          }
                          className={`flex w-full items-center justify-between rounded-md px-3 py-2 text-left text-sm font-medium transition-colors ${
                            submenuActive
                              ? 'bg-amber-400 text-teal-950'
                              : 'text-amber-50 hover:bg-teal-800'
                          }`}
                        >
                          {item.label}
                          <ChevronDown
                            className={`size-4 transition-transform ${isOpen ? 'rotate-180' : ''}`}
                          />
                        </button>
                        {isOpen && (
                          <div className="space-y-1 pl-2">
                            {item.submenu.map((subitem) => (
                              <Link
                                key={subitem.href}
                                href={subitem.href}
                                className={`block rounded-md px-3 py-2 text-xs transition-colors ${
                                  isActive(subitem.href)
                                    ? 'bg-amber-400 font-medium text-teal-950'
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
                      key={item.href!}
                      href={item.href!}
                      className={`rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                        isActive(item.href!)
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
                className="rounded-md px-3 py-2 text-sm font-medium text-amber-50 transition-colors hover:bg-teal-800"
              >
                Ask Gaia
              </Link>
              <Link
                href="/pilot"
                className="mt-2 rounded-md bg-amber-400 px-3 py-2 text-center text-sm font-bold text-teal-950"
              >
                Request Fiscal Watch
              </Link>
            </nav>
            <div className="mt-3 flex justify-end border-t border-teal-700 pt-3">
              <ThemeToggle />
            </div>
          </div>
        </details>
      </div>
    </header>
  )
}
