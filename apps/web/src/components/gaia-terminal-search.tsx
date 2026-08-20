'use client'

import {
  Activity,
  ArrowRight,
  Bot,
  Download,
  FileCheck2,
  FileText,
  FlaskConical,
  GitCompareArrows,
  MapPinned,
  Radar,
  Search,
  ShieldCheck,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import Link from 'next/link'
import { useEffect, useMemo, useRef, useState } from 'react'

import type { PublishedOverview } from '@/lib/published-api'

type Jurisdiction = PublishedOverview['allocations'][number]

type TerminalCommand = {
  label: string
  description: string
  href: string
  category: string
  keywords: string
  icon: LucideIcon
}

const commands: TerminalCommand[] = [
  {
    label: 'Gaia Analyst',
    description: 'Ask evidence-grounded questions over published FAAC and IGR records.',
    href: '/gaia-analyst',
    category: 'Intelligence',
    keywords: 'ask ai analyst question faac igr intelligence',
    icon: Bot,
  },
  {
    label: 'Fiscal Watch',
    description: 'Inspect deterministic monitoring signals over governed fiscal evidence.',
    href: '/fiscal-watch',
    category: 'Monitoring',
    keywords: 'watch monitor alert movement anomaly signal change',
    icon: Radar,
  },
  {
    label: 'National Reconciliation',
    description: 'Compare jurisdiction-ledger totals with independently governed national evidence.',
    href: '/national-reconciliation',
    category: 'Evidence',
    keywords: 'national reconcile reconciliation variance official total evidence',
    icon: ShieldCheck,
  },
  {
    label: 'Evidence Registry',
    description: 'Trace published periods to source documents, URLs and SHA-256 fingerprints.',
    href: '/sources',
    category: 'Evidence',
    keywords: 'source registry document sha hash provenance evidence proof',
    icon: FileCheck2,
  },
  {
    label: 'Compare Jurisdictions',
    description: 'Compare two to six jurisdictions without filling missing values.',
    href: '/compare',
    category: 'Research',
    keywords: 'compare comparison states jurisdictions benchmark ranking',
    icon: GitCompareArrows,
  },
  {
    label: 'Decision Packets',
    description: 'Create print-ready state evidence dossiers for institutional review.',
    href: '/decision-packets',
    category: 'Institutional',
    keywords: 'decision packet report dossier investment committee memo pdf',
    icon: FileText,
  },
  {
    label: 'Fiscal Design Lab',
    description: 'Run clearly labelled hypothetical resilience scenarios over governed evidence.',
    href: '/fiscal-design',
    category: 'Simulation',
    keywords: 'scenario simulation stress test design shock resilience model',
    icon: FlaskConical,
  },
  {
    label: 'Fiscal Events',
    description: 'Follow immutable evidence lifecycle and fiscal-state events.',
    href: '/events',
    category: 'Monitoring',
    keywords: 'events timeline revision change lifecycle history',
    icon: Activity,
  },
  {
    label: 'Fiscal Pulse',
    description: 'Explore descriptive momentum, volatility, deduction burden and retention signals.',
    href: '/fiscal-pulse',
    category: 'Intelligence',
    keywords: 'pulse momentum volatility deduction retention ranking signal',
    icon: Activity,
  },
  {
    label: 'Verify Evidence Manifest',
    description: 'Verify a Fiscal Design evidence manifest locally against its integrity contract.',
    href: '/fiscal-design/verify',
    category: 'Verification',
    keywords: 'verify manifest hash sha integrity proof evidence',
    icon: ShieldCheck,
  },
  {
    label: 'Export Governed Data',
    description: 'Open entitled exports for reproducible downstream analysis.',
    href: '/account#exports',
    category: 'Data',
    keywords: 'download export csv xlsx json api data',
    icon: Download,
  },
]

function compactNaira(value: string | null) {
  if (!value) return 'Unavailable'
  const amount = Number(value)
  if (!Number.isFinite(amount)) return 'Unavailable'
  if (Math.abs(amount) >= 1_000_000_000_000)
    return `₦${(amount / 1_000_000_000_000).toFixed(2)}T`
  if (Math.abs(amount) >= 1_000_000_000)
    return `₦${(amount / 1_000_000_000).toFixed(2)}B`
  if (Math.abs(amount) >= 1_000_000)
    return `₦${(amount / 1_000_000).toFixed(1)}M`
  return `₦${amount.toLocaleString('en-NG', { maximumFractionDigits: 2 })}`
}

function tokens(value: string) {
  return value
    .trim()
    .toLocaleLowerCase('en-NG')
    .split(/\s+/)
    .filter(Boolean)
}

function matches(haystack: string, query: string[]) {
  const normalized = haystack.toLocaleLowerCase('en-NG')
  return query.every((token) => normalized.includes(token))
}

export function GaiaTerminalSearch({
  jurisdictions,
  periodLabel,
}: {
  jurisdictions: Jurisdiction[]
  periodLabel: string | null
}) {
  const [query, setQuery] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)
  const queryTokens = useMemo(() => tokens(query), [query])

  useEffect(() => {
    function handleShortcut(event: KeyboardEvent) {
      const target = event.target as HTMLElement | null
      const editing =
        target?.tagName === 'INPUT' ||
        target?.tagName === 'TEXTAREA' ||
        target?.isContentEditable

      if (event.key === '/' && !editing && !event.metaKey && !event.ctrlKey) {
        event.preventDefault()
        inputRef.current?.focus()
      }
      if (event.key === 'Escape' && document.activeElement === inputRef.current) {
        setQuery('')
        inputRef.current?.blur()
      }
    }

    window.addEventListener('keydown', handleShortcut)
    return () => window.removeEventListener('keydown', handleShortcut)
  }, [])

  const commandMatches = useMemo(() => {
    if (queryTokens.length === 0) return commands
    return commands.filter((command) =>
      matches(
        `${command.label} ${command.description} ${command.category} ${command.keywords}`,
        queryTokens,
      ),
    )
  }, [queryTokens])

  const jurisdictionMatches = useMemo(() => {
    const ordered = [...jurisdictions].sort(
      (left, right) =>
        Number(right.net_allocation ?? 0) - Number(left.net_allocation ?? 0),
    )
    if (queryTokens.length === 0) return ordered.slice(0, 8)
    return ordered.filter((item) =>
      matches(
        `${item.state_name} ${item.state_code} ${item.state_slug} ${item.geopolitical_zone}`,
        queryTokens,
      ),
    )
  }, [jurisdictions, queryTokens])

  const hasResults = commandMatches.length > 0 || jurisdictionMatches.length > 0

  return (
    <div>
      <div className="border-border bg-background relative rounded-2xl border p-2 shadow-sm">
        <Search
          className="text-muted-foreground pointer-events-none absolute top-1/2 left-5 size-5 -translate-y-1/2"
          aria-hidden="true"
        />
        <input
          ref={inputRef}
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          className="placeholder:text-muted-foreground h-14 w-full rounded-xl bg-transparent pr-20 pl-12 text-base outline-none"
          placeholder="Search Lagos, FCT, South West, evidence, reconciliation…"
          aria-label="Search Gaia Terminal"
          autoComplete="off"
        />
        <kbd className="border-border bg-muted text-muted-foreground pointer-events-none absolute top-1/2 right-4 -translate-y-1/2 rounded border px-2 py-1 font-mono text-[0.68rem]">
          /
        </kbd>
      </div>

      <div className="text-muted-foreground mt-3 flex flex-wrap items-center justify-between gap-2 text-xs">
        <span>
          Search the latest governed jurisdiction ledger and every major research workflow.
        </span>
        {periodLabel ? <span className="font-mono">{periodLabel}</span> : null}
      </div>

      {!hasResults ? (
        <div className="border-border bg-muted/20 mt-7 rounded-xl border border-dashed p-7">
          <p className="font-medium">No governed result found</p>
          <p className="text-muted-foreground mt-2 max-w-2xl text-sm leading-6">
            Gaia Terminal does not invent a jurisdiction, workflow or fiscal value to satisfy a search. Try a state name, code, geopolitical zone, evidence, reconciliation, Analyst or Watch.
          </p>
        </div>
      ) : null}

      {jurisdictionMatches.length > 0 ? (
        <section className="mt-8" aria-labelledby="terminal-jurisdictions">
          <div className="flex flex-wrap items-end justify-between gap-3">
            <div>
              <p className="text-primary font-mono text-xs font-semibold tracking-[0.16em] uppercase">
                Governed jurisdictions
              </p>
              <h2 id="terminal-jurisdictions" className="mt-2 text-xl font-semibold">
                {queryTokens.length === 0 ? 'Latest ledger leaders' : 'Jurisdiction matches'}
              </h2>
            </div>
            <Link href="/states" className="text-primary text-sm font-medium hover:underline">
              All jurisdictions →
            </Link>
          </div>

          <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            {jurisdictionMatches.map((item) => (
              <article
                key={item.state_code}
                className="border-border bg-card rounded-xl border p-4 shadow-sm"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="font-semibold">{item.state_name}</p>
                    <p className="text-muted-foreground mt-1 text-xs">
                      {item.state_code} · {item.geopolitical_zone}
                    </p>
                  </div>
                  <MapPinned className="text-primary size-4" aria-hidden="true" />
                </div>
                <p className="mt-5 font-mono text-xl font-semibold">
                  {compactNaira(item.net_allocation)}
                </p>
                <p className="text-muted-foreground mt-1 text-xs">Latest published net allocation</p>
                <div className="mt-5 flex flex-wrap gap-2 text-xs font-medium">
                  <Link
                    href={`/states/${item.state_slug}`}
                    className="bg-primary text-primary-foreground inline-flex items-center gap-1.5 rounded-md px-3 py-2"
                  >
                    Open state <ArrowRight className="size-3" aria-hidden="true" />
                  </Link>
                  <Link
                    href={`/jurisdictions/${item.state_code}/local-governments`}
                    className="border-border hover:bg-muted inline-flex items-center rounded-md border px-3 py-2"
                  >
                    LGAs
                  </Link>
                </div>
              </article>
            ))}
          </div>
        </section>
      ) : null}

      {commandMatches.length > 0 ? (
        <section className="mt-10" aria-labelledby="terminal-commands">
          <p className="text-primary font-mono text-xs font-semibold tracking-[0.16em] uppercase">
            Command surface
          </p>
          <h2 id="terminal-commands" className="mt-2 text-xl font-semibold">
            Research and institutional workflows
          </h2>
          <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {commandMatches.map((command) => {
              const Icon = command.icon
              return (
                <Link
                  key={command.href}
                  href={command.href}
                  className="border-border bg-card hover:bg-muted/40 group rounded-xl border p-4 transition-colors"
                >
                  <div className="flex items-start gap-3">
                    <span className="bg-primary/10 text-primary flex size-9 shrink-0 items-center justify-center rounded-lg">
                      <Icon className="size-4" aria-hidden="true" />
                    </span>
                    <div className="min-w-0">
                      <div className="flex items-center justify-between gap-3">
                        <p className="font-semibold">{command.label}</p>
                        <ArrowRight
                          className="text-muted-foreground group-hover:text-primary size-4 shrink-0 transition-colors"
                          aria-hidden="true"
                        />
                      </div>
                      <p className="text-muted-foreground mt-2 text-sm leading-6">
                        {command.description}
                      </p>
                      <p className="text-muted-foreground mt-3 font-mono text-[0.65rem] tracking-wide uppercase">
                        {command.category}
                      </p>
                    </div>
                  </div>
                </Link>
              )
            })}
          </div>
        </section>
      ) : null}
    </div>
  )
}
