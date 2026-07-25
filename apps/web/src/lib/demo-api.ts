import type {
  DemoComparisonResponse,
  DemoOverviewResponse,
  DemoSourcesResponse,
  DemoStateDetailResponse,
  DemoStatesResponse,
} from '@gaiafaac/shared-types'
import { z } from 'zod'

const verificationStatus = z.enum([
  'pending',
  'automatically_validated',
  'requires_review',
  'human_verified',
  'rejected',
  'superseded',
])

const period = z.object({
  id: z.string(),
  reporting_label: z.string(),
  revenue_month: z.iso.date(),
  faac_meeting_date: z.iso.date().nullable(),
  publication_date: z.iso.date().nullable(),
  verification_status: verificationStatus,
  is_published: z.literal(false),
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
  verification_status: verificationStatus,
  source_document_id: z.string(),
  is_published: z.literal(false),
})

const stateSummary = z.object({
  name: z.string(),
  code: z.string(),
  slug: z.string(),
  geopolitical_zone: z.string(),
  capital: z.string(),
  has_demo_allocation: z.boolean(),
  demo_net_allocation: z.string().nullable(),
  verification_status: verificationStatus.nullable(),
})

const component = z.object({
  component_type: z.string(),
  component_name: z.string(),
  gross_amount: z.string().nullable(),
  deduction_amount: z.string().nullable(),
  net_amount: z.string().nullable(),
  reported_unit: z.string(),
})

const dataLabel = z.literal('DEMO DATA - NOT REAL FAAC DATA')

const overviewSchema = z.object({
  data_label: dataLabel,
  scope_note: z.string(),
  period,
  covered_states: z.number().int(),
  expected_states: z.number().int(),
  sample_gross_total: z.string().nullable(),
  sample_deductions_total: z.string().nullable(),
  sample_net_total: z.string().nullable(),
  allocations: z.array(allocation),
})

const statesSchema = z.object({
  data_label: dataLabel,
  period,
  states: z.array(stateSummary),
})

const stateDetailSchema = z.object({
  data_label: dataLabel,
  period,
  state: stateSummary,
  allocation: allocation.nullable(),
  components: z.array(component),
  unavailable_note: z.string().nullable(),
})

const comparisonSchema = z.object({
  data_label: dataLabel,
  scope_note: z.string(),
  period,
  states: z.array(stateDetailSchema),
})

const sourcesSchema = z.object({
  data_label: dataLabel,
  sources: z.array(
    z.object({
      id: z.string(),
      source_organization: z.string(),
      source_url: z.url().nullable(),
      original_filename: z.string(),
      sha256: z.string().length(64),
      mime_type: z.string(),
      publication_date: z.iso.date().nullable(),
      downloaded_at: z.string().nullable(),
      document_version: z.string(),
      source_status: z.string(),
      is_demo: z.literal(true),
    }),
  ),
})

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

async function fetchDemo<T>(
  path: string,
  schema: z.ZodType<T>,
): Promise<ApiResult<T>> {
  try {
    const response = await fetch(`${apiBaseUrl()}${path}`, {
      next: { revalidate: 300 },
    })
    if (!response.ok) {
      const body = (await response.json().catch(() => null)) as {
        detail?: unknown
      } | null
      return {
        data: null,
        error:
          typeof body?.detail === 'string'
            ? body.detail
            : response.status === 404
              ? 'The labelled demo dataset is not loaded.'
              : 'The demo-data service is unavailable.',
      }
    }
    return { data: schema.parse(await response.json()), error: null }
  } catch {
    return {
      data: null,
      error: 'The demo-data service is unavailable.',
    }
  }
}

export function getDemoOverview(): Promise<ApiResult<DemoOverviewResponse>> {
  return fetchDemo('/api/v1/overview/latest', overviewSchema)
}

export function getDemoStates(): Promise<ApiResult<DemoStatesResponse>> {
  return fetchDemo('/api/v1/states', statesSchema)
}

export function getDemoState(
  slug: string,
): Promise<ApiResult<DemoStateDetailResponse>> {
  return fetchDemo(`/api/v1/states/${encodeURIComponent(slug)}`, stateDetailSchema)
}

export function getDemoComparison(
  slugs: string[],
): Promise<ApiResult<DemoComparisonResponse>> {
  const query = new URLSearchParams()
  for (const slug of slugs) query.append('states', slug)
  return fetchDemo(`/api/v1/compare?${query.toString()}`, comparisonSchema)
}

export function getDemoSources(): Promise<ApiResult<DemoSourcesResponse>> {
  return fetchDemo('/api/v1/sources', sourcesSchema)
}
