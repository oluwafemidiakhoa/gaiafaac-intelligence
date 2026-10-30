'use client'

import Link from 'next/link'
import { useMemo, useState } from 'react'

import type { PublishedAnalytics } from '@/lib/analytics-api'
import type { PublishedOverview } from '@/lib/published-api'

type WindowSize = '6' | '12' | 'all'

function money(value: string | null) {
  if (value === null) return 'Unavailable'
  const n = Number(value)
  return Number.isFinite(n)
    ? new Intl.NumberFormat('en-NG', {
        style: 'currency',
        currency: 'NGN',
        maximumFractionDigits: 0,
      }).format(n)
    : 'Unavailable'
}

export function FiscalResearchWorkspace({
  overview,
  analytics,
}: {
  overview: PublishedOverview
  analytics: PublishedAnalytics | null
}) {
  const [windowSize, setWindowSize] = useState<WindowSize>('12')
  const [first, setFirst] = useState(overview.allocations[0]?.state_code ?? '')
  const [second, setSecond] = useState(overview.allocations[1]?.state_code ?? '')

  const periods = useMemo(() => {
    const chronological = [...(analytics?.national_trend ?? [])].sort((a, b) =>
      a.revenue_month.localeCompare(b.revenue_month),
    )
    return windowSize === 'all'
      ? chronological
      : chronological.slice(-Number(windowSize))
  }, [analytics, windowSize])

  const maximum = Math.max(
    1,
    ...periods.map((period) => Number(period.total_net) || 0),
  )
  const choices = [...overview.allocations].sort((a, b) =>
    a.state_name.localeCompare(b.state_name),
  )
  const selection = [first, second].map((code) =>
    choices.find((item) => item.state_code === code),
  )

  return (
    <section
      aria-labelledby="fiscal-research-heading"
      className="mb-10 rounded-2xl border border-emerald-900/20 bg-white p-5 text-slate-950 shadow-sm dark:border-white/10 dark:bg-[#08231d] dark:text-white sm:p-7"
    >
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold tracking-widest text-emerald-700 uppercase dark:text-emerald-300">
            Published-data workspace
          </p>
          <h2 id="fiscal-research-heading" className="mt-2 text-2xl font-semibold">
            Explore fiscal evidence
          </h2>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
            National monthly trend and latest jurisdiction comparison. Figures
            are sourced from published records, not forecasts.
          </p>
        </div>
        <Link href="/sources" className="text-sm font-semibold text-emerald-700 underline dark:text-emerald-300">
          Inspect original sources
        </Link>
      </div>

      <div className="mt-8 border-t border-slate-200 pt-6 dark:border-white/10">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h3 className="font-semibold">National net allocations by revenue month</h3>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              Published reporting periods only; units in Nigerian naira
            </p>
          </div>
          <div role="group" aria-label="Trend time window" className="flex gap-2">
            {(['6', '12', 'all'] as const).map((value) => (
              <button
                key={value}
                type="button"
                onClick={() => setWindowSize(value)}
                aria-pressed={windowSize === value}
                className={`rounded-md border px-3 py-2 text-xs font-medium ${windowSize === value ? 'border-emerald-700 bg-emerald-700 text-white' : 'border-slate-300 dark:border-white/20'}`}
              >
                {value === 'all' ? 'All' : `${value} months`}
              </button>
            ))}
          </div>
        </div>
        {periods.length ? (
          <div className="mt-6 overflow-x-auto">
            <div className="flex min-w-[460px] items-end gap-2" style={{ height: 240 }}>
              {periods.map((period) => {
                const amount = Number(period.total_net)
                const safe = Number.isFinite(amount) && amount >= 0 ? amount : 0
                return (
                  <div key={period.revenue_month} className="flex min-w-0 flex-1 flex-col items-center gap-2">
                    <span className="text-[10px] text-slate-500 dark:text-slate-400">
                      {money(period.total_net).replace(/\.00$/, '')}
                    </span>
                    <div
                      title={`${period.reporting_label}: ${money(period.total_net)}`}
                      aria-label={`${period.reporting_label}: ${money(period.total_net)}`}
                      className="w-full rounded-t bg-emerald-600"
                      style={{ height: `${Math.max(4, (safe / maximum) * 165)}px` }}
                    />
                    <span className="text-center text-[10px] text-slate-600 dark:text-slate-300">
                      {period.revenue_month.slice(0, 7)}
                    </span>
                  </div>
                )
              })}
            </div>
          </div>
        ) : (
          <p className="mt-6 rounded-lg border border-dashed p-5 text-sm">
            No published monthly trend is available. Gaia does not fill missing
            months with fabricated values.
          </p>
        )}
      </div>

      <div className="mt-8 border-t border-slate-200 pt-6 dark:border-white/10">
        <h3 className="font-semibold">Compare latest published jurisdictions</h3>
        <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
          {overview.period.reporting_label} · Latest ledger only, not a historical state trend
        </p>
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          {[first, second].map((current, i) => (
            <label key={i} className="flex flex-col gap-2 text-sm">
              {i === 0 ? 'Jurisdiction A' : 'Jurisdiction B'}
              <select
                value={current}
                onChange={(event) =>
                  i === 0 ? setFirst(event.target.value) : setSecond(event.target.value)
                }
                className="rounded-lg border border-slate-300 bg-white p-3 text-slate-950"
              >
                {choices.map((item) => (
                  <option key={item.state_code} value={item.state_code}>
                    {item.state_name}
                  </option>
                ))}
              </select>
            </label>
          ))}
        </div>
        {first === second ? (
          <p className="mt-3 text-sm text-amber-700 dark:text-amber-300">
            Select two different jurisdictions to compare.
          </p>
        ) : null}
        <div className="mt-5 grid gap-3 sm:grid-cols-2">
          {selection.map((item, i) => (
            <div key={i} className="rounded-xl border border-slate-200 p-4 dark:border-white/15">
              <p className="font-semibold">{item?.state_name ?? 'Unavailable'}</p>
              <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                Net allocation
              </p>
              <p className="mt-2 text-xl font-semibold">
                {money(item?.net_allocation ?? null)}
              </p>
              {item ? (
                <Link href={`/states/${item.state_slug}`} className="mt-3 inline-block text-sm text-emerald-700 underline dark:text-emerald-300">
                  Open jurisdiction evidence
                </Link>
              ) : null}
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
