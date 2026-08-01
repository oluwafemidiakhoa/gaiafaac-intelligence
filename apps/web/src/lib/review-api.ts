import { z } from 'zod'

export const pendingReviewSchema = z.object({
  run_id: z.string(),
  reporting_label: z.string(),
  revenue_month: z.iso.date(),
  source_organization: z.string(),
  status: z.string(),
  covered_states: z.number().int(),
  expected_states: z.number().int(),
  finding_count: z.number().int(),
  blocking_count: z.number().int(),
  created_at: z.string().nullable(),
})

export type PendingReviewItem = z.infer<typeof pendingReviewSchema>

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

export async function getPendingReviews(): Promise<
  ApiResult<PendingReviewItem[]>
> {
  try {
    const response = await fetch(`${apiBaseUrl()}/api/v1/review/pending`, {
      next: { revalidate: 120 },
      headers: { 'X-Admin-Key': process.env.ADMIN_KEY ?? '' },
    })
    if (!response.ok) {
      return { data: null, error: 'The review queue is unavailable.' }
    }
    return {
      data: z.array(pendingReviewSchema).parse(await response.json()),
      error: null,
    }
  } catch {
    return { data: null, error: 'The review queue is unavailable.' }
  }
}
