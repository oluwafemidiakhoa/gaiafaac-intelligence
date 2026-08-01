import { z } from 'zod'

const trendPoint = z.object({
  revenue_month: z.iso.date(),
  reporting_label: z.string(),
  total_net: z.string(),
  covered_states: z.number().int(),
})

const rankedState = z.object({
  state_name: z.string(),
  state_slug: z.string(),
  state_code: z.string(),
  geopolitical_zone: z.string(),
  net_allocation: z.string(),
})

const mover = z.object({
  state_name: z.string(),
  state_slug: z.string(),
  previous_net: z.string(),
  current_net: z.string(),
  change: z.string(),
  pct_change: z.number(),
})

export const publishedAnalyticsSchema = z.object({
  months_published: z.number().int(),
  national_trend: z.array(trendPoint),
  latest_period_label: z.string().nullable(),
  top_states: z.array(rankedState),
  biggest_movers: z.array(mover),
  note: z.string(),
})

export type PublishedAnalytics = z.infer<typeof publishedAnalyticsSchema>

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

export async function getPublishedAnalytics(): Promise<
  ApiResult<PublishedAnalytics>
> {
  try {
    const response = await fetch(`${apiBaseUrl()}/api/v1/published/analytics`, {
      next: { revalidate: 300 },
    })
    if (!response.ok) {
      return { data: null, error: 'Analytics are unavailable.' }
    }
    return {
      data: publishedAnalyticsSchema.parse(await response.json()),
      error: null,
    }
  } catch {
    return { data: null, error: 'Analytics are unavailable.' }
  }
}
