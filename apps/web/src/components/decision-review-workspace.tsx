'use client'

import { useCallback, useEffect, useState } from 'react'
import Link from 'next/link'

import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'

interface DecisionRoom {
  id: string
  title: string
  decision_question: string | null
  jurisdictions: string[]
  evidence_domains: string[]
  baseline_date: string | null
  evidence_cutoff: string | null
  status: string
}

interface ReviewTrigger {
  match_id: string
  contract_id: string
  contract_name: string
  state_code: string
  state_name: string
  event_type: string
  severity: string
  headline: string
  detail: string
  occurred_at: string
  matched_at: string
}

interface ReviewState {
  room_id: string
  review_required: boolean
  review_trigger_match_id: string | null
  review_required_at: string | null
  last_reviewed_at: string | null
  reviewed_by_user_id: string | null
  latest_receipt_id: string | null
  latest_receipt_sha256: string | null
  latest_receipt_created_at: string | null
  predecessor_receipt_id: string | null
  triggering_match_id: string | null
  trigger: ReviewTrigger | null
}

interface ReceiptSummary {
  id: string
  room_id: string
  predecessor_receipt_id: string | null
  triggering_match_id: string | null
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

function shortHash(value: string | null) {
  if (!value) return '—'
  return `${value.slice(0, 12)}…${value.slice(-10)}`
}

export function DecisionReviewWorkspace({ roomId }: { roomId: string }) {
  const [room, setRoom] = useState<DecisionRoom | null>(null)
  const [review, setReview] = useState<ReviewState | null>(null)
  const [receipts, setReceipts] = useState<ReceiptSummary[]>([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    const [roomRow, reviewRow, receiptRows] = await Promise.all([
      request<DecisionRoom>(`/evidence-rooms/${roomId}`),
      request<ReviewState>(`/decision-rooms/${roomId}/review-state`),
      request<ReceiptSummary[]>(`/decision-rooms/${roomId}/fiscal-receipts`),
    ])
    setRoom(roomRow)
    setReview(reviewRow)
    setReceipts(receiptRows)
    setError(null)
  }, [roomId])

  useEffect(() => {
    let cancelled = false
    void Promise.all([
      request<DecisionRoom>(`/evidence-rooms/${roomId}`),
      request<ReviewState>(`/decision-rooms/${roomId}/review-state`),
      request<ReceiptSummary[]>(`/decision-rooms/${roomId}/fiscal-receipts`),
    ])
      .then(([roomRow, reviewRow, receiptRows]) => {
        if (cancelled) return
        setRoom(roomRow)
        setReview(reviewRow)
        setReceipts(receiptRows)
      })
      .catch((caught: unknown) => {
        if (cancelled) return
        setError(caught instanceof Error ? caught.message : 'Decision review is unavailable.')
      })

    return () => {
      cancelled = true
    }
  }, [roomId])

  async function issueSuccessorReceipt() {
    setBusy(true)
    try {
      await request<ReceiptDetail>(`/decision-rooms/${roomId}/fiscal-receipts`, {
        method: 'POST',
      })
      await refresh()
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : 'Unable to issue successor Fiscal Receipt.',
      )
    } finally {
      setBusy(false)
    }
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Decision review unavailable</CardTitle>
          <CardDescription>{error}</CardDescription>
        </CardHeader>
        <CardContent>
          <Button asChild variant="outline">
            <Link href="/decision-rooms">Back to Decision Rooms</Link>
          </Button>
        </CardContent>
      </Card>
    )
  }

  if (!room || !review) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Loading decision review…</CardTitle>
        </CardHeader>
      </Card>
    )
  }

  return (
    <div className="space-y-5">
      <Card
        className={
          review.review_required
            ? 'overflow-hidden border-amber-500/30 bg-amber-500/[0.04]'
            : 'overflow-hidden border-emerald-500/20 bg-emerald-500/[0.03]'
        }
      >
        <CardHeader className="border-b">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="max-w-3xl">
              <p
                className={`font-mono text-[0.65rem] font-semibold tracking-[0.16em] uppercase ${
                  review.review_required ? 'text-amber-700' : 'text-emerald-700'
                }`}
              >
                {review.review_required ? 'Decision review required' : 'Decision review current'}
              </p>
              <CardTitle className="mt-2 text-2xl">{room.title}</CardTitle>
              <CardDescription className="mt-2">
                {room.decision_question ?? 'No formal decision question has been declared.'}
              </CardDescription>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button asChild variant="outline">
                <Link href="/decision-rooms">Decision Rooms</Link>
              </Button>
              <Button asChild variant="outline">
                <Link href="/watch-contracts">Watch Contracts</Link>
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="grid gap-4 pt-5 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <p className="text-muted-foreground text-xs">Jurisdictions</p>
            <p className="mt-1 text-sm font-medium">
              {room.jurisdictions.join(', ') || 'Not declared'}
            </p>
          </div>
          <div>
            <p className="text-muted-foreground text-xs">Evidence domains</p>
            <p className="mt-1 text-sm font-medium">
              {room.evidence_domains.join(', ') || 'Not declared'}
            </p>
          </div>
          <div>
            <p className="text-muted-foreground text-xs">Latest Receipt</p>
            <p className="mt-1 font-mono text-sm font-medium">
              {shortHash(review.latest_receipt_sha256)}
            </p>
          </div>
          <div>
            <p className="text-muted-foreground text-xs">Last reviewed</p>
            <p className="mt-1 text-sm font-medium">
              {review.last_reviewed_at
                ? new Date(review.last_reviewed_at).toLocaleString()
                : 'Not yet reviewed'}
            </p>
          </div>
        </CardContent>
      </Card>

      {review.review_required ? (
        <Card className="border-amber-500/30">
          <CardHeader>
            <CardTitle>What changed</CardTitle>
            <CardDescription>
              Gaia preserves the governed Watch Contract match that reopened this decision. Human review is required before a successor Receipt becomes the new decision record.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            {review.trigger ? (
              <>
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                  <div>
                    <p className="text-muted-foreground text-xs">Watch Contract</p>
                    <p className="mt-1 text-sm font-medium">{review.trigger.contract_name}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground text-xs">Jurisdiction</p>
                    <p className="mt-1 text-sm font-medium">
                      {review.trigger.state_name} · {review.trigger.state_code}
                    </p>
                  </div>
                  <div>
                    <p className="text-muted-foreground text-xs">Severity</p>
                    <p className="mt-1 text-sm font-medium capitalize">
                      {review.trigger.severity}
                    </p>
                  </div>
                  <div>
                    <p className="text-muted-foreground text-xs">Occurred</p>
                    <p className="mt-1 text-sm font-medium">
                      {new Date(review.trigger.occurred_at).toLocaleString()}
                    </p>
                  </div>
                </div>
                <div className="rounded-xl border bg-muted/20 p-4">
                  <p className="font-semibold">{review.trigger.headline}</p>
                  <p className="text-muted-foreground mt-2 text-sm leading-6">
                    {review.trigger.detail}
                  </p>
                  <p className="text-muted-foreground mt-3 font-mono text-xs">
                    {review.trigger.event_type} · match {review.trigger.match_id}
                  </p>
                </div>
              </>
            ) : (
              <p className="text-muted-foreground text-sm">
                The room is marked for review, but detailed trigger context is not available.
              </p>
            )}

            <div className="flex flex-wrap items-center justify-between gap-4 rounded-xl border border-amber-500/20 bg-amber-500/[0.04] p-4">
              <div>
                <p className="font-semibold">Resolve by issuing a successor Fiscal Receipt</p>
                <p className="text-muted-foreground mt-1 max-w-2xl text-sm">
                  This does not approve the decision automatically. It records the current evidence boundary, links the predecessor Receipt and triggering Watch match, and records that the room was re-reviewed.
                </p>
              </div>
              <Button disabled={busy} onClick={() => void issueSuccessorReceipt()}>
                {busy ? 'Issuing…' : 'Issue successor Receipt'}
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle>No unresolved governed change</CardTitle>
            <CardDescription>
              This Decision Room is current against the monitoring events Gaia has recorded. Watch Contracts remain active independently of room lifecycle.
            </CardDescription>
          </CardHeader>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Fiscal Receipt lineage</CardTitle>
          <CardDescription>
            Each successor Receipt points to its predecessor. The chain preserves how the decision evidence record evolved after governed changes.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {receipts.length === 0 ? (
            <p className="text-muted-foreground text-sm">No Fiscal Receipts exist for this room yet.</p>
          ) : (
            <div className="space-y-3">
              {receipts.map((receipt, index) => (
                <div key={receipt.id} className="rounded-xl border p-4">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="font-mono text-xs text-muted-foreground">
                        {index === 0 ? 'Current Receipt' : `Prior Receipt ${index}`}
                      </p>
                      <p className="mt-1 font-mono text-sm font-semibold break-all">
                        {receipt.receipt_sha256}
                      </p>
                    </div>
                    <Button asChild size="sm" variant="outline">
                      <Link href={`/verify/${receipt.id}`}>Verify</Link>
                    </Button>
                  </div>
                  <div className="text-muted-foreground mt-3 flex flex-wrap gap-x-5 gap-y-1 text-xs">
                    <span>{receipt.evidence_count} evidence records</span>
                    <span>{new Date(receipt.created_at).toLocaleString()}</span>
                    {receipt.predecessor_receipt_id ? (
                      <span>Predecessor {receipt.predecessor_receipt_id}</span>
                    ) : (
                      <span>Origin Receipt</span>
                    )}
                    {receipt.triggering_match_id ? (
                      <span>Triggered by Watch match {receipt.triggering_match_id}</span>
                    ) : null}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
