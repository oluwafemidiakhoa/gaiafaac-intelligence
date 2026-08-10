import { z } from 'zod'

const fiscalWatchEventSchema = z.object({
  kind: z.enum([
    'negative_net',
    'large_monthly_move',
    'high_deduction_burden',
  ]),
  severity: z.enum(['watch', 'elevated']),
  state_name: z.string(),
  state_slug: z.string(),
  state_code: z.string(),
  revenue_month: z.iso.date(),
  headline: z.string(),
  detail: z.string(),
  current_net: z.string().nullable(),
  previous_net: z.string().nullable(),
  change_pct: z.number().nullable(),
  deduction_burden_pct: z.number().nullable(),
  proof_path: z.string(),
})

export const fiscalWatchSchema = z.object({
  year: z.number().int(),
  latest_revenue_month: z.iso.date().nullable(),
  previous_revenue_month: z.iso.date().nullable(),
  event_count: z.number().int(),
  events: z.array(fiscalWatchEventSchema),
  note: z.string(),
})

export type FiscalWatch = z.infer<typeof fiscalWatchSchema>
export type FiscalWatchEvent = z.infer<typeof fiscalWatchEventSchema>

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

export async function getFiscalWatch(
  year: number,
): Promise<ApiResult<FiscalWatch>> {
  try {
    const response = await fetch(
      `${apiBaseUrl()}/api/v1/published/fiscal-watch?year=${year}`,
      { next: { revalidate: 300 } },
    )
    if (!response.ok) {
      return { data: null, error: 'Fiscal Watch is unavailable.' }
    }
    return { data: fiscalWatchSchema.parse(await response.json()), error: null }
  } catch {
    return { data: null, error: 'Fiscal Watch is unavailable.' }
  }
}
