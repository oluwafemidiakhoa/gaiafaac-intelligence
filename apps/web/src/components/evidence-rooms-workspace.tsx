'use client'

import { FormEvent, useCallback, useEffect, useState } from 'react'
import Link from 'next/link'

import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'

type RoomStatus = 'open' | 'closed' | 'archived'
type ReferenceKind =
  | 'organization_alert'
  | 'fiscal_proof'
  | 'decision_packet'
  | 'source'
  | 'fiscal_event'

interface RoomSummary {
  id: string
  title: string
  description: string | null
  decision_question: string | null
  jurisdictions: string[]
  evidence_domains: string[]
  baseline_date: string | null
  evidence_cutoff: string | null
  status: RoomStatus
  evidence_count: number
  note_count: number
  updated_at: string
}

interface CapturedEvidence {
  id: string
  reference_kind: ReferenceKind
  reference_id: string
  reference_uri: string | null
  source_sha256: string | null
  record_sha256: string
  captured_at: string
}

interface RoomNote {
  id: string
  body: string
  created_at: string
  updated_at: string
}

interface RoomDetail extends RoomSummary {
  evidence: CapturedEvidence[]
  notes: RoomNote[]
}

interface ReceiptSummary {
  id: string
  room_id: string
  evidence_cutoff: string | null
  methodology_version: string
  receipt_sha256: string
  evidence_count: number
  created_at: string
}

interface ReceiptDetail extends ReceiptSummary {
  organization_id: string
  created_by_user_id: string | null
  manifest: Record<string, unknown>
}

async function jsonRequest<T>(path: string, init?: RequestInit): Promise<T> {
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
      // Preserve the status-based message when the response is not JSON.
    }
    throw new Error(detail)
  }
  return (await response.json()) as T
}

function commaList(value: FormDataEntryValue | null) {
  return String(value ?? '')
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
}

function shortHash(value: string) {
  return `${value.slice(0, 12)}…${value.slice(-10)}`
}

export function EvidenceRoomsWorkspace() {
  const [rooms, setRooms] = useState<RoomSummary[]>([])
  const [selected, setSelected] = useState<RoomDetail | null>(null)
  const [receipts, setReceipts] = useState<ReceiptSummary[]>([])
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const loadRooms = useCallback(async () => {
    try {
      const result = await jsonRequest<RoomSummary[]>('/evidence-rooms')
      setRooms(result)
      setError(null)
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : 'Decision Rooms are unavailable.',
      )
    }
  }, [])

  const loadReceipts = useCallback(async (roomId: string) => {
    try {
      const result = await jsonRequest<ReceiptSummary[]>(
        `/decision-rooms/${roomId}/fiscal-receipts`,
      )
      setReceipts(result)
    } catch {
      setReceipts([])
    }
  }, [])

  const openRoom = useCallback(
    async (roomId: string) => {
      try {
        const detail = await jsonRequest<RoomDetail>(
          `/evidence-rooms/${roomId}`,
        )
        setSelected(detail)
        await loadReceipts(roomId)
        setError(null)
      } catch (caught) {
        setError(
          caught instanceof Error
            ? caught.message
            : 'Decision Room is unavailable.',
        )
      }
    },
    [loadReceipts],
  )

  useEffect(() => {
    let cancelled = false

    void jsonRequest<RoomSummary[]>('/evidence-rooms')
      .then((result) => {
        if (cancelled) return
        setRooms(result)
        setError(null)
      })
      .catch((caught: unknown) => {
        if (cancelled) return
        setError(
          caught instanceof Error
            ? caught.message
            : 'Decision Rooms are unavailable.',
        )
      })

    return () => {
      cancelled = true
    }
  }, [])

  async function createRoom(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const formElement = event.currentTarget
    const form = new FormData(formElement)
    const title = String(form.get('title') ?? '').trim()
    if (title.length < 3) return
    setBusy(true)
    try {
      const room = await jsonRequest<RoomSummary>('/evidence-rooms', {
        method: 'POST',
        body: JSON.stringify({
          title,
          description: String(form.get('description') ?? '').trim() || null,
          decision_question:
            String(form.get('decision_question') ?? '').trim() || null,
          jurisdictions: commaList(form.get('jurisdictions')),
          evidence_domains: commaList(form.get('evidence_domains')),
          baseline_date: String(form.get('baseline_date') ?? '') || null,
        }),
      })
      formElement.reset()
      await loadRooms()
      await openRoom(room.id)
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : 'Unable to create Decision Room.',
      )
    } finally {
      setBusy(false)
    }
  }

  async function saveDecisionContext(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!selected) return
    const form = new FormData(event.currentTarget)
    setBusy(true)
    try {
      await jsonRequest(`/evidence-rooms/${selected.id}/decision-context`, {
        method: 'PATCH',
        body: JSON.stringify({
          decision_question:
            String(form.get('decision_question') ?? '').trim() || null,
          jurisdictions: commaList(form.get('jurisdictions')),
          evidence_domains: commaList(form.get('evidence_domains')),
          baseline_date: String(form.get('baseline_date') ?? '') || null,
          evidence_cutoff: selected.evidence_cutoff,
        }),
      })
      await openRoom(selected.id)
      await loadRooms()
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : 'Unable to save decision context.',
      )
    } finally {
      setBusy(false)
    }
  }

  async function addEvidence(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!selected) return
    const formElement = event.currentTarget
    const form = new FormData(formElement)
    const referenceId = String(form.get('reference_id') ?? '').trim()
    if (!referenceId) return
    setBusy(true)
    try {
      await jsonRequest(`/evidence-rooms/${selected.id}/evidence`, {
        method: 'POST',
        body: JSON.stringify({
          reference_kind: String(form.get('reference_kind')) as ReferenceKind,
          reference_id: referenceId,
          state_slug: String(form.get('state_slug') ?? '').trim() || null,
          revenue_month: String(form.get('revenue_month') ?? '').trim() || null,
          year: String(form.get('year') ?? '').trim()
            ? Number(form.get('year'))
            : null,
        }),
      })
      formElement.reset()
      await openRoom(selected.id)
      await loadRooms()
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : 'Unable to capture evidence.',
      )
    } finally {
      setBusy(false)
    }
  }

  async function generateReceipt() {
    if (!selected) return
    setBusy(true)
    try {
      const receipt = await jsonRequest<ReceiptDetail>(
        `/decision-rooms/${selected.id}/fiscal-receipts`,
        { method: 'POST' },
      )
      await loadReceipts(selected.id)
      window.location.assign(`/verify/${receipt.id}`)
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : 'Unable to generate Fiscal Receipt.',
      )
    } finally {
      setBusy(false)
    }
  }

  async function addNote(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!selected) return
    const formElement = event.currentTarget
    const form = new FormData(formElement)
    const body = String(form.get('body') ?? '').trim()
    if (!body) return
    setBusy(true)
    try {
      await jsonRequest(`/evidence-rooms/${selected.id}/notes`, {
        method: 'POST',
        body: JSON.stringify({ body }),
      })
      formElement.reset()
      await openRoom(selected.id)
      await loadRooms()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Unable to add note.')
    } finally {
      setBusy(false)
    }
  }

  async function setStatus(nextStatus: RoomStatus) {
    if (!selected) return
    setBusy(true)
    try {
      await jsonRequest(`/evidence-rooms/${selected.id}/status`, {
        method: 'PATCH',
        body: JSON.stringify({ status: nextStatus }),
      })
      await openRoom(selected.id)
      await loadRooms()
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : 'Unable to update room status.',
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
            <CardTitle>Start a Decision Room</CardTitle>
            <CardDescription>
              Freeze the context around an expensive decision before the
              evidence changes.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form className="grid gap-3" onSubmit={createRoom}>
              <input
                name="title"
                minLength={3}
                maxLength={200}
                required
                placeholder="Edo infrastructure facility · FY2026"
                className="border-input bg-background h-10 rounded-md border px-3 text-sm"
              />
              <textarea
                name="decision_question"
                maxLength={5000}
                rows={3}
                placeholder="What decision must this evidence support?"
                className="border-input bg-background rounded-md border px-3 py-2 text-sm"
              />
              <input
                name="jurisdictions"
                placeholder="Jurisdictions: Edo, Delta"
                className="border-input bg-background h-10 rounded-md border px-3 text-sm"
              />
              <input
                name="evidence_domains"
                placeholder="Domains: FAAC, IGR, debt"
                className="border-input bg-background h-10 rounded-md border px-3 text-sm"
              />
              <label className="text-muted-foreground grid gap-1 text-xs">
                Baseline date
                <input
                  name="baseline_date"
                  type="date"
                  className="border-input bg-background text-foreground h-10 rounded-md border px-3 text-sm"
                />
              </label>
              <textarea
                name="description"
                maxLength={5000}
                rows={2}
                placeholder="Internal purpose or mandate"
                className="border-input bg-background rounded-md border px-3 py-2 text-sm"
              />
              <Button disabled={busy} type="submit">
                Create Decision Room
              </Button>
            </form>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Organization rooms</CardTitle>
            <CardDescription>
              {rooms.length} durable decision case files
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {rooms.length === 0 ? (
              <p className="text-muted-foreground text-sm">
                No Decision Rooms yet.
              </p>
            ) : (
              rooms.map((room) => (
                <button
                  key={room.id}
                  type="button"
                  onClick={() => void openRoom(room.id)}
                  className="border-border hover:bg-muted/50 w-full rounded-lg border p-3 text-left transition-colors"
                >
                  <div className="flex items-start justify-between gap-3">
                    <span className="leading-5 font-medium">{room.title}</span>
                    <span className="text-muted-foreground text-[0.65rem] font-semibold tracking-wide uppercase">
                      {room.status}
                    </span>
                  </div>
                  <p className="text-muted-foreground mt-2 text-xs">
                    {room.evidence_count} evidence · {room.note_count} notes
                  </p>
                </button>
              ))
            )}
          </CardContent>
        </Card>
      </aside>

      <section className="min-w-0">
        {error ? (
          <div className="border-destructive/30 bg-destructive/5 text-destructive mb-4 rounded-lg border p-4 text-sm">
            {error}
          </div>
        ) : null}

        {!selected ? (
          <Card>
            <CardHeader>
              <CardTitle>Preserve what the institution knew.</CardTitle>
              <CardDescription>
                Select a room or create one. A Decision Room keeps governed
                evidence, human interpretation and later Fiscal Receipts
                structurally separate.
              </CardDescription>
            </CardHeader>
          </Card>
        ) : (
          <div className="space-y-5">
            <Card>
              <CardHeader>
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div className="max-w-3xl">
                    <p className="font-mono text-[0.65rem] font-semibold tracking-[0.16em] text-emerald-700 uppercase">
                      Decision Room · {selected.status}
                    </p>
                    <CardTitle className="mt-2 text-2xl">
                      {selected.title}
                    </CardTitle>
                    <CardDescription className="mt-2">
                      {selected.decision_question ??
                        'No formal decision question has been declared yet.'}
                    </CardDescription>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      disabled={busy || selected.status === 'open'}
                      onClick={() => void setStatus('open')}
                    >
                      Open
                    </Button>
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      disabled={busy || selected.status === 'closed'}
                      onClick={() => void setStatus('closed')}
                    >
                      Close
                    </Button>
                    <Button
                      type="button"
                      size="sm"
                      variant="outline"
                      disabled={busy || selected.status === 'archived'}
                      onClick={() => void setStatus('archived')}
                    >
                      Archive
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4 md:grid-cols-4">
                  <div>
                    <p className="text-muted-foreground text-xs">
                      Jurisdictions
                    </p>
                    <p className="mt-1 text-sm font-medium">
                      {selected.jurisdictions.join(', ') || 'Not declared'}
                    </p>
                  </div>
                  <div>
                    <p className="text-muted-foreground text-xs">
                      Evidence domains
                    </p>
                    <p className="mt-1 text-sm font-medium">
                      {selected.evidence_domains.join(', ') || 'Not declared'}
                    </p>
                  </div>
                  <div>
                    <p className="text-muted-foreground text-xs">Baseline</p>
                    <p className="mt-1 text-sm font-medium">
                      {selected.baseline_date ?? 'Not declared'}
                    </p>
                  </div>
                  <div>
                    <p className="text-muted-foreground text-xs">
                      Evidence captured
                    </p>
                    <p className="mt-1 font-mono text-lg font-semibold">
                      {selected.evidence.length}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <div className="grid gap-5 lg:grid-cols-[1fr_0.9fr]">
              <Card>
                <CardHeader>
                  <CardTitle>Decision context</CardTitle>
                  <CardDescription>
                    Human-defined context. It is not converted into fiscal fact.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <form className="grid gap-3" onSubmit={saveDecisionContext}>
                    <textarea
                      name="decision_question"
                      defaultValue={selected.decision_question ?? ''}
                      rows={3}
                      maxLength={5000}
                      placeholder="Decision question"
                      className="border-input bg-background rounded-md border px-3 py-2 text-sm"
                    />
                    <div className="grid gap-3 sm:grid-cols-2">
                      <input
                        name="jurisdictions"
                        defaultValue={selected.jurisdictions.join(', ')}
                        placeholder="Edo, Delta"
                        className="border-input bg-background h-10 rounded-md border px-3 text-sm"
                      />
                      <input
                        name="evidence_domains"
                        defaultValue={selected.evidence_domains.join(', ')}
                        placeholder="FAAC, IGR, debt"
                        className="border-input bg-background h-10 rounded-md border px-3 text-sm"
                      />
                    </div>
                    <label className="text-muted-foreground grid gap-1 text-xs">
                      Baseline date
                      <input
                        name="baseline_date"
                        type="date"
                        defaultValue={selected.baseline_date ?? ''}
                        className="border-input bg-background text-foreground h-10 rounded-md border px-3 text-sm"
                      />
                    </label>
                    <Button
                      disabled={busy || selected.status === 'archived'}
                      type="submit"
                    >
                      Save decision boundary
                    </Button>
                  </form>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Fiscal Receipt</CardTitle>
                  <CardDescription>
                    Generate a reproducible SHA-256 manifest from the evidence
                    captured in this room. Private notes are excluded from
                    public verification.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <Button
                    disabled={busy}
                    type="button"
                    onClick={() => void generateReceipt()}
                    className="w-full"
                  >
                    Generate Fiscal Receipt
                  </Button>
                  {receipts.length ? (
                    <div className="space-y-2">
                      {receipts.slice(0, 4).map((receipt) => (
                        <Link
                          key={receipt.id}
                          href={`/verify/${receipt.id}`}
                          className="border-border hover:bg-muted/50 block rounded-lg border p-3 transition"
                        >
                          <div className="flex items-center justify-between gap-3">
                            <span className="font-mono text-xs">
                              {shortHash(receipt.receipt_sha256)}
                            </span>
                            <span className="text-muted-foreground text-xs">
                              {receipt.evidence_count} records
                            </span>
                          </div>
                          <p className="text-muted-foreground mt-1 text-xs">
                            {new Date(receipt.created_at).toISOString()}
                          </p>
                        </Link>
                      ))}
                    </div>
                  ) : (
                    <p className="text-muted-foreground text-sm">
                      No Fiscal Receipt has been generated for this room yet.
                    </p>
                  )}
                </CardContent>
              </Card>
            </div>

            <Card>
              <CardHeader>
                <CardTitle>Capture governed evidence</CardTitle>
                <CardDescription>
                  Add existing Gaia evidence objects. Each reference is
                  snapshotted and hashed at capture time and cannot later be
                  edited.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form
                  className="grid gap-3 md:grid-cols-2"
                  onSubmit={addEvidence}
                >
                  <select
                    name="reference_kind"
                    defaultValue="fiscal_event"
                    className="border-input bg-background h-10 rounded-md border px-3 text-sm"
                  >
                    <option value="organization_alert">
                      Organization alert
                    </option>
                    <option value="fiscal_event">Fiscal Event</option>
                    <option value="fiscal_proof">Fiscal Proof</option>
                    <option value="decision_packet">Decision Packet</option>
                    <option value="source">Source SHA-256</option>
                  </select>
                  <input
                    name="reference_id"
                    required
                    placeholder="Event ID, proof ID, packet ID or source SHA"
                    className="border-input bg-background h-10 rounded-md border px-3 text-sm"
                  />
                  <input
                    name="state_slug"
                    placeholder="State slug when required"
                    className="border-input bg-background h-10 rounded-md border px-3 text-sm"
                  />
                  <input
                    name="revenue_month"
                    type="date"
                    className="border-input bg-background h-10 rounded-md border px-3 text-sm"
                  />
                  <input
                    name="year"
                    type="number"
                    min="2000"
                    max="2100"
                    placeholder="Year when required"
                    className="border-input bg-background h-10 rounded-md border px-3 text-sm"
                  />
                  <Button
                    disabled={busy || selected.status === 'archived'}
                    type="submit"
                  >
                    Capture evidence
                  </Button>
                </form>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Evidence manifest</CardTitle>
                <CardDescription>
                  {selected.evidence.length} immutable references currently
                  inside the decision boundary.
                </CardDescription>
              </CardHeader>
              <CardContent>
                {selected.evidence.length === 0 ? (
                  <p className="text-muted-foreground text-sm">
                    No evidence captured yet.
                  </p>
                ) : (
                  <div className="divide-border border-border divide-y rounded-xl border">
                    {selected.evidence.map((item) => (
                      <div key={item.id} className="p-4">
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <span className="text-sm font-semibold capitalize">
                            {item.reference_kind.replaceAll('_', ' ')}
                          </span>
                          <span className="text-muted-foreground font-mono text-xs">
                            {new Date(item.captured_at).toISOString()}
                          </span>
                        </div>
                        <p className="text-muted-foreground mt-2 font-mono text-xs break-all">
                          Reference {item.reference_id}
                        </p>
                        <p className="mt-1 font-mono text-xs break-all">
                          Record SHA-256 {item.record_sha256}
                        </p>
                        {item.source_sha256 ? (
                          <p className="text-muted-foreground mt-1 font-mono text-xs break-all">
                            Source SHA-256 {item.source_sha256}
                          </p>
                        ) : null}
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Human review notes</CardTitle>
                <CardDescription>
                  Interpretation remains explicitly separate from governed
                  evidence and is never included in the public receipt verifier.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <form
                  className="flex flex-col gap-3 sm:flex-row"
                  onSubmit={addNote}
                >
                  <textarea
                    name="body"
                    required
                    rows={2}
                    placeholder="Analyst interpretation, committee question or review note"
                    className="border-input bg-background min-h-20 flex-1 rounded-md border px-3 py-2 text-sm"
                  />
                  <Button
                    disabled={busy || selected.status === 'archived'}
                    type="submit"
                  >
                    Add note
                  </Button>
                </form>
                {selected.notes.length ? (
                  selected.notes.map((note) => (
                    <div
                      key={note.id}
                      className="border-border rounded-lg border p-4"
                    >
                      <p className="text-sm leading-6 whitespace-pre-wrap">
                        {note.body}
                      </p>
                      <p className="text-muted-foreground mt-2 text-xs">
                        Updated {new Date(note.updated_at).toISOString()}
                      </p>
                    </div>
                  ))
                ) : (
                  <p className="text-muted-foreground text-sm">
                    No human notes yet.
                  </p>
                )}
              </CardContent>
            </Card>
          </div>
        )}
      </section>
    </div>
  )
}
