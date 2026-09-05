import { z } from 'zod'

const pilotLeadSchema = z.object({
  id: z.string().uuid(),
  name: z.string(),
  email: z.string(),
  organization: z.string().nullable(),
  role: z.string().nullable(),
  country: z.string().nullable(),
  plan_interest: z.string(),
  use_case: z.string(),
  states_or_periods: z.string().nullable(),
  requested_evidence_domains: z.string().nullable(),
  preferred_format: z.string().nullable(),
  expected_users: z.number().int().nullable(),
  buying_timeline: z.string().nullable(),
  source_page: z.string().nullable(),
  status: z.string(),
  source: z.string(),
  owner_name: z.string().nullable(),
  next_action: z.string().nullable(),
  next_action_at: z.string().nullable(),
  internal_notes: z.string().nullable(),
  closed_reason: z.string().nullable(),
  converted_organization_id: z.string().uuid().nullable(),
  status_changed_at: z.string().nullable(),
  created_at: z.string(),
  updated_at: z.string(),
})

const commercialAnalyticsSchema = z.object({
  generated_at: z.string(),
  signups_total: z.number().int(),
  active_users_total: z.number().int(),
  leads_total: z.number().int(),
  leads_by_status: z.record(z.string(), z.number().int()),
  leads_by_plan: z.record(z.string(), z.number().int()),
  won_lead_conversion_rate_pct: z.number().nullable(),
  active_subscriptions_total: z.number().int(),
  active_subscriptions_by_plan: z.record(z.string(), z.number().int()),
  configured_mrr_naira: z.string(),
  successful_payment_count: z.number().int(),
  successful_payment_revenue_naira: z.string(),
  failed_payment_count: z.number().int(),
  expired_or_canceled_subscriptions: z.number().int(),
  one_time_purchases: z.number().int().nullable(),
  one_time_purchase_note: z.string(),
  decision_rooms_total: z.number().int(),
  fiscal_receipts_total: z.number().int(),
  watchlists_total: z.number().int(),
  watch_contracts_total: z.number().int(),
  api_requests_total: z.number().int(),
  exports_total: z.number().int(),
  events_last_30_days: z.record(z.string(), z.number().int()),
  statement: z.string(),
})

export type PilotLead = z.infer<typeof pilotLeadSchema>
export type CommercialAnalytics = z.infer<typeof commercialAnalyticsSchema>

function apiBaseUrl() {
  return z
    .url()
    .parse(
      process.env.API_INTERNAL_URL ??
        process.env.NEXT_PUBLIC_API_URL ??
        'http://localhost:8000',
    )
    .replace(/\/$/, '')
}

function adminHeaders(extra: Record<string, string> = {}) {
  return {
    'X-Admin-Key': process.env.ADMIN_KEY ?? '',
    ...extra,
  }
}

export async function getPilotLeads(): Promise<{
  data: PilotLead[] | null
  error: string | null
}> {
  try {
    const response = await fetch(
      `${apiBaseUrl()}/api/v1/commercial/pilot-leads`,
      {
        cache: 'no-store',
        headers: adminHeaders(),
      },
    )
    if (!response.ok) {
      return { data: null, error: 'The commercial lead inbox is unavailable.' }
    }
    return {
      data: z.array(pilotLeadSchema).parse(await response.json()),
      error: null,
    }
  } catch {
    return { data: null, error: 'The commercial lead inbox is unavailable.' }
  }
}

export async function getCommercialAnalytics(): Promise<{
  data: CommercialAnalytics | null
  error: string | null
}> {
  try {
    const response = await fetch(
      `${apiBaseUrl()}/api/v1/commercial/analytics`,
      {
        cache: 'no-store',
        headers: adminHeaders(),
      },
    )
    if (!response.ok) {
      return { data: null, error: 'Commercial analytics are unavailable.' }
    }
    return {
      data: commercialAnalyticsSchema.parse(await response.json()),
      error: null,
    }
  } catch {
    return { data: null, error: 'Commercial analytics are unavailable.' }
  }
}

export async function updatePilotLead(
  leadId: string,
  payload: {
    status?: string
    requested_evidence_domains?: string | null
    buying_timeline?: string | null
    source_page?: string | null
    owner_name?: string | null
    next_action?: string | null
    next_action_at?: string | null
    internal_notes?: string | null
    closed_reason?: string | null
  },
): Promise<{ ok: boolean; error: string | null }> {
  try {
    const response = await fetch(
      `${apiBaseUrl()}/api/v1/commercial/pilot-leads/${encodeURIComponent(leadId)}`,
      {
        method: 'PATCH',
        cache: 'no-store',
        headers: adminHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify(payload),
      },
    )
    if (!response.ok) {
      return { ok: false, error: 'The lead could not be updated.' }
    }
    pilotLeadSchema.parse(await response.json())
    return { ok: true, error: null }
  } catch {
    return { ok: false, error: 'The lead could not be updated.' }
  }
}
