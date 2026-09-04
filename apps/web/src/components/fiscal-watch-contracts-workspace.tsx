'use client'

import Link from 'next/link'
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
type ReviewStatus = 'open' | 'acknowledged' | 'resolved'

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
  escalation_after_minutes: number
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

interface WatchDelivery {
  id: string
  review_id: string
  match_id: string
  contract_id: string
  recipient_user_id: string | null
  channel: 'in_app'
  status: 'delivered' | 'failed'
  details: Record<string, unknown>
  delivered_at: string | null
  created_at: string
}

interface OperationalReview {
  id: string
  match_id: string
  contract_id: string
  room_id: string
  assigned_user_id: string | null
  status: ReviewStatus
  due_at: string
  escalated_at: string | null
  acknowledged_at: string | null
  acknowledged_by_user_id: string | null
  resolved_at: string | null
  resolved_by_user_id: string | null
  resolution_note: string | null
  created_at: string
  updated_at: string
  contract_name: string
  state_code: string
  state_name: string
  event_type: string
  severity: string
  headline: string
  detail: string
  occurred_at: string
  deliveries: WatchDelivery[]
}

interface Evaluation {
  contract: WatchContract
  new_match_count: number
  total_match_count: number
  matches: WatchMatch[]
  operational_review_count: number
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

function isOverdue(review: OperationalReview) {
  return (
    review.status !== 'resolved' &&
    new Date(review.due_at).getTime() < Date.now()
  )
}

function slaLabel(minutes: number) {
  if (minutes % 1440 === 0) return `${minutes / 1440}d`
  if (minutes % 60 === 0) return `${minutes / 60}h`
  return `${minutes}m`
}

export function FiscalWatchContractsWorkspace() {
  const [rooms, setRooms] = useState<DecisionRoom[]>([])
  const [contracts, setContracts] = useState<WatchContract[]>([])
  const [selected, setSelected] = useState<WatchContract | null>(null)
  const [matches, setMatches] = useState<WatchMatch[]>([])
  const [reviews, setReviews] = useState<OperationalReview[]>([])
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

  async function refreshReviews(contractId: string) {
    setReviews(
      await request<OperationalReview[]>(
        `/fiscal-watch-contracts/${contractId}/reviews`,
      ),
    )
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
      const [matchRows, reviewRows] = await Promise.all([
        request<WatchMatch[]>(`/fiscal-watch-contracts/${contract.id}/matches`),
        request<OperationalReview[]>(
          `/fiscal-watch-contracts/${contract.id}/reviews`,
        ),
      ])
      setMatches(matchRows)
      setReviews(reviewRows)
      setError(null)
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : 'Unable to load contract operations.',
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
          escalation_after_minutes: Number(
            form.get('escalation_after_minutes') ?? 1440,
          ),
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
      await Promise.all([refresh(), refreshReviews(selected.id)])
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

  async function acknowledgeReview(reviewId: string) {
    if (!selected) return
    setBusy(true)
    try {
      await request(`/fiscal-watch-contracts/reviews/${reviewId}/acknowledge`, {
        method: 'POST',
      })
      await refreshReviews(selected.id)
      setError(null)
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : 'Unable to acknowledge review.',
      )
    } finally {
      setBusy(false)
    }
  }

  async function resolveReview(reviewId: string) {
    if (!selected) return
    const resolutionNote = window.prompt(
      'Record the operational resolution. This does not clear the Decision Room evidence review.',
    )
    if (!resolutionNote?.trim()) return
    setBusy(true)
    try {
      await request(`/fiscal-watch-contracts/reviews/${reviewId}/resolve`, {
        method: 'POST',
        body: JSON.stringify({ resolution_note: resolutionNote.trim() }),
      })
      await refreshReviews(selected.id)
      setError(null)
    } catch (caught) {
      setError(
        caught instanceof Error ? caught.message : 'Unable to resolve review.',
      )
    } finally {
      setBusy(false)
    }
  }

  async function escalateOverdue() {
    if (!selected) return
    setBusy(true)
    try {
      await request('/fiscal-watch-contracts/reviews/escalate', {
        method: 'POST',
      })
      await refreshReviews(selected.id)
      setError(null)
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : 'Unable to escalate reviews.',
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
              <label className="text-muted-foreground grid gap-1 text-xs">
                Escalate unresolved operational review after
                <select
                  name="escalation_after_minutes"
                  defaultValue="1440"
                  className="border-input bg-background text-foreground h-10 rounded-md border px-3 text-sm"
                >
                  <option value="60">1 hour</option>
                  <option value="240">4 hours</option>
                  <option value="720">12 hours</option>
                  <option value="1440">24 hours</option>
                  <option value="2880">48 hours</option>
                  <option value="10080">7 days</option>
                </select>
              </label>
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
                    + · SLA {slaLabel(contract.escalation_after_minutes)}
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
                declared mandate and manage the resulting organization review
                queue.
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
                    <Button asChild variant="outline">
                      <Link href={`/decision-rooms/${selected.room_id}/review`}>
                        Decision Review
                      </Link>
                    </Button>
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
                    Operational SLA
                  </p>
                  <p className="mt-1 text-sm font-medium">
                    Escalate after {slaLabel(selected.escalation_after_minutes)}
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

            <Card className="border-amber-500/20">
              <CardHeader>
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div>
                    <CardTitle>Operational review queue</CardTitle>
                    <CardDescription className="mt-2 max-w-3xl">
                      Each new governed Watch match enters the organization
                      inbox once. Acknowledge and resolve operational handling
                      here. Evidence re-review remains open in the Decision Room
                      until a successor Fiscal Receipt is issued.
                    </CardDescription>
                  </div>
                  <Button
                    variant="outline"
                    disabled={busy}
                    onClick={() => void escalateOverdue()}
                  >
                    Escalate overdue
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                {reviews.length === 0 ? (
                  <p className="text-muted-foreground text-sm">
                    No operational reviews have been created for this contract
                    yet.
                  </p>
                ) : (
                  <div className="space-y-3">
                    {reviews.map((review) => {
                      const overdue = isOverdue(review)
                      const delivered = review.deliveries.some(
                        (item) =>
                          item.channel === 'in_app' &&
                          item.status === 'delivered',
                      )
                      return (
                        <div key={review.id} className="rounded-xl border p-4">
                          <div className="flex flex-wrap items-start justify-between gap-4">
                            <div className="max-w-3xl">
                              <div className="flex flex-wrap items-center gap-2">
                                <span className="font-semibold">
                                  {review.headline}
                                </span>
                                <span className="rounded-full border px-2 py-0.5 text-[0.65rem] font-semibold uppercase">
                                  {review.status}
                                </span>
                                {review.escalated_at ? (
                                  <span className="rounded-full border border-amber-500/30 bg-amber-500/10 px-2 py-0.5 text-[0.65rem] font-semibold text-amber-800 uppercase">
                                    Escalated
                                  </span>
                                ) : overdue ? (
                                  <span className="rounded-full border border-amber-500/30 px-2 py-0.5 text-[0.65rem] font-semibold text-amber-800 uppercase">
                                    Overdue
                                  </span>
                                ) : null}
                              </div>
                              <p className="text-muted-foreground mt-2 text-sm leading-6">
                                {review.detail}
                              </p>
                              <div className="text-muted-foreground mt-3 flex flex-wrap gap-x-4 gap-y-1 font-mono text-xs">
                                <span>{review.state_code}</span>
                                <span>{review.severity}</span>
                                <span>
                                  Due {new Date(review.due_at).toLocaleString()}
                                </span>
                                <span>
                                  {delivered
                                    ? 'In-app delivered'
                                    : 'Delivery pending'}
                                </span>
                              </div>
                            </div>
                            <div className="flex flex-wrap gap-2">
                              {review.status === 'open' ? (
                                <Button
                                  size="sm"
                                  variant="outline"
                                  disabled={busy}
                                  onClick={() =>
                                    void acknowledgeReview(review.id)
                                  }
                                >
                                  Acknowledge
                                </Button>
                              ) : null}
                              {review.status !== 'resolved' ? (
                                <Button
                                  size="sm"
                                  disabled={busy}
                                  onClick={() => void resolveReview(review.id)}
                                >
                                  Resolve handling
                                </Button>
                              ) : null}
                            </div>
                          </div>
                          {review.resolution_note ? (
                            <div className="bg-muted/30 mt-4 rounded-lg border p-3 text-sm">
                              <span className="font-medium">Resolution:</span>{' '}
                              {review.resolution_note}
                            </div>
                          ) : null}
                        </div>
                      )
                    })}
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Matched governed changes</CardTitle>
                <CardDescription>
                  Persisted matches to organization alerts generated from
                  published Fiscal Watch signals and immutable Fiscal Events.
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
