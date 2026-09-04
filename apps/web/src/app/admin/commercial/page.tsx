import type { Metadata } from 'next'
import Link from 'next/link'

import { PageHeader } from '@/components/page-header'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { getCommercialAnalytics } from '@/lib/commercial-api'

export const metadata: Metadata = { title: 'Commercial analytics' }
export const dynamic = 'force-dynamic'

function naira(value: string) {
  const amount = Number(value)
  if (!Number.isFinite(amount)) return `₦${value}`
  return new Intl.NumberFormat('en-NG', {
    style: 'currency',
    currency: 'NGN',
    maximumFractionDigits: 2,
  }).format(amount)
}

function Metric({ label, value, note }: { label: string; value: string | number; note?: string }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-muted-foreground text-xs font-semibold tracking-wide uppercase">
          {label}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-3xl font-semibold tracking-tight">{value}</p>
        {note ? <p className="text-muted-foreground mt-2 text-xs leading-5">{note}</p> : null}
      </CardContent>
    </Card>
  )
}

export default async function CommercialAnalyticsPage() {
  const result = await getCommercialAnalytics()
  const data = result.data

  return (
    <div className="gaia-shell py-12 lg:py-16">
      <PageHeader
        eyebrow="Commercial operations"
        title="Factual commercial analytics"
        description="Production metrics calculated only from persisted Gaia customer, subscription, payment, product-workflow and first-party event records."
      />

      <div className="mt-6 flex flex-wrap gap-3">
        <Button asChild variant="outline"><Link href="/admin/leads">Open lead pipeline</Link></Button>
        <Button asChild variant="outline"><Link href="/pricing">Open pricing</Link></Button>
      </div>

      {!data ? (
        <p className="text-destructive mt-10 text-sm font-medium">
          {result.error ?? 'Commercial analytics are unavailable.'}
        </p>
      ) : (
        <>
          <section className="mt-10 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <Metric label="Signups" value={data.signups_total} note={`${data.active_users_total} active users`} />
            <Metric label="Active paid organizations" value={data.active_subscriptions_total} note={Object.entries(data.active_subscriptions_by_plan).map(([plan, count]) => `${plan} ${count}`).join(' · ') || 'No active paid plans'} />
            <Metric label="Configured MRR" value={naira(data.configured_mrr_naira)} note="Active canonical subscriptions × configured Paystack plan price; not booked revenue." />
            <Metric label="Verified payment revenue" value={naira(data.successful_payment_revenue_naira)} note={`${data.successful_payment_count} successful · ${data.failed_payment_count} failed`} />
            <Metric label="Institutional leads" value={data.leads_total} note={Object.entries(data.leads_by_status).map(([stage, count]) => `${stage.replaceAll('_', ' ')} ${count}`).join(' · ') || 'No leads'} />
            <Metric label="Won lead conversion" value={data.won_lead_conversion_rate_pct === null ? 'Unavailable' : `${data.won_lead_conversion_rate_pct.toFixed(2)}%`} note="Won leads ÷ stored institutional leads." />
            <Metric label="Decision Rooms" value={data.decision_rooms_total} />
            <Metric label="Fiscal Receipts" value={data.fiscal_receipts_total} />
            <Metric label="Watchlists" value={data.watchlists_total} />
            <Metric label="Watch Contracts" value={data.watch_contracts_total} />
            <Metric label="API requests" value={data.api_requests_total} />
            <Metric label="Exports · 30d" value={data.exports_total} note="Counts only export_generated first-party events currently recorded." />
            <Metric label="Expired / canceled subscriptions" value={data.expired_or_canceled_subscriptions} />
            <Metric label="One-time purchases" value={data.one_time_purchases ?? 'Unavailable'} note={data.one_time_purchase_note} />
          </section>

          <section className="mt-8 grid gap-5 lg:grid-cols-2">
            <Card>
              <CardHeader><CardTitle>Plan distribution</CardTitle></CardHeader>
              <CardContent className="space-y-3 text-sm">
                {Object.entries(data.active_subscriptions_by_plan).length ? Object.entries(data.active_subscriptions_by_plan).map(([plan, count]) => (
                  <div key={plan} className="border-border flex items-center justify-between border-b pb-2 last:border-0">
                    <span className="capitalize">{plan}</span><strong>{count}</strong>
                  </div>
                )) : <p className="text-muted-foreground">No active paid subscriptions.</p>}
              </CardContent>
            </Card>
            <Card>
              <CardHeader><CardTitle>First-party funnel events · 30 days</CardTitle></CardHeader>
              <CardContent className="space-y-3 text-sm">
                {Object.entries(data.events_last_30_days).length ? Object.entries(data.events_last_30_days).sort(([a], [b]) => a.localeCompare(b)).map(([event, count]) => (
                  <div key={event} className="border-border flex items-center justify-between gap-4 border-b pb-2 last:border-0">
                    <span className="font-mono text-xs">{event}</span><strong>{count}</strong>
                  </div>
                )) : <p className="text-muted-foreground">No first-party commercial events recorded in the last 30 days.</p>}
              </CardContent>
            </Card>
          </section>

          <p className="text-muted-foreground mt-8 max-w-4xl text-xs leading-5">{data.statement}</p>
        </>
      )}
    </div>
  )
}
