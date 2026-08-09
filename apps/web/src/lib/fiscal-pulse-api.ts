import { z } from 'zod'

const fiscalPulseStateSchema = z.object({
  state_name: z.string(),
  state_slug: z.string(),
  state_code: z.string(),
  geopolitical_zone: z.string(),
  months_published: z.number().int(),
  months_with_net: z.number().int(),
  months_with_complete_financials: z.number().int(),
  annual_gross: z.string().nullable(),
  annual_deductions: z.string().nullable(),
  annual_net: z.string().nullable(),
  deduction_burden_pct: z.number().nullable(),
  net_retention_pct: z.number().nullable(),
  momentum: z.enum(['Improving', 'Stable', 'Weakening', 'Insufficient data']),
  momentum_pct: z.number().nullable(),
  volatility: z.enum(['Low', 'Moderate', 'High', 'Insufficient data']),
  volatility_cv_pct: z.number().nullable(),
  evidence_status: z.enum(['Verified', 'Partial', 'Review required']),
})

export const fiscalPulseSchema = z.object({
  year: z.number().int(),
  months_published: z.number().int(),
  expected_months: z.number().int(),
  coverage_status: z.enum(['complete_year', 'partial_year', 'no_data']),
  coverage_label: z.string(),
  latest_period_label: z.string().nullable(),
  total_net: z.string().nullable(),
  states: z.array(fiscalPulseStateSchema),
  note: z.string(),
})

export type FiscalPulse = z.infer<typeof fiscalPulseSchema>
export type FiscalPulseState = z.infer<typeof fiscalPulseStateSchema>

export interface ApiResult<T> {
  data: T | null
  error: string | null
}

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

export async function getFiscalPulse(
  year = 2024,
): Promise<ApiResult<FiscalPulse>> {
  try {
    const response = await fetch(
      `${apiBaseUrl()}/api/v1/published/fiscal-pulse?year=${year}`,
      { next: { revalidate: 300 } },
    )
    if (!response.ok) {
      return { data: null, error: 'Fiscal Pulse is unavailable.' }
    }
    return { data: fiscalPulseSchema.parse(await response.json()), error: null }
  } catch {
    return { data: null, error: 'Fiscal Pulse is unavailable.' }
  }
}
