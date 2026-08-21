import { z } from 'zod'

const analystEvidenceSchema = z.object({
  state_name: z.string().nullable(),
  state_slug: z.string().nullable(),
  label: z.string(),
  value: z.string(),
  metric: z.string(),
  reference_path: z.string().nullable(),
  reference_label: z.string().nullable(),
  evidence_domain: z.enum(['faac', 'igr', 'ledger']).default('faac'),
  period_label: z.string().nullable().optional(),
  source_organization: z.string().nullable().optional(),
  source_sha256: z.string().nullable().optional(),
  gaia_object_id: z.string().nullable().optional(),
  evidence_status: z.string().nullable().optional(),
  relevant_date: z.string().nullable().optional(),
})

const gaiaAnalystSchema = z.object({
  question: z.string(),
  year: z.number().int(),
  intent: z.enum([
    'latest_changes',
    'latest_state_net',
    'top_net',
    'lowest_net',
    'highest_deduction_burden',
    'most_volatile',
    'momentum',
    'compare',
    'igr_latest',
    'igr_state',
    'igr_top',
    'igr_lowest',
    'igr_compare',
    'ledger_metric',
    'temporal_metric',
    'unsupported',
  ]),
  status: z.enum(['answered', 'insufficient_data', 'unsupported']),
  answer: z.string(),
  coverage_label: z.string(),
  evidence: z.array(analystEvidenceSchema),
  caveat: z.string(),
  suggested_questions: z.array(z.string()),
})

export type GaiaAnalystResponse = z.infer<typeof gaiaAnalystSchema>

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

export async function askGaiaAnalyst(question: string, year: number) {
  try {
    const params = new URLSearchParams({ question, year: String(year) })
    const response = await fetch(
      `${apiBaseUrl()}/api/v1/published/gaia-analyst?${params.toString()}`,
      { cache: 'no-store' },
    )
    if (!response.ok) {
      return { data: null, error: 'Gaia Analyst is unavailable.' }
    }
    return {
      data: gaiaAnalystSchema.parse(await response.json()),
      error: null,
    }
  } catch {
    return { data: null, error: 'Gaia Analyst is unavailable.' }
  }
}
