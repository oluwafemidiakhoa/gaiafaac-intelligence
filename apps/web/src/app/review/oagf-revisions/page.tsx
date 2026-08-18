import { AlertTriangle, ArrowRight, CheckCircle2, History } from 'lucide-react'
import type { Metadata } from 'next'
import Link from 'next/link'

import { PageHeader } from '@/components/page-header'
import { StatusPill } from '@/components/status-pill'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { formatDate } from '@/lib/format'
import { getOagfRevisionCases } from '@/lib/oagf-revision-api'

export const metadata: Metadata = { title: 'OAGF official revisions' }
export const dynamic = 'force-dynamic'

export default async function OagfRevisionQueuePage() {
  const result = await getOagfRevisionCases()
  const cases = result.data ?? []
  const investigation = cases.filter((item) => item.status === 'investigation_required').length
  const pending = cases.filter((item) => item.status === 'pending_review').length

  return (
    <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
      <PageHeader
        eyebrow="OAGF source integrity"
        title="Official OAGF revisions"
        description="Changed official FAAC source bytes are retained as new immutable versions and queued here. Detection never overwrites published fiscal evidence."
      />

      <div className="mt-8 grid gap-4 md:grid-cols-3">
        <Card><CardHeader><History className="text-primary size-5" /><CardTitle className="pt-3 text-2xl">{cases.length}</CardTitle><CardDescription>Open revision cases</CardDescription></CardHeader></Card>
        <Card><CardHeader><CheckCircle2 className="text-primary size-5" /><CardTitle className="pt-3 text-2xl">{pending}</CardTitle><CardDescription>Awaiting classification</CardDescription></CardHeader></Card>
        <Card><CardHeader><AlertTriangle className="size-5 text-amber-700" /><CardTitle className="pt-3 text-2xl">{investigation}</CardTitle><CardDescription>Investigation / republication required</CardDescription></CardHeader></Card>
      </div>

      {result.error ? (
        <Card className="mt-8 border-dashed"><CardContent className="pt-6"><p className="font-medium">Revision service unavailable</p><p className="text-muted-foreground mt-2 text-sm">{result.error}</p></CardContent></Card>
      ) : cases.length ? (
        <div className="mt-8 space-y-4">
          {cases.map((item) => (
            <Card key={item.id}>
              <CardHeader>
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div><CardTitle>{item.reporting_label ?? item.title}</CardTitle><CardDescription className="mt-2">Detected {new Intl.DateTimeFormat('en-NG', { dateStyle: 'medium', timeStyle: 'short', timeZone: 'UTC' }).format(new Date(item.detected_at))} UTC{item.revenue_month ? ` · reporting period ${formatDate(item.revenue_month)}` : ''}</CardDescription></div>
                  <StatusPill tone={item.status === 'pending_review' ? 'neutral' : 'warning'}>{item.status.replaceAll('_', ' ')}</StatusPill>
                </div>
              </CardHeader>
              <CardContent>
                <dl className="grid gap-4 text-sm md:grid-cols-3">
                  <div><dt className="text-muted-foreground">Version change</dt><dd className="mt-1 font-mono font-semibold">v{item.previous_version} → v{item.current_version}</dd></div>
                  <div><dt className="text-muted-foreground">Previous SHA</dt><dd className="mt-1 font-mono text-xs">{item.previous_sha256.slice(0, 16)}…</dd></div>
                  <div><dt className="text-muted-foreground">Current SHA</dt><dd className="mt-1 font-mono text-xs">{item.current_sha256.slice(0, 16)}…</dd></div>
                </dl>
                <div className="border-border mt-5 flex justify-end border-t pt-4"><Button asChild size="sm"><Link href={`/review/oagf-revisions/${item.id}`}>Open revision packet<ArrowRight className="size-4" /></Link></Button></div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <Card className="mt-8 border-dashed"><CardContent className="pt-6"><CheckCircle2 className="text-primary size-5" /><p className="mt-3 font-medium">No unresolved OAGF revisions</p><p className="text-muted-foreground mt-2 text-sm">A changed official historical PDF will appear here automatically after the revision monitor runs.</p></CardContent></Card>
      )}

      <Button asChild variant="outline" className="mt-8"><Link href="/review">Back to evidence control</Link></Button>
    </div>
  )
}
