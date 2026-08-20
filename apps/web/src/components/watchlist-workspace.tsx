'use client'

import { Bell, Eye, Plus, Radar, Trash2 } from 'lucide-react'
import Link from 'next/link'
import { useEffect, useMemo, useState } from 'react'

import { StatusPill } from '@/components/status-pill'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { formatDate, formatNaira } from '@/lib/format'

interface AvailableState {
  state_name: string
  state_code: string
  state_slug: string
  geopolitical_zone: string
}

interface WatchlistItem extends AvailableState {
  id: string
  created_at: string
}

interface WatchlistAlert {
  event_key: string
  kind: 'negative_net' | 'large_monthly_move' | 'high_deduction_burden'
  severity: 'watch' | 'elevated'
  state_name: string
  state_slug: string
  state_code: string
  revenue_month: string
  headline: string
  detail: string
  current_net: string | null
  previous_net: string | null
  change_pct: number | null
  deduction_burden_pct: number | null
  proof_path: string
}

interface AlertsResponse {
  year: number
  watchlist_count: number
  alert_count: number
  alerts: WatchlistAlert[]
  note: string
}

async function errorMessage(response: Response) {
  const body = (await response.json().catch(() => ({}))) as { detail?: string }
  return body.detail ?? 'Request failed.'
}

export function WatchlistWorkspace({
  availableStates,
}: {
  availableStates: AvailableState[]
}) {
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([])
  const [alerts, setAlerts] = useState<AlertsResponse | null>(null)
  const [selectedCode, setSelectedCode] = useState(availableStates[0]?.state_code ?? '')
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(true)
  const year = new Date().getUTCFullYear()

  const selectableStates = useMemo(() => {
    const watched = new Set(watchlist.map((item) => item.state_code))
    return availableStates.filter((state) => !watched.has(state.state_code))
  }, [availableStates, watchlist])

  async function load() {
    const response = await fetch('/api/customer/watchlists', { cache: 'no-store' })
    if (response.status === 401) {
      window.location.assign('/account/login')
      return
    }
    if (!response.ok) {
      setMessage(await errorMessage(response))
      setLoading(false)
      return
    }

    const nextWatchlist = (await response.json()) as WatchlistItem[]
    setWatchlist(nextWatchlist)

    const alertsResponse = await fetch(`/api/customer/watchlists/alerts?year=${year}`, {
      cache: 'no-store',
    })
    if (alertsResponse.ok) {
      setAlerts((await alertsResponse.json()) as AlertsResponse)
    } else {
      setMessage(await errorMessage(alertsResponse))
    }
    setLoading(false)
  }

  useEffect(() => {
    void load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    if (!selectableStates.some((state) => state.state_code === selectedCode)) {
      setSelectedCode(selectableStates[0]?.state_code ?? '')
    }
  }, [selectableStates, selectedCode])

  async function addState() {
    if (!selectedCode) return
    setMessage('')
    const response = await fetch('/api/customer/watchlists', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ state_code: selectedCode }),
    })
    if (!response.ok) {
      setMessage(await errorMessage(response))
      return
    }
    await load()
  }

  async function removeState(id: string) {
    setMessage('')
    const response = await fetch(`/api/customer/watchlists/${id}`, {
      method: 'DELETE',
    })
    if (!response.ok) {
      setMessage(await errorMessage(response))
      return
    }
    await load()
  }

  if (loading) {
    return <p className="text-muted-foreground mt-8 text-sm">Loading Watchlist…</p>
  }

  return (
    <div className="mt-9 space-y-8">
      {message ? (
        <p className="border-border bg-muted/30 rounded-lg border p-3 text-sm">{message}</p>
      ) : null}

      <section className="grid gap-4 lg:grid-cols-[1fr_20rem]">
        <Card>
          <CardHeader>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <CardTitle>Follow a jurisdiction</CardTitle>
                <CardDescription className="mt-1">
                  Save the states you need to monitor. Gaia filters governed Fiscal Watch signals to your list.
                </CardDescription>
              </div>
              <StatusPill tone="success">Evidence-backed</StatusPill>
            </div>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col gap-3 sm:flex-row">
              <select
                value={selectedCode}
                onChange={(event) => setSelectedCode(event.target.value)}
                disabled={selectableStates.length === 0}
                className="border-input bg-background h-10 min-w-0 flex-1 rounded-md border px-3 text-sm"
                aria-label="Jurisdiction to watch"
              >
                {selectableStates.length === 0 ? (
                  <option value="">All available jurisdictions are watched</option>
                ) : (
                  selectableStates.map((state) => (
                    <option key={state.state_code} value={state.state_code}>
                      {state.state_name} · {state.geopolitical_zone}
                    </option>
                  ))
                )}
              </select>
              <Button onClick={addState} disabled={!selectedCode}>
                <Plus className="size-4" aria-hidden="true" />
                Watch state
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-muted/25">
          <CardHeader>
            <Radar className="text-primary size-5" aria-hidden="true" />
            <CardTitle className="pt-3">Monitoring contract</CardTitle>
            <CardDescription>
              Current alerts cover large monthly moves, negative net allocations and high deduction burden only.
            </CardDescription>
          </CardHeader>
        </Card>
      </section>

      <section>
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <p className="text-primary font-mono text-xs font-semibold tracking-[0.16em] uppercase">
              My Watchlist
            </p>
            <h2 className="mt-2 text-2xl font-semibold">{watchlist.length} jurisdictions followed</h2>
          </div>
          <Link href="/decision-packets" className="text-primary text-sm font-medium hover:underline">
            Create Decision Packet →
          </Link>
        </div>

        {watchlist.length === 0 ? (
          <Card className="mt-4 border-dashed">
            <CardHeader>
              <Eye className="text-muted-foreground size-5" aria-hidden="true" />
              <CardTitle className="pt-3">Nothing followed yet</CardTitle>
              <CardDescription>
                Add a state above. Gaia will not generate an alert until a governed Fiscal Watch signal exists for that state.
              </CardDescription>
            </CardHeader>
          </Card>
        ) : (
          <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {watchlist.map((item) => (
              <Card key={item.id}>
                <CardHeader>
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <CardTitle>{item.state_name}</CardTitle>
                      <CardDescription className="mt-1">
                        {item.state_code} · {item.geopolitical_zone}
                      </CardDescription>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => removeState(item.id)}
                      aria-label={`Stop watching ${item.state_name}`}
                    >
                      <Trash2 className="size-4" aria-hidden="true" />
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="flex flex-wrap gap-2">
                  <Button asChild size="sm" variant="outline">
                    <Link href={`/states/${item.state_slug}`}>Open state</Link>
                  </Button>
                  <Button asChild size="sm" variant="outline">
                    <Link href={`/decision-packets/${item.state_slug}`}>Decision packet</Link>
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </section>

      <section>
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <p className="text-primary font-mono text-xs font-semibold tracking-[0.16em] uppercase">
              Alert inbox
            </p>
            <h2 className="mt-2 text-2xl font-semibold">
              {alerts?.alert_count ?? 0} governed signals in {year}
            </h2>
          </div>
          <Link href="/fiscal-watch" className="text-primary text-sm font-medium hover:underline">
            Open full Fiscal Watch →
          </Link>
        </div>

        {!alerts || alerts.alerts.length === 0 ? (
          <Card className="mt-4 border-dashed">
            <CardHeader>
              <Bell className="text-muted-foreground size-5" aria-hidden="true" />
              <CardTitle className="pt-3">No active watchlist signals</CardTitle>
              <CardDescription>
                No deterministic Fiscal Watch event currently matches your saved jurisdictions for {year}. No alert has been inferred.
              </CardDescription>
            </CardHeader>
          </Card>
        ) : (
          <div className="mt-4 space-y-3">
            {alerts.alerts.map((alert) => (
              <Card key={alert.event_key}>
                <CardHeader>
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <StatusPill tone={alert.severity === 'elevated' ? 'demo' : 'neutral'}>
                          {alert.severity}
                        </StatusPill>
                        <span className="text-muted-foreground text-xs">
                          {alert.state_name} · {formatDate(alert.revenue_month)}
                        </span>
                      </div>
                      <CardTitle className="pt-3 text-lg">{alert.headline}</CardTitle>
                      <CardDescription className="mt-2 max-w-4xl">{alert.detail}</CardDescription>
                    </div>
                    <Button asChild size="sm" variant="outline">
                      <Link href={alert.proof_path}>Inspect proof</Link>
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  <dl className="grid gap-4 text-sm sm:grid-cols-3">
                    <div>
                      <dt className="text-muted-foreground">Current net</dt>
                      <dd className="mt-1 font-mono font-medium">{formatNaira(alert.current_net)}</dd>
                    </div>
                    <div>
                      <dt className="text-muted-foreground">Previous net</dt>
                      <dd className="mt-1 font-mono font-medium">{formatNaira(alert.previous_net)}</dd>
                    </div>
                    <div>
                      <dt className="text-muted-foreground">Observed signal</dt>
                      <dd className="mt-1 font-mono font-medium">
                        {alert.change_pct !== null
                          ? `${alert.change_pct > 0 ? '+' : ''}${alert.change_pct.toFixed(2)}% MoM`
                          : alert.deduction_burden_pct !== null
                            ? `${alert.deduction_burden_pct.toFixed(2)}% deduction burden`
                            : alert.kind.replaceAll('_', ' ')}
                      </dd>
                    </div>
                  </dl>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {alerts ? (
          <p className="text-muted-foreground mt-4 max-w-4xl text-xs leading-5">{alerts.note}</p>
        ) : null}
      </section>
    </div>
  )
}
