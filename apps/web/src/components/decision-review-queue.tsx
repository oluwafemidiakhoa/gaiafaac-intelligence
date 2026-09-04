'use client'

import { useEffect, useState } from 'react'
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
  review_required_at: string | null
  latest_receipt_id: string | null
  latest_receipt_sha256: string | null
  trigger: ReviewTrigger | null
}

interface ReviewItem {
  room: DecisionRoom
  review: ReviewState
}

async function request<T>(path: string): Promise<T> {
  const response = await fetch(`/api/customer${path}`, { cache: 'no-store' })
  if (!response.ok) throw new Error(`Request failed (${response.status})`)
  return (await response.json()) as T
}

export function DecisionReviewQueue() {
  const [items, setItems] = useState<ReviewItem[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false

    void request<DecisionRoom[]>('/evidence-rooms')
      .then(async (rooms) => {
        const states = await Promise.all(
          rooms.map(async (room) => {
            try {
              const review = await request<ReviewState>(
                `/decision-rooms/${room.id}/review-state`,
              )
              return { room, review }
            } catch {
              return null
            }
          }),
        )
        if (cancelled) return
        setItems(
          states.filter(
            (item): item is ReviewItem => item !== null && item.review.review_required,
          ),
        )
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [])

  return (
    <Card className="overflow-hidden border-amber-500/20 bg-amber-500/[0.03]">
      <CardHeader className="border-b border-amber-500/15">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="font-mono text-[0.65rem] font-semibold tracking-[0.16em] text-amber-700 uppercase">
              Institutional review queue
            </p>
            <CardTitle className="mt-2">Decisions reopened by governed change</CardTitle>
            <CardDescription className="mt-2 max-w-3xl">
              A Watch Contract match never silently rewrites a decision. It reopens the linked Decision Room for human review and preserves the trigger until a successor Fiscal Receipt is issued.
            </CardDescription>
          </div>
          <div className="rounded-full border border-amber-500/20 bg-background px-3 py-1 font-mono text-xs">
            {loading ? 'Checking…' : `${items.length} require review`}
          </div>
        </div>
      </CardHeader>
      <CardContent className="pt-5">
        {loading ? (
          <p className="text-muted-foreground text-sm">Loading decision review state…</p>
        ) : items.length === 0 ? (
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <p className="font-medium">No Decision Room currently requires re-review.</p>
              <p className="text-muted-foreground mt-1 text-sm">
                Watch Contracts remain active and will reopen only the decisions whose declared monitoring rules match governed changes.
              </p>
            </div>
            <Button asChild variant="outline">
              <Link href="/watch-contracts">Open Watch Contracts</Link>
            </Button>
          </div>
        ) : (
          <div className="grid gap-3 lg:grid-cols-2">
            {items.map(({ room, review }) => (
              <Link
                key={room.id}
                href={`/decision-rooms/${room.id}/review`}
                className="group rounded-xl border border-amber-500/20 bg-background p-4 transition hover:border-amber-500/40"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="font-semibold group-hover:underline">{room.title}</p>
                    <p className="text-muted-foreground mt-1 line-clamp-2 text-sm">
                      {review.trigger?.headline ??
                        room.decision_question ??
                        'Governed monitoring change requires review.'}
                    </p>
                  </div>
                  <span className="rounded-full bg-amber-500/10 px-2 py-1 text-[0.65rem] font-semibold text-amber-800 uppercase">
                    Review required
                  </span>
                </div>
                <div className="text-muted-foreground mt-3 flex flex-wrap gap-x-4 gap-y-1 font-mono text-xs">
                  {review.trigger ? (
                    <>
                      <span>{review.trigger.state_code}</span>
                      <span>{review.trigger.severity}</span>
                      <span>{review.trigger.contract_name}</span>
                    </>
                  ) : null}
                </div>
              </Link>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
