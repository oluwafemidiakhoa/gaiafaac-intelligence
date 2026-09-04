'use client'

import { FormEvent, useEffect, useState } from 'react'

import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'

type ContractStatus = 'active' | 'paused' | 'archived'

interface DecisionRoom {
  id: string
  title: string
  status: string
}

interface WatchContract {
  id: string
  room_id: string
  baseline_receipt_id: string | null
  name: string
  state_codes: string[]
  event_types: string[]
  minimum_severity: string
  status: ContractStatus
  last_evaluated_at: string | null
  created_at: string
  match_count: number
}

interface WatchMatch {
  id: string
  contract_id: string
  room_id: string
  organization_alert_id: string
  state_code: string
  state_name: string
  event_type: string
  severity: string
  headline: string
  detail: string
  occurred_at: string
  matched_at: string
}

interface Evaluation {
  contract: WatchContract
  new_match_count: number
  total_match_count: number
  matches: WatchMatch[]
  note: string
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api/customer${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
    cache: 'no-store',
  })
  if (!response.ok) {
    let detail = `Request failed (${response.status})`
    try {
      const payload = (await response.json()) as { detail?: string }
      if (payload.detail) detail = payload.detail
    } catch {
      // Preserve status-based error when upstream body is not JSON.
    }
    throw new Error(detail)
  }
  return (await response.json()) as T
}

function csv(value: FormDataEntryValue | null) {
  return String(value ?? '')
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
}

export function FiscalWatchContractsWorkspace() {
  const [rooms, setRooms] = useState<DecisionRoom[]>([])
  const [contracts, setContracts] = useState<WatchContract[]>([])
  const [selected, setSelected] = useState<WatchContract | null>(null)
  const [matches, setMatches] = useState<WatchMatch[]>([])
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function refresh() {
    const [roomRows, contractRows] = await Promise.all([
      request<DecisionRoom[]>('/evidence-rooms'),
      request<WatchContract[]>('/fiscal-watch-contracts'),
    ])
    setRooms(roomRows)
    setContracts(contractRows)
    if (selected) {
      const current =
        contractRows.find((item) => item.id === selected.id) ?? null
      setSelected(current)
    }
  }

  useEffect(() => {
    let cancelled = false
    void Promise.all([
      request<DecisionRoom[]>('/evidence-rooms'),
      request<WatchContract[]>('/fiscal-watch-contracts'),
    ])
      .then(([roomRows, contractRows]) => {
        if (cancelled) return
        setRooms(roomRows)
        setContracts(contractRows)
      })
      .catch((caught: unknown) => {
        if (cancelled) return
        setError(
          caught instanceof Error
            ? caught.message
            : 'Watch Contracts are unavailable.',
        )
      })
    return () => {
      cancelled = true
    }
  }, [])

  async function openContract(contract: WatchContract) {
    setSelected(contract)
    try {
      setMatches(
        await request<WatchMatch[]>(
          `/fiscal-watch-contracts/${contract.id}/matches`,
        ),
      )
      setError(null)
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : 'Unable to load contract matches.',
      )
    }
  }

  async function createContract(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const formElement = event.currentTarget
    const form = new FormData(formElement)
    setBusy(true)
    try {
      const created = await request<WatchContract>('/fiscal-watch-contracts', {
        method: 'POST',
        body: JSON.stringify({
          name: String(form.get('name') ?? '').trim(),
          room_id: String(form.get('room_id') ?? ''),
          baseline_receipt_id:
            String(form.get('baseline_receipt_id') ?? '').trim() || null,
          state_codes: csv(form.get('state_codes')),
          event_types: csv(form.get('event_types')),
          minimum_severity: String(form.get('minimum_severity') ?? 'watch'),
        }),
      })
      formElement.reset()
      await refresh()
      await openContract(created)
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : 'Unable to create Watch Contract.',
      )
    } finally {
      setBusy(false)
    }
  }

  async function evaluate() {
    if (!selected) return
    setBusy(true)
    try {
      const result = await request<Evaluation>(
        `/fiscal-watch-contracts/${selected.id}/evaluate`,
        { method: 'POST' },
      )
      setSelected(result.contract)
      setMatches(result.matches)
      await refresh()
      setError(null)
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : 'Unable to evaluate Watch Contract.',
      )
    } finally {
      setBusy(false)
    }
  }

  async function setStatus(status: ContractStatus) {
    if (!selected) return
    setBusy(true)
    try {
      const updated = await request<WatchContract>(
        `/fiscal-watch-contracts/${selected.id}/status`,
        { method: 'PATCH', body: JSON.stringify({ status }) },
      )
      setSelected(updated)
      await refresh()
      setError(null)
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : 'Unable to update contract status.',
      )
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[22rem_minmax(0,1fr)]">
      <aside className="space-y-5">
        <Card>
          <CardHeader>
            <CardTitle>Create Watch Contract</CardTitle>
            <CardDescription>
              Define exactly which governed changes should reopen a decision.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form className="grid gap-3" onSubmit={createContract}>
              <input
                name="name"
                required
                minLength={3}
                maxLength={200}
                placeholder="Edo facility monitoring mandate"
                className="border-input bg-background h-10 rounded-md border px-3 text-sm"
              />
              <select
                name="room_id"
                required
                defaultValue=""
                className="border-input bg-background h-10 rounded-md border px-3 text-sm"
              >
                <option value="" disabled>
                  Link Decision Room
                </option>
                {rooms.map((room) => (
                  <option key={room.id} value={room.id}>
                    {room.title}
                  </option>
                ))}
              </select>
              <input
                name="baseline_receipt_id"
                placeholder="Baseline Fiscal Receipt ID (optional)"
                className="border-input bg-background h-10 rounded-md border px-3 text-sm"
              />
              <input
                name="state_codes"
                placeholder="State codes: ED, DE"
                className="border-input bg-background h-10 rounded-md border px-3 text-sm"
              />
              <input
                name="event_types"
                placeholder="Events: source_revised, large_monthly_move"
                className="border-input bg-background h-10 rounded-md border px-3 text-sm"
              />
              <select
                name="minimum_severity"
                defaultValue="watch"
                className="border-input bg-background h-10 rounded-md border px-3 text-sm"
              >
                <option value="informational">Informational+</option>
                <option value="watch">Watch+</option>
                <option value="elevated">Elevated+</option>
                <option value="notable">Notable+</option>
                <option value="material">Material+</option>
                <option value="critical">Critical only</option>
              </select>
              <Button type="submit" disabled={busy || rooms.length === 0}>
                Activate Watch Contract
              </Button>
            </form>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Active mandates</CardTitle>
            <CardDescription>
              {contracts.length} organization contracts
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {contracts.length === 0 ? (
              <p className="text-muted-foreground text-sm">No contracts yet.</p>
            ) : (
              contracts.map((contract) => (
                <button
                  key={contract.id}
                  type="button"
                  onClick={() => void openContract(contract)}
                  className="border-border hover:bg-muted/50 w-full rounded-lg border p-3 text-left"
                >
                  <div className="flex items-start justify-between gap-3">
                    <span className="text-sm font-medium">{contract.name}</span>
                    <span className="text-muted-foreground text-[0.65rem] font-semibold uppercase">
                      {contract.status}
                    </span>
                  </div>
                  <p className="text-muted-foreground mt-2 text-xs">
                    {contract.match_count} matches · {contract.minimum_severity}
                    +
                  </p>
                </button>
              ))
            )}
          </CardContent>
        </Card>
      </aside>

      <section className="min-w-0 space-y-5">
        {error ? (
          <div className="border-destructive/30 bg-destructive/5 text-destructive rounded-xl border p-4 text-sm">
            {error}
          </div>
        ) : null}

        {!selected ? (
          <Card>
            <CardHeader>
              <CardTitle>
                Monitoring tied to a decision, not a dashboard.
              </CardTitle>
              <CardDescription>
                Select a Watch Contract to evaluate governed changes against its
                declared mandate.
              </CardDescription>
            </CardHeader>
          </Card>
        ) : (
          <>
            <Card>
              <CardHeader>
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div>
                    <p className="font-mono text-xs tracking-[0.15em] text-emerald-700 uppercase">
                      Fiscal Watch Contract · {selected.status}
                    </p>
                    <CardTitle className="mt-2 text-2xl">
                      {selected.name}
                    </CardTitle>
                    <CardDescription className="mt-2">
                      Linked Decision Room {selected.room_id}
                    </CardDescription>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Button
                      disabled={busy || selected.status !== 'active'}
                      onClick={() => void evaluate()}
                    >
                      Evaluate now
                    </Button>
                    <Button
                      variant="outline"
                      disabled={busy || selected.status === 'paused'}
                      onClick={() => void setStatus('paused')}
                    >
                      Pause
                    </Button>
                    <Button
                      variant="outline"
                      disabled={busy || selected.status === 'active'}
                      onClick={() => void setStatus('active')}
                    >
                      Activate
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <div>
                  <p className="text-muted-foreground text-xs">Jurisdictions</p>
                  <p className="mt-1 text-sm font-medium">
                    {selected.state_codes.join(', ') ||
                      'All shared watchlist jurisdictions'}
                  </p>
                </div>
                <div>
                  <p className="text-muted-foreground text-xs">Event types</p>
                  <p className="mt-1 text-sm font-medium">
                    {selected.event_types.join(', ') ||
                      'All governed event types'}
                  </p>
                </div>
                <div>
                  <p className="text-muted-foreground text-xs">
                    Minimum severity
                  </p>
                  <p className="mt-1 text-sm font-medium capitalize">
                    {selected.minimum_severity}
                  </p>
                </div>
                <div>
                  <p className="text-muted-foreground text-xs">
                    Last evaluated
                  </p>
                  <p className="mt-1 text-sm font-medium">
                    {selected.last_evaluated_at
                      ? new Date(selected.last_evaluated_at).toLocaleString()
                      : 'Never'}
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Matched governed changes</CardTitle>
                <CardDescription>
                  These are persisted matches to organization alerts generated
                  from published Fiscal Watch signals and immutable Fiscal
                  Events.
                </CardDescription>
              </CardHeader>
              <CardContent>
                {matches.length === 0 ? (
                  <p className="text-muted-foreground text-sm">
                    No governed changes match this contract yet.
                  </p>
                ) : (
                  <div className="divide-border border-border divide-y rounded-xl border">
                    {matches.map((match) => (
                      <div key={match.id} className="p-4">
                        <div className="flex flex-wrap items-center justify-between gap-3">
                          <div>
                            <p className="font-semibold">{match.headline}</p>
                            <p className="text-muted-foreground mt-1 text-sm">
                              {match.detail}
                            </p>
                          </div>
                          <div className="text-right">
                            <p className="font-mono text-xs uppercase">
                              {match.state_code} · {match.severity}
                            </p>
                            <p className="text-muted-foreground mt-1 text-xs">
                              {new Date(match.occurred_at).toLocaleString()}
                            </p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </>
        )}
      </section>
    </div>
  )
}
