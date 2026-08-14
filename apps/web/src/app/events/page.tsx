import type { Metadata } from 'next'
import Link from 'next/link'

import { DataUnavailable } from '@/components/data-unavailable'
import { PageHeader } from '@/components/page-header'
import { StatusPill } from '@/components/status-pill'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { getFiscalEvents } from '@/lib/fiscal-ledger-api'
import { formatDate, humanize } from '@/lib/format'

export const metadata: Metadata = {
  title: 'Gaia Fiscal Events',
  description: 'Deterministic fiscal evidence lifecycle events.',
}
export const dynamic = 'force-dynamic'

type EventSearchParams = {
  jurisdiction?: string
  event_type?: string
  severity?: string
  evidence_status?: string
  date_from?: string
  date_to?: string
}

export default async function FiscalEventsPage({
  searchParams,
}: {
  searchParams: Promise<EventSearchParams>
}) {
  const filters = await searchParams
  const result = await getFiscalEvents({
    jurisdiction: filters.jurisdiction,
    eventType: filters.event_type,
    severity: filters.severity,
    evidenceStatus: filters.evidence_status,
    dateFrom: filters.date_from,
    dateTo: filters.date_to,
  })
  const events = result.data?.data ?? []

  return (
    <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
      <PageHeader
        eyebrow="Gaia fiscal events"
        title="Evidence lifecycle stream"
        description="A chronological record of source, claim, conflict, and Fiscal State changes generated from retained evidence. Event text does not infer causality."
      />

      <Card className="mt-8">
        <CardContent className="pt-6">
          <form
            className="grid gap-4 md:grid-cols-3 xl:grid-cols-6"
            method="get"
          >
            <label className="grid gap-1.5 text-xs font-medium">
              Jurisdiction
              <input
                name="jurisdiction"
                defaultValue={filters.jurisdiction}
                placeholder="NG-LA"
                className="border-input bg-background h-9 rounded-md border px-3 text-sm"
              />
            </label>
            <label className="grid gap-1.5 text-xs font-medium">
              Event type
              <select
                name="event_type"
                defaultValue={filters.event_type ?? ''}
                className="border-input bg-background h-9 rounded-md border px-3 text-sm"
              >
                <option value="">All types</option>
                <option value="new_source_detected">New source detected</option>
                <option value="source_revised">Source revised</option>
                <option value="claim_superseded">Claim superseded</option>
                <option value="cross_source_conflict">
                  Cross-source conflict
                </option>
                <option value="fiscal_state_changed">
                  Fiscal State changed
                </option>
                <option value="faac_spike">FAAC spike</option>
                <option value="faac_decline">FAAC decline</option>
              </select>
            </label>
            <label className="grid gap-1.5 text-xs font-medium">
              Severity
              <select
                name="severity"
                defaultValue={filters.severity ?? ''}
                className="border-input bg-background h-9 rounded-md border px-3 text-sm"
              >
                <option value="">All severities</option>
                <option value="informational">Informational</option>
                <option value="notable">Notable</option>
                <option value="material">Material</option>
                <option value="critical">Critical</option>
              </select>
            </label>
            <label className="grid gap-1.5 text-xs font-medium">
              Evidence status
              <select
                name="evidence_status"
                defaultValue={filters.evidence_status ?? ''}
                className="border-input bg-background h-9 rounded-md border px-3 text-sm"
              >
                <option value="">All statuses</option>
                <option value="verified">Verified</option>
                <option value="partial">Partial</option>
                <option value="conflicting">Conflicting</option>
                <option value="unavailable">Unavailable</option>
              </select>
            </label>
            <label className="grid gap-1.5 text-xs font-medium">
              From
              <input
                name="date_from"
                type="date"
                defaultValue={filters.date_from}
                className="border-input bg-background h-9 rounded-md border px-3 text-sm"
              />
            </label>
            <label className="grid gap-1.5 text-xs font-medium">
              To
              <input
                name="date_to"
                type="date"
                defaultValue={filters.date_to}
                className="border-input bg-background h-9 rounded-md border px-3 text-sm"
              />
            </label>
            <div className="flex gap-2 md:col-span-3 xl:col-span-6">
              <Button type="submit" size="sm">
                Apply filters
              </Button>
              <Button asChild variant="outline" size="sm">
                <Link href="/events">Clear</Link>
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      <div className="mt-8">
        {events.length ? (
          <ol className="space-y-3">
            {events.map((event) => (
              <li key={event.event_id}>
                <Card>
                  <CardContent className="grid gap-4 pt-6 md:grid-cols-[9rem_8rem_1fr_auto] md:items-start">
                    <div>
                      <p className="font-mono text-sm font-semibold">
                        {formatDate(event.detected_at.slice(0, 10))}
                      </p>
                      <p className="text-muted-foreground mt-1 font-mono text-xs">
                        {event.detected_at.slice(11, 16)} UTC
                      </p>
                    </div>
                    <Link
                      href={`/jurisdictions/${event.jurisdiction.code}`}
                      className="hover:text-primary font-mono font-semibold"
                    >
                      {event.jurisdiction.code}
                    </Link>
                    <div>
                      <p className="font-medium">{event.explanation}</p>
                      <p className="text-muted-foreground mt-2 font-mono text-xs">
                        {humanize(event.event_type)} · {event.event_id}
                      </p>
                      {event.evidence_ids.length ? (
                        <p className="text-muted-foreground mt-2 text-xs">
                          Evidence: {event.evidence_ids.join(' · ')}
                        </p>
                      ) : null}
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <StatusPill
                        tone={
                          event.evidence_status === 'verified'
                            ? 'success'
                            : 'neutral'
                        }
                      >
                        {humanize(event.evidence_status)}
                      </StatusPill>
                      <StatusPill tone="neutral">{event.severity}</StatusPill>
                    </div>
                  </CardContent>
                </Card>
              </li>
            ))}
          </ol>
        ) : (
          <DataUnavailable message="No fiscal evidence lifecycle events match these filters." />
        )}
      </div>

      <p className="text-muted-foreground mt-6 text-xs leading-5">
        {result.data?.evidence.meaning ??
          'No event metadata is available. No causal explanation has been inferred.'}
      </p>
    </div>
  )
}
