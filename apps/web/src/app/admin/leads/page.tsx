import type { Metadata } from 'next'

import { PageHeader } from '@/components/page-header'
import { getPilotLeads } from '@/lib/commercial-api'

export const metadata: Metadata = { title: 'Commercial leads' }
export const dynamic = 'force-dynamic'

function displayDate(value: string) {
  return new Intl.DateTimeFormat('en-US', {
    dateStyle: 'medium',
    timeStyle: 'short',
    timeZone: 'America/Chicago',
  }).format(new Date(value))
}

export default async function CommercialLeadsPage() {
  const result = await getPilotLeads()
  const leads = result.data ?? []

  return (
    <div className="mx-auto max-w-7xl px-5 py-12 lg:px-8 lg:py-16">
      <PageHeader
        eyebrow="Commercial operations"
        title="Pilot enquiries"
        description="Private lead inbox for Analyst, Team, and API pilot requests."
      />

      {result.error ? (
        <p className="text-destructive mt-10 text-sm font-medium">
          {result.error}
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
                    {lead.plan_interest} pilot
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
                    <a
                      className="hover:underline"
                      href={`mailto:${lead.email}`}
                    >
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
                  <dt className="text-muted-foreground">Status</dt>
                  <dd className="mt-1 font-medium capitalize">{lead.status}</dd>
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
            </article>
          ))}
        </div>
      )}
    </div>
  )
}
