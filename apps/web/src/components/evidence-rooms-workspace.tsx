'use client'

import { FormEvent, useCallback, useEffect, useState } from 'react'

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
  status: RoomStatus
  evidence_count: number
  note_count: number
  updated_at: string
}

interface CapturedEvidence {
  id: string
  reference_kind: ReferenceKind
  reference_id: string
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

export function EvidenceRoomsWorkspace() {
  const [rooms, setRooms] = useState<RoomSummary[]>([])
  const [selected, setSelected] = useState<RoomDetail | null>(null)
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
          : 'Evidence Rooms are unavailable.',
      )
    }
  }, [])

  const openRoom = useCallback(async (roomId: string) => {
    try {
      const detail = await jsonRequest<RoomDetail>(`/evidence-rooms/${roomId}`)
      setSelected(detail)
      setError(null)
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : 'Evidence Room is unavailable.',
      )
    }
  }, [])

  useEffect(() => {
    let cancelled = false
    jsonRequest<RoomSummary[]>('/evidence-rooms')
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
            : 'Evidence Rooms are unavailable.',
        )
      })
    return () => {
      cancelled = true
    }
  }, [])

  async function createRoom(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    const title = String(form.get('title') ?? '').trim()
    const description = String(form.get('description') ?? '').trim()
    if (title.length < 3) return
    setBusy(true)
    try {
      const room = await jsonRequest<RoomSummary>('/evidence-rooms', {
        method: 'POST',
        body: JSON.stringify({ title, description: description || null }),
      })
      event.currentTarget.reset()
      await loadRooms()
      await openRoom(room.id)
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : 'Unable to create Evidence Room.',
      )
    } finally {
      setBusy(false)
    }
  }

  async function addEvidence(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!selected) return
    const form = new FormData(event.currentTarget)
    const referenceKind = String(form.get('reference_kind')) as ReferenceKind
    const referenceId = String(form.get('reference_id') ?? '').trim()
    const stateSlug = String(form.get('state_slug') ?? '').trim()
    const revenueMonth = String(form.get('revenue_month') ?? '').trim()
    const yearValue = String(form.get('year') ?? '').trim()
    if (!referenceId) return
    setBusy(true)
    try {
      await jsonRequest(`/evidence-rooms/${selected.id}/evidence`, {
        method: 'POST',
        body: JSON.stringify({
          reference_kind: referenceKind,
          reference_id: referenceId,
          state_slug: stateSlug || null,
          revenue_month: revenueMonth || null,
          year: yearValue ? Number(yearValue) : null,
        }),
      })
      event.currentTarget.reset()
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

  async function addNote(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!selected) return
    const form = new FormData(event.currentTarget)
    const body = String(form.get('body') ?? '').trim()
    if (!body) return
    setBusy(true)
    try {
      await jsonRequest(`/evidence-rooms/${selected.id}/notes`, {
        method: 'POST',
        body: JSON.stringify({ body }),
      })
      event.currentTarget.reset()
      await openRoom(selected.id)
      await loadRooms()
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Unable to add note.')
    } finally {
      setBusy(false)
    }
  }

  async function setStatus(status: RoomStatus) {
    if (!selected) return
    setBusy(true)
    try {
      await jsonRequest(`/evidence-rooms/${selected.id}/status`, {
        method: 'PATCH',
        body: JSON.stringify({ status }),
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
    <div className="grid gap-6 xl:grid-cols-[22rem_1fr]">
      <div className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Create case file</CardTitle>
            <CardDescription>
              Team/API organizations can create durable rooms. Evidence is
              immutable; notes remain commentary.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form className="grid gap-3" onSubmit={createRoom}>
              <input
                name="title"
                minLength={3}
                maxLength={200}
                required
                placeholder="Lagos Q3 credit review"
                className="border-input bg-background h-10 rounded-md border px-3 text-sm"
              />
              <textarea
                name="description"
                maxLength={5000}
                rows={3}
                placeholder="Purpose and decision context"
                className="border-input bg-background rounded-md border px-3 py-2 text-sm"
              />
              <Button disabled={busy} type="submit">
                Create Evidence Room
              </Button>
            </form>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Organization rooms</CardTitle>
            <CardDescription>{rooms.length} durable case files</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {rooms.length === 0 ? (
              <p className="text-muted-foreground text-sm">
                No Evidence Rooms available.
              </p>
            ) : (
              rooms.map((room) => (
                <button
                  key={room.id}
                  type="button"
                  onClick={() => void openRoom(room.id)}
                  className="border-border hover:bg-muted/50 w-full rounded-lg border p-3 text-left transition-colors"
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-medium">{room.title}</span>
                    <span className="text-muted-foreground text-xs uppercase">
                      {room.status}
                    </span>
                  </div>
                  <p className="text-muted-foreground mt-1 text-xs">
                    {room.evidence_count} evidence · {room.note_count} notes
                  </p>
                </button>
              ))
            )}
          </CardContent>
        </Card>
      </div>

      <div>
        {error ? (
          <div className="border-destructive/30 bg-destructive/5 text-destructive mb-4 rounded-lg border p-4 text-sm">
            {error}
          </div>
        ) : null}

        {!selected ? (
          <Card>
            <CardHeader>
              <CardTitle>Select an Evidence Room</CardTitle>
              <CardDescription>
                Open a room to capture governed references, review immutable
                hashes and keep human notes separate.
              </CardDescription>
            </CardHeader>
          </Card>
        ) : (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div>
                    <CardTitle>{selected.title}</CardTitle>
                    <CardDescription>
                      {selected.description ?? 'No description'}
                    </CardDescription>
                  </div>
                  <div className="flex gap-2">
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
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Capture governed evidence</CardTitle>
                <CardDescription>
                  References are snapshotted and hashed at capture time.
                  Captured evidence cannot be edited or deleted.
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
                    placeholder="Event ID, alert ID, proof ID or source SHA"
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
                  <Button disabled={busy} type="submit">
                    Capture immutable reference
                  </Button>
                </form>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Evidence chain</CardTitle>
                <CardDescription>
                  {selected.evidence.length} immutable captured references
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {selected.evidence.length === 0 ? (
                  <p className="text-muted-foreground text-sm">
                    No evidence captured yet.
                  </p>
                ) : (
                  selected.evidence.map((item) => (
                    <div
                      key={item.id}
                      className="border-border rounded-lg border p-4"
                    >
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <span className="font-medium">
                          {item.reference_kind.replaceAll('_', ' ')}
                        </span>
                        <span className="text-muted-foreground font-mono text-xs">
                          {new Date(item.captured_at).toISOString()}
                        </span>
                      </div>
                      <p className="text-muted-foreground mt-2 font-mono text-xs break-all">
                        Reference: {item.reference_id}
                      </p>
                      <p className="mt-2 font-mono text-xs break-all">
                        Record SHA-256: {item.record_sha256}
                      </p>
                      {item.source_sha256 ? (
                        <p className="text-muted-foreground mt-1 font-mono text-xs break-all">
                          Source SHA-256: {item.source_sha256}
                        </p>
                      ) : null}
                    </div>
                  ))
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Human notes</CardTitle>
                <CardDescription>
                  Notes are intentionally separate from governed fiscal evidence
                  and may be edited by their authors through the API.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <form className="flex gap-3" onSubmit={addNote}>
                  <textarea
                    name="body"
                    required
                    rows={2}
                    placeholder="Analyst interpretation or decision context"
                    className="border-input bg-background min-h-20 flex-1 rounded-md border px-3 py-2 text-sm"
                  />
                  <Button disabled={busy} type="submit">
                    Add note
                  </Button>
                </form>
                {selected.notes.map((note) => (
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
                ))}
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  )
}
