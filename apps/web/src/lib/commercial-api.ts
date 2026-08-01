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
  preferred_format: z.string().nullable(),
  expected_users: z.number().int().nullable(),
  status: z.string(),
  source: z.string(),
  created_at: z.string(),
})

export type PilotLead = z.infer<typeof pilotLeadSchema>

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

export async function getPilotLeads(): Promise<{
  data: PilotLead[] | null
  error: string | null
}> {
  try {
    const response = await fetch(
      `${apiBaseUrl()}/api/v1/commercial/pilot-leads`,
      {
        cache: 'no-store',
        headers: { 'X-Admin-Key': process.env.ADMIN_KEY ?? '' },
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
