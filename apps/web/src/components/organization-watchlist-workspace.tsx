'use client'

import {
  Bell,
  Check,
  CheckCheck,
  Plus,
  ShieldCheck,
  Trash2,
  Users,
} from 'lucide-react'
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
import { formatDate, humanize } from '@/lib/format'

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

interface AccountProfile {
  organization_name: string
  membership_role: 'owner' | 'admin' | 'member'
  plan_code: string
  max_users: number
}

async function errorMessage(response: Response) {
  const body = (await response.json().catch(() => ({}))) as { detail?: string }
  return body.detail ?? 'Request failed.'
}

function metricText(alert: WatchlistAlert) {
  const change = alert.metrics.change_pct
  if (typeof change === 'number')
    return `${change > 0 ? '+' : ''}${change.toFixed(2)}% MoM`
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

export function OrganizationWatchlistWorkspace({
  availableStates,
}: {
  availableStates: AvailableState[]
}) {
  const [profile, setProfile] = useState<AccountProfile | null>(null)
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([])
  const [alerts, setAlerts] = useState<AlertsResponse | null>(null)
  const [selectedCode, setSelectedCode] = useState(
    availableStates[0]?.state_code ?? '',
  )
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(true)
  const year = new Date().getUTCFullYear()

  const eligible = (profile?.max_users ?? 0) > 1
  const canAdmin =
    profile?.membership_role === 'owner' || profile?.membership_role === 'admin'

  const selectableStates = useMemo(() => {
    const watched = new Set(watchlist.map((item) => item.state_code))
    return availableStates.filter((state) => !watched.has(state.state_code))
  }, [availableStates, watchlist])

  const effectiveSelectedCode = selectableStates.some(
    (state) => state.state_code === selectedCode,
  )
    ? selectedCode
    : (selectableStates[0]?.state_code ?? '')

  async function loadWorkspace(nextProfile?: AccountProfile) {
    const resolvedProfile = nextProfile ?? profile
    if (!resolvedProfile || resolvedProfile.max_users <= 1) return
    const [watchlistResponse, alertsResponse] = await Promise.all([
      fetch('/api/customer/watchlists/organization', { cache: 'no-store' }),
      fetch(`/api/customer/watchlists/organization/alerts?year=${year}`, {
        cache: 'no-store',
      }),
    ])
    if (!watchlistResponse.ok) {
      setMessage(await errorMessage(watchlistResponse))
      return
    }
    if (!alertsResponse.ok) {
      setMessage(await errorMessage(alertsResponse))
      return
    }
    setWatchlist((await watchlistResponse.json()) as WatchlistItem[])
    setAlerts((await alertsResponse.json()) as AlertsResponse)
  }

  async function load() {
    const profileResponse = await fetch('/api/customer/account/me', {
      cache: 'no-store',
    })
    if (profileResponse.status === 401) return
    if (!profileResponse.ok) {
      setMessage(await errorMessage(profileResponse))
      setLoading(false)
      return
    }
    const nextProfile = (await profileResponse.json()) as AccountProfile
    setProfile(nextProfile)
    await loadWorkspace(nextProfile)
    setLoading(false)
  }

  useEffect(() => {
    // Initial organization workspace hydration intentionally updates local UI state.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function addState() {
    if (!effectiveSelectedCode || !canAdmin) return
    setMessage('')
    const response = await fetch('/api/customer/watchlists/organization', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ state_code: effectiveSelectedCode }),
    })
    if (!response.ok) {
      setMessage(await errorMessage(response))
      return
    }
    await loadWorkspace()
  }

  async function removeState(id: string) {
    if (!canAdmin) return
    setMessage('')
    const response = await fetch(`/api/customer/watchlists/organization/${id}`, {
      method: 'DELETE',
    })
    if (!response.ok) {
      setMessage(await errorMessage(response))
      return
    }
    await loadWorkspace()
  }

  async function markRead(id: string) {
    const response = await fetch(
      `/api/customer/watchlists/organization/alerts/${id}/read`,
      { method: 'POST' },
    )
    if (!response.ok) {
      setMessage(await errorMessage(response))
      return
    }
    await loadWorkspace()
  }

  async function markAllRead() {
    const response = await fetch(
      `/api/customer/watchlists/organization/alerts/read-all?year=${year}`,
      { method: 'POST' },
    )
    if (!response.ok) {
      setMessage(await errorMessage(response))
      return
    }
    await loadWorkspace()
  }

  if (loading || !profile) return null

  if (!eligible) {
    return (
      <Card className="mt-8 border-dashed">
        <CardHeader>
          <Users className="text-primary size-5" aria-hidden="true" />
          <CardTitle className="pt-3">Shared organization monitoring</CardTitle>
          <CardDescription className="max-w-3xl">
            Team and API organizations can maintain one shared jurisdiction list
            and evidence-backed alert inbox while each member keeps independent
            read state. Personal Watchlists remain available on every account.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button asChild>
            <Link href="/pricing">Compare Team and API</Link>
          </Button>
        </CardContent>
      </Card>
    )
  }

  return (
    <section className="mt-8 rounded-2xl border border-primary/15 bg-primary/[0.025] p-5 sm:p-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="max-w-3xl">
          <div className="flex items-center gap-2">
            <Users className="text-primary size-5" aria-hidden="true" />
            <p className="text-primary font-mono text-xs font-semibold tracking-[0.16em] uppercase">
              Organization monitoring
            </p>
          </div>
          <h2 className="mt-3 text-2xl font-semibold">
            {profile.organization_name} shared workspace
          </h2>
          <p className="text-muted-foreground mt-2 text-sm leading-6">
            Everyone in the organization sees the same governed monitoring list
            and alert ledger. Read receipts stay personal to each member, so one
            analyst cannot clear another analyst&apos;s inbox.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <StatusPill tone="success">{profile.plan_code}</StatusPill>
          <StatusPill tone="neutral">{profile.membership_role}</StatusPill>
        </div>
      </div>

      {message ? (
        <p className="border-border bg-background mt-5 rounded-lg border p-3 text-sm">
          {message}
        </p>
      ) : null}

      <div className="mt-6 grid gap-4 lg:grid-cols-[1fr_20rem]">
        <Card>
          <CardHeader>
            <CardTitle>Shared jurisdictions</CardTitle>
            <CardDescription>
              Owners and administrators control the organization monitoring
              perimeter. Members can inspect every shared state and alert.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {canAdmin ? (
              <div className="flex flex-col gap-3 sm:flex-row">
                <select
                  value={effectiveSelectedCode}
                  onChange={(event) => setSelectedCode(event.target.value)}
                  disabled={selectableStates.length === 0}
                  className="border-input bg-background h-10 min-w-0 flex-1 rounded-md border px-3 text-sm"
                  aria-label="Jurisdiction to share with organization"
                >
                  {selectableStates.length === 0 ? (
                    <option value="">
                      All available jurisdictions are monitored
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
                  Add to workspace
                </Button>
              </div>
            ) : (
              <p className="text-muted-foreground text-sm">
                Your organization administrator controls the shared monitoring
                list.
              </p>
            )}
          </CardContent>
        </Card>

        <Card className="bg-background/80">
          <CardHeader>
            <ShieldCheck className="text-primary size-5" aria-hidden="true" />
            <CardTitle className="pt-3">Governed boundary</CardTitle>
            <CardDescription>
              Shared alerts are snapshots of deterministic Fiscal Watch signals
              and immutable Fiscal Events. This workspace does not create new
              fiscal facts or infer missing values.
            </CardDescription>
          </CardHeader>
        </Card>
      </div>

      {watchlist.length ? (
        <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {watchlist.map((item) => (
            <Card key={item.id} className="bg-background/80">
              <CardHeader>
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <CardTitle>{item.state_name}</CardTitle>
                    <CardDescription className="mt-1">
                      {item.state_code} · {item.geopolitical_zone}
                    </CardDescription>
                  </div>
                  {canAdmin ? (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => removeState(item.id)}
                      aria-label={`Remove ${item.state_name} from shared monitoring`}
                    >
                      <Trash2 className="size-4" aria-hidden="true" />
                    </Button>
                  ) : null}
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
      ) : (
        <p className="text-muted-foreground mt-5 text-sm">
          No jurisdictions are in the shared monitoring perimeter yet.
        </p>
      )}

      <div className="mt-8 flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-primary font-mono text-xs font-semibold tracking-[0.16em] uppercase">
            Shared alert ledger
          </p>
          <h3 className="mt-2 text-xl font-semibold">
            {alerts?.unread_count ?? 0} unread for you ·{' '}
            {alerts?.alert_count ?? 0} organization alerts in {year}
          </h3>
        </div>
        <div className="flex flex-wrap gap-2">
          {alerts?.unread_count ? (
            <Button size="sm" variant="outline" onClick={markAllRead}>
              <CheckCheck className="size-4" aria-hidden="true" />
              Mark all read for me
            </Button>
          ) : null}
          <Button asChild size="sm" variant="outline">
            <Link href="/events">Evidence events</Link>
          </Button>
        </div>
      </div>

      {!alerts || alerts.alerts.length === 0 ? (
        <Card className="mt-4 border-dashed bg-background/70">
          <CardHeader>
            <Bell className="text-muted-foreground size-5" aria-hidden="true" />
            <CardTitle className="pt-3">No shared governed alerts yet</CardTitle>
            <CardDescription>
              Nothing has crossed the deterministic monitoring or evidence-event
              boundary for the shared jurisdictions in {year}. Nothing has been
              inferred.
            </CardDescription>
          </CardHeader>
        </Card>
      ) : (
        <div className="mt-4 space-y-3">
          {alerts.alerts.map((alert) => (
            <Card
              key={alert.id}
              className={
                alert.is_read ? 'bg-background/70 opacity-75' : 'bg-background'
              }
            >
              <CardHeader>
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <StatusPill tone={alert.is_read ? 'neutral' : 'success'}>
                        {alert.is_read ? 'Read by you' : 'Unread for you'}
                      </StatusPill>
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
                        Mark read for me
                      </Button>
                    ) : null}
                    <Button asChild size="sm" variant="outline">
                      <Link href={alert.link_path}>Inspect evidence</Link>
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="grid gap-4 text-sm sm:grid-cols-2">
                <div>
                  <p className="text-muted-foreground">Recorded event</p>
                  <p className="mt-1 font-mono font-medium">
                    {metricText(alert)}
                  </p>
                </div>
                <div>
                  <p className="text-muted-foreground">Evidence IDs</p>
                  <p className="mt-1 font-mono text-xs break-all">
                    {alert.evidence_ids.length
                      ? alert.evidence_ids.join(' · ')
                      : 'No explicit evidence IDs attached'}
                  </p>
                </div>
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
  )
}
