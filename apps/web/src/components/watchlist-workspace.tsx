'use client'

import { Bell, Check, CheckCheck, Eye, Plus, Radar, Trash2 } from 'lucide-react'
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
import { formatDate, formatNaira, humanize } from '@/lib/format'

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
  id: string
  event_key: string
  source_kind: 'fiscal_watch' | 'fiscal_event' | 'publication'
  event_type: string
  severity: string
  state_name: string
  state_slug: string
  state_code: string
  occurred_at: string
  headline: string
  detail: string
  link_path: string
  evidence_ids: string[]
  metrics: Record<string, unknown>
  read_at: string | null
  is_read: boolean
}

interface AlertsResponse {
  year: number
  watchlist_count: number
  alert_count: number
  unread_count: number
  alerts: WatchlistAlert[]
  note: string
}

async function errorMessage(response: Response) {
  const body = (await response.json().catch(() => ({}))) as { detail?: string }
  return body.detail ?? 'Request failed.'
}

function metricText(alert: WatchlistAlert) {
  const change = alert.metrics.change_pct
  if (typeof change === 'number')
    return `${change > 0 ? '+' : ''}${change.toFixed(2)}% MoM`
  const burden = alert.metrics.deduction_burden_pct
  if (typeof burden === 'number')
    return `${burden.toFixed(2)}% deduction burden`
  const values = Object.entries(alert.metrics)
    .filter(
      ([, value]) => value !== null && value !== undefined && value !== '',
    )
    .slice(0, 2)
  if (!values.length) return humanize(alert.event_type)
  return values
    .map(([key, value]) => `${humanize(key)}: ${String(value)}`)
    .join(' · ')
}

function currentNet(alert: WatchlistAlert) {
  const value = alert.metrics.current_net
  return typeof value === 'string' ? value : null
}

function previousNet(alert: WatchlistAlert) {
  const value = alert.metrics.previous_net
  return typeof value === 'string' ? value : null
}

export function WatchlistWorkspace({
  availableStates,
}: {
  availableStates: AvailableState[]
}) {
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([])
  const [alerts, setAlerts] = useState<AlertsResponse | null>(null)
  const [selectedCode, setSelectedCode] = useState(
    availableStates[0]?.state_code ?? '',
  )
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(true)
  const year = new Date().getUTCFullYear()

  const selectableStates = useMemo(() => {
    const watched = new Set(watchlist.map((item) => item.state_code))
    return availableStates.filter((state) => !watched.has(state.state_code))
  }, [availableStates, watchlist])

  const effectiveSelectedCode = selectableStates.some(
    (state) => state.state_code === selectedCode,
  )
    ? selectedCode
    : (selectableStates[0]?.state_code ?? '')

  async function load() {
    const response = await fetch('/api/customer/watchlists', {
      cache: 'no-store',
    })
    if (response.status === 401) {
      window.location.assign('/account/login')
      return
    }
    if (!response.ok) {
      setMessage(await errorMessage(response))
      setLoading(false)
      return
    }

    setWatchlist((await response.json()) as WatchlistItem[])
    const alertsResponse = await fetch(
      `/api/customer/watchlists/alerts?year=${year}`,
      {
        cache: 'no-store',
      },
    )
    if (alertsResponse.ok)
      setAlerts((await alertsResponse.json()) as AlertsResponse)
    else setMessage(await errorMessage(alertsResponse))
    setLoading(false)
  }

  useEffect(() => {
    // Initial Watchlist hydration intentionally updates local UI state.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function addState() {
    if (!effectiveSelectedCode) return
    setMessage('')
    const response = await fetch('/api/customer/watchlists', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ state_code: effectiveSelectedCode }),
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

  async function markRead(id: string) {
    const response = await fetch(`/api/customer/watchlists/alerts/${id}/read`, {
      method: 'POST',
    })
    if (!response.ok) {
      setMessage(await errorMessage(response))
      return
    }
    await load()
  }

  async function markAllRead() {
    const response = await fetch(
      `/api/customer/watchlists/alerts/read-all?year=${year}`,
      {
        method: 'POST',
      },
    )
    if (!response.ok) {
      setMessage(await errorMessage(response))
      return
    }
    await load()
  }

  if (loading)
    return (
      <p className="text-muted-foreground mt-8 text-sm">Loading Watchlist…</p>
    )

  return (
    <div className="mt-9 space-y-8">
      {message ? (
        <p className="border-border bg-muted/30 rounded-lg border p-3 text-sm">
          {message}
        </p>
      ) : null}

      <section className="grid gap-4 lg:grid-cols-[1fr_20rem]">
        <Card>
          <CardHeader>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <CardTitle>Follow a jurisdiction</CardTitle>
                <CardDescription className="mt-1">
                  Save the states you need to monitor. Gaia persists governed
                  allocation signals and evidence lifecycle events for your
                  list.
                </CardDescription>
              </div>
              <StatusPill tone="success">Evidence-backed</StatusPill>
            </div>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col gap-3 sm:flex-row">
              <select
                value={effectiveSelectedCode}
                onChange={(event) => setSelectedCode(event.target.value)}
                disabled={selectableStates.length === 0}
                className="border-input bg-background h-10 min-w-0 flex-1 rounded-md border px-3 text-sm"
                aria-label="Jurisdiction to watch"
              >
                {selectableStates.length === 0 ? (
                  <option value="">
                    All available jurisdictions are watched
                  </option>
                ) : (
                  selectableStates.map((state) => (
                    <option key={state.state_code} value={state.state_code}>
                      {state.state_name} · {state.geopolitical_zone}
                    </option>
                  ))
                )}
              </select>
              <Button onClick={addState} disabled={!effectiveSelectedCode}>
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
              Allocation movements come from Fiscal Watch. Source revisions,
              conflicts and Fiscal State changes come from Gaia's immutable
              event ledger.
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
            <h2 className="mt-2 text-2xl font-semibold">
              {watchlist.length} jurisdictions followed
            </h2>
          </div>
          <Link
            href="/decision-packets"
            className="text-primary text-sm font-medium hover:underline"
          >
            Create Decision Packet →
          </Link>
        </div>

        {watchlist.length === 0 ? (
          <Card className="mt-4 border-dashed">
            <CardHeader>
              <Eye
                className="text-muted-foreground size-5"
                aria-hidden="true"
              />
              <CardTitle className="pt-3">Nothing followed yet</CardTitle>
              <CardDescription>
                Add a state above. Gaia will only materialize alerts from
                governed monitoring or evidence events.
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
                    <Link href={`/decision-packets/${item.state_slug}`}>
                      Decision packet
                    </Link>
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
              {alerts?.unread_count ?? 0} unread · {alerts?.alert_count ?? 0}{' '}
              total in {year}
            </h2>
          </div>
          <div className="flex flex-wrap gap-2">
            {alerts?.unread_count ? (
              <Button size="sm" variant="outline" onClick={markAllRead}>
                <CheckCheck className="size-4" aria-hidden="true" />
                Mark all read
              </Button>
            ) : null}
            <Button asChild size="sm" variant="outline">
              <Link href="/events">Evidence events</Link>
            </Button>
            <Button asChild size="sm" variant="outline">
              <Link href="/fiscal-watch">Fiscal Watch</Link>
            </Button>
          </div>
        </div>

        {!alerts || alerts.alerts.length === 0 ? (
          <Card className="mt-4 border-dashed">
            <CardHeader>
              <Bell
                className="text-muted-foreground size-5"
                aria-hidden="true"
              />
              <CardTitle className="pt-3">No governed alerts yet</CardTitle>
              <CardDescription>
                No deterministic monitoring or evidence-lifecycle event has been
                materialized for this workspace in {year}. Nothing has been
                inferred.
              </CardDescription>
            </CardHeader>
          </Card>
        ) : (
          <div className="mt-4 space-y-3">
            {alerts.alerts.map((alert) => (
              <Card
                key={alert.id}
                className={alert.is_read ? 'opacity-75' : undefined}
              >
                <CardHeader>
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        {!alert.is_read ? (
                          <StatusPill tone="success">Unread</StatusPill>
                        ) : (
                          <StatusPill tone="neutral">Read</StatusPill>
                        )}
                        <StatusPill tone="neutral">
                          {humanize(alert.source_kind)}
                        </StatusPill>
                        <StatusPill tone="neutral">
                          {humanize(alert.severity)}
                        </StatusPill>
                        <span className="text-muted-foreground text-xs">
                          {alert.state_name} ·{' '}
                          {formatDate(alert.occurred_at.slice(0, 10))}
                        </span>
                      </div>
                      <CardTitle className="pt-3 text-lg">
                        {alert.headline}
                      </CardTitle>
                      <CardDescription className="mt-2 max-w-4xl">
                        {alert.detail}
                      </CardDescription>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {!alert.is_read ? (
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => markRead(alert.id)}
                        >
                          <Check className="size-4" aria-hidden="true" />
                          Mark read
                        </Button>
                      ) : null}
                      <Button asChild size="sm" variant="outline">
                        <Link href={alert.link_path}>Inspect evidence</Link>
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <dl className="grid gap-4 text-sm sm:grid-cols-3">
                    {alert.source_kind === 'fiscal_watch' ? (
                      <>
                        <div>
                          <dt className="text-muted-foreground">Current net</dt>
                          <dd className="mt-1 font-mono font-medium">
                            {formatNaira(currentNet(alert))}
                          </dd>
                        </div>
                        <div>
                          <dt className="text-muted-foreground">
                            Previous net
                          </dt>
                          <dd className="mt-1 font-mono font-medium">
                            {formatNaira(previousNet(alert))}
                          </dd>
                        </div>
                      </>
                    ) : (
                      <div className="sm:col-span-2">
                        <dt className="text-muted-foreground">Evidence IDs</dt>
                        <dd className="mt-1 font-mono text-xs break-all">
                          {alert.evidence_ids.length
                            ? alert.evidence_ids.join(' · ')
                            : 'No explicit evidence IDs attached'}
                        </dd>
                      </div>
                    )}
                    <div>
                      <dt className="text-muted-foreground">Recorded event</dt>
                      <dd className="mt-1 font-mono font-medium">
                        {metricText(alert)}
                      </dd>
                    </div>
                  </dl>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {alerts ? (
          <p className="text-muted-foreground mt-4 max-w-4xl text-xs leading-5">
            {alerts.note}
          </p>
        ) : null}
      </section>
    </div>
  )
}
