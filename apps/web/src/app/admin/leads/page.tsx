import type { Metadata } from 'next'

import { PageHeader } from '@/components/page-header'
import { getCommercialAnalytics, getPilotLeads } from '@/lib/commercial-api'

import { updateLeadAction } from './actions'

export const metadata: Metadata = { title: 'Commercial operations' }
export const dynamic = 'force-dynamic'

const LEAD_STAGES = [
  'new',
  'contacted',
  'qualified',
  'pilot',
  'proposal',
  'won',
  'lost',
] as const

function displayDate(value: string | null) {
  if (!value) return 'Not scheduled'
  return new Intl.DateTimeFormat('en-US', {
    dateStyle: 'medium',
    timeStyle: 'short',
    timeZone: 'America/Chicago',
  }).format(new Date(value))
}

function naira(value: string) {
  const amount = Number(value)
  if (!Number.isFinite(amount)) return `₦${value}`
  return new Intl.NumberFormat('en-NG', {
    style: 'currency',
    currency: 'NGN',
    maximumFractionDigits: 2,
  }).format(amount)
}

export default async function CommercialLeadsPage() {
  const [leadResult, analyticsResult] = await Promise.all([
    getPilotLeads(),
    getCommercialAnalytics(),
  ])
  const leads = leadResult.data ?? []
  const analytics = analyticsResult.data

  return (
    <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
      <PageHeader
        eyebrow="Commercial operations"
        title="Revenue control plane"
        description="Authorized lead workflow and first-party commercial metrics computed from persisted Gaia records only."
      />

      {analytics ? (
        <section className="mt-10 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <div className="border-border rounded-xl border p-5">
            <p className="text-muted-foreground text-xs font-semibold tracking-wide uppercase">
              Leads
            </p>
            <p className="mt-2 text-3xl font-semibold">{analytics.leads_total}</p>
            <p className="text-muted-foreground mt-2 text-xs">
              {Object.entries(analytics.leads_by_status)
                .map(([stage, count]) => `${stage} ${count}`)
                .join(' · ') || 'No lead stages yet'}
            </p>
          </div>
          <div className="border-border rounded-xl border p-5">
            <p className="text-muted-foreground text-xs font-semibold tracking-wide uppercase">
              Active paid organizations
            </p>
            <p className="mt-2 text-3xl font-semibold">
              {analytics.active_subscriptions_total}
            </p>
            <p className="text-muted-foreground mt-2 text-xs">
              {Object.entries(analytics.active_subscriptions_by_plan)
                .map(([plan, count]) => `${plan} ${count}`)
                .join(' · ') || 'No active paid subscriptions'}
            </p>
          </div>
          <div className="border-border rounded-xl border p-5">
            <p className="text-muted-foreground text-xs font-semibold tracking-wide uppercase">
              Verified payment revenue
            </p>
            <p className="mt-2 text-3xl font-semibold">
              {naira(analytics.successful_payment_revenue_naira)}
            </p>
            <p className="text-muted-foreground mt-2 text-xs">
              {analytics.successful_payment_count} successful payment
              {analytics.successful_payment_count === 1 ? '' : 's'}
            </p>
          </div>
          <div className="border-border rounded-xl border p-5">
            <p className="text-muted-foreground text-xs font-semibold tracking-wide uppercase">
              First-party events · 30d
            </p>
            <p className="mt-2 text-3xl font-semibold">
              {Object.values(analytics.events_last_30_days).reduce(
                (total, count) => total + count,
                0,
              )}
            </p>
            <p className="text-muted-foreground mt-2 text-xs">
              No device IDs, fingerprinting or third-party analytics.
            </p>
          </div>
          <p className="text-muted-foreground sm:col-span-2 xl:col-span-4 text-xs">
            {analytics.statement}
          </p>
        </section>
      ) : analyticsResult.error ? (
        <p className="text-destructive mt-10 text-sm font-medium">
          {analyticsResult.error}
        </p>
      ) : null}

      {leadResult.error ? (
        <p className="text-destructive mt-10 text-sm font-medium">
          {leadResult.error}
        </p>
      ) : leads.length === 0 ? (
        <p className="text-muted-foreground mt-10 text-sm">
          No pilot enquiries have been submitted yet.
        </p>
      ) : (
        <div className="mt-10 space-y-5">
          <p className="text-muted-foreground text-sm">
            {leads.length} lead{leads.length === 1 ? '' : 's'}, newest first.
          </p>
          {leads.map((lead) => (
            <article
              key={lead.id}
              className="border-border rounded-lg border p-6"
            >
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <h2 className="text-xl font-semibold">{lead.name}</h2>
                  <p className="text-muted-foreground mt-1 text-sm">
                    {lead.organization ?? 'Independent'}
                    {lead.role ? ` · ${lead.role}` : ''}
                    {lead.country ? ` · ${lead.country}` : ''}
                  </p>
                </div>
                <div className="text-right text-sm">
                  <p className="font-medium capitalize">
                    {lead.plan_interest} · {lead.status}
                  </p>
                  <p className="text-muted-foreground mt-1">
                    {displayDate(lead.created_at)}
                  </p>
                </div>
              </div>

              <dl className="mt-6 grid gap-5 text-sm sm:grid-cols-2 lg:grid-cols-4">
                <div>
                  <dt className="text-muted-foreground">Email</dt>
                  <dd className="mt-1 font-medium">
                    <a className="hover:underline" href={`mailto:${lead.email}`}>
                      {lead.email}
                    </a>
                  </dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Format</dt>
                  <dd className="mt-1 font-medium">
                    {lead.preferred_format ?? 'Not specified'}
                  </dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Expected users</dt>
                  <dd className="mt-1 font-medium">
                    {lead.expected_users ?? 'Not specified'}
                  </dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Next action</dt>
                  <dd className="mt-1 font-medium">
                    {lead.next_action ?? 'Not set'}
                  </dd>
                  <dd className="text-muted-foreground mt-1 text-xs">
                    {displayDate(lead.next_action_at)}
                  </dd>
                </div>
              </dl>

              <div className="mt-6 grid gap-5 lg:grid-cols-2">
                <div>
                  <h3 className="text-sm font-semibold">Use case</h3>
                  <p className="text-muted-foreground mt-2 text-sm leading-6 whitespace-pre-wrap">
                    {lead.use_case}
                  </p>
                </div>
                <div>
                  <h3 className="text-sm font-semibold">States or periods</h3>
                  <p className="text-muted-foreground mt-2 text-sm leading-6 whitespace-pre-wrap">
                    {lead.states_or_periods ?? 'Not specified'}
                  </p>
                </div>
              </div>

              <form
                action={updateLeadAction}
                className="bg-muted/20 mt-6 grid gap-3 rounded-xl border p-4 lg:grid-cols-5"
              >
                <input type="hidden" name="lead_id" value={lead.id} />
                <label className="grid gap-1 text-xs">
                  Stage
                  <select
                    name="status"
                    defaultValue={lead.status}
                    className="border-input bg-background h-10 rounded-md border px-3 text-sm capitalize"
                  >
                    {LEAD_STAGES.map((stage) => (
                      <option key={stage} value={stage}>
                        {stage}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="grid gap-1 text-xs">
                  Owner
                  <input
                    name="owner_name"
                    defaultValue={lead.owner_name ?? ''}
                    className="border-input bg-background h-10 rounded-md border px-3 text-sm"
                    placeholder="Commercial owner"
                  />
                </label>
                <label className="grid gap-1 text-xs lg:col-span-2">
                  Next action
                  <input
                    name="next_action"
                    defaultValue={lead.next_action ?? ''}
                    className="border-input bg-background h-10 rounded-md border px-3 text-sm"
                    placeholder="Schedule pilot scoping call"
                  />
                </label>
                <label className="grid gap-1 text-xs">
                  Due
                  <input
                    type="datetime-local"
                    name="next_action_at"
                    defaultValue={
                      lead.next_action_at
                        ? new Date(lead.next_action_at).toISOString().slice(0, 16)
                        : ''
                    }
                    className="border-input bg-background h-10 rounded-md border px-3 text-sm"
                  />
                </label>
                <label className="grid gap-1 text-xs lg:col-span-4">
                  Closed / loss reason
                  <input
                    name="closed_reason"
                    defaultValue={lead.closed_reason ?? ''}
                    className="border-input bg-background h-10 rounded-md border px-3 text-sm"
                    placeholder="Only required when useful to the commercial record"
                  />
                </label>
                <button
                  type="submit"
                  className="bg-primary text-primary-foreground h-10 self-end rounded-md px-4 text-sm font-medium"
                >
                  Save lead
                </button>
              </form>
            </article>
          ))}
        </div>
      )}
    </div>
  )
}
