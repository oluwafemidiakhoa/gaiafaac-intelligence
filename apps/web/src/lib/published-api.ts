import { z } from 'zod'

const period = z.object({
  id: z.string(),
  reporting_label: z.string(),
  revenue_month: z.iso.date(),
  faac_meeting_date: z.iso.date().nullable(),
  publication_date: z.iso.date().nullable(),
  published_at: z.string().nullable(),
})

const source = z.object({
  source_organization: z.string(),
  source_url: z.url().nullable(),
  original_filename: z.string(),
  sha256: z.string().length(64),
  publication_date: z.iso.date().nullable(),
})

const allocation = z.object({
  state_name: z.string(),
  state_code: z.string(),
  state_slug: z.string(),
  geopolitical_zone: z.string(),
  gross_total: z.string().nullable(),
  total_deductions: z.string().nullable(),
  net_allocation: z.string().nullable(),
  reported_unit: z.string(),
})

const publishedOverviewSchema = z.object({
  period,
  source,
  covered_states: z.number().int(),
  expected_states: z.number().int(),
  total_gross: z.string().nullable(),
  total_deductions: z.string().nullable(),
  total_net: z.string().nullable(),
  allocations: z.array(allocation),
})

export type PublishedOverview = z.infer<typeof publishedOverviewSchema>

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

export async function getPublishedOverview(): Promise<ApiResult<PublishedOverview>> {
  try {
    const response = await fetch(
      `${apiBaseUrl()}/api/v1/published/overview/latest`,
      { next: { revalidate: 300 } },
    )
    if (!response.ok) {
      return {
        data: null,
        error:
          response.status === 404
            ? 'No published FAAC data is available yet.'
            : 'The published-data service is unavailable.',
      }
    }
    return {
      data: publishedOverviewSchema.parse(await response.json()),
      error: null,
    }
  } catch {
    return { data: null, error: 'The published-data service is unavailable.' }
  }
}
