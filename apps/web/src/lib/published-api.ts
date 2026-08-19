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

export async function getPublishedOverview(): Promise<
  ApiResult<PublishedOverview>
> {
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

export const publishedSourceSchema = z.object({
  revenue_month: z.iso.date(),
  reporting_label: z.string(),
  source_organization: z.string(),
  original_filename: z.string(),
  sha256: z.string().length(64),
  source_url: z.url().nullable(),
  publication_date: z.iso.date().nullable(),
  covered_states: z.number().int(),
  expected_states: z.number().int(),
})

export type PublishedSourceItem = z.infer<typeof publishedSourceSchema>

export async function getPublishedSources(): Promise<
  ApiResult<PublishedSourceItem[]>
> {
  try {
    const response = await fetch(`${apiBaseUrl()}/api/v1/published/sources`, {
      next: { revalidate: 300 },
    })
    if (!response.ok) {
      return { data: null, error: 'The source registry is unavailable.' }
    }
    return {
      data: z.array(publishedSourceSchema).parse(await response.json()),
      error: null,
    }
  } catch {
    return { data: null, error: 'The source registry is unavailable.' }
  }
}

const nationalObservedValueSchema = z.object({
  value: z.string().nullable(),
  evidence_class: z.enum(['observed', 'derived', 'conflicted', 'missing']),
})

const nationalReconciliationSchema = z.object({
  status: z.enum(['reconciled', 'conflicted', 'incomplete', 'unavailable']),
  observed_total: z.string().nullable(),
  derived_total: z.string().nullable(),
  variance: z.string().nullable(),
  tolerance: z.string().nullable(),
  evidence_class: z.enum(['observed', 'derived', 'conflicted', 'missing']),
  basis: z.string(),
  note: z.string(),
})

export const publishedNationalDistributionSchema = z.object({
  reporting_period_id: z.string(),
  reporting_label: z.string(),
  revenue_month: z.iso.date(),
  disbursement_month: z.iso.date(),
  allocation_period_month: z.iso.date().nullable(),
  published_at: z.string().nullable(),
  verification_status: z.string(),
  reported_unit: z.string(),
  derivation_treatment: z.string(),
  states_scope: z.string(),
  canonical_source_status: z.enum([
    'available',
    'missing',
    'superseded',
    'conflicted',
  ]),
  covered_jurisdictions: z.number().int(),
  expected_jurisdictions: z.number().int(),
  source: z.object({
    source_organization: z.string(),
    source_url: z.string().nullable(),
    original_filename: z.string(),
    sha256: z.string().length(64),
    publication_date: z.iso.date().nullable(),
    document_version: z.string(),
    source_type: z.enum([
      'canonical_national_evidence',
      'official_national_summary_evidence',
      'official_government_press_release',
    ]),
    source_authority: z.enum(['canonical', 'official_secondary', 'contextual']),
  }),
  net_distributable_amount: nationalObservedValueSchema,
  federal_amount: nationalObservedValueSchema,
  states_amount: nationalObservedValueSchema,
  local_governments_amount: nationalObservedValueSchema,
  derivation_amount: nationalObservedValueSchema,
  vat_amount: nationalObservedValueSchema,
  statutory_amount: nationalObservedValueSchema,
  component_reconciliation: nationalReconciliationSchema,
  jurisdiction_reconciliation: nationalReconciliationSchema,
})

export type PublishedNationalDistribution = z.infer<
  typeof publishedNationalDistributionSchema
>

export async function getPublishedNationalDistributions(): Promise<
  ApiResult<PublishedNationalDistribution[]>
> {
  try {
    const response = await fetch(
      `${apiBaseUrl()}/api/v1/published/national-distribution/history?limit=24`,
      { next: { revalidate: 300 } },
    )
    if (!response.ok) {
      return { data: null, error: 'The national evidence registry is unavailable.' }
    }
    return {
      data: z
        .array(publishedNationalDistributionSchema)
        .parse(await response.json()),
      error: null,
    }
  } catch {
    return {
      data: null,
      error: 'The national evidence registry is unavailable.',
    }
  }
}

const publishedIgrSourceSchema = z.object({
  organization: z.string(),
  source_url: z.url().nullable(),
  sha256: z.string().length(64),
  publication_date: z.iso.date().nullable(),
})

export const publishedIgrRecordSchema = z.object({
  state_name: z.string(),
  state_slug: z.string(),
  state_code: z.string(),
  fiscal_year: z.number().int(),
  period_type: z.enum(['annual', 'quarterly']),
  quarter: z.number().int().nullable(),
  period_start: z.iso.date(),
  period_end: z.iso.date(),
  igr_amount: z.string(),
  reported_unit: z.string(),
  source_page: z.number().int().nullable(),
  source_table: z.string().nullable(),
  verification_status: z.string(),
  source: publishedIgrSourceSchema,
})

export type PublishedIgrRecord = z.infer<typeof publishedIgrRecordSchema>

export async function getLatestPublishedIgr(
  stateSlug: string,
): Promise<ApiResult<PublishedIgrRecord>> {
  try {
    const response = await fetch(
      `${apiBaseUrl()}/api/v1/published/igr/latest?state_slug=${encodeURIComponent(stateSlug)}`,
      { next: { revalidate: 300 } },
    )
    if (!response.ok) {
      return {
        data: null,
        error:
          response.status === 404
            ? 'No published IGR evidence is available for this state yet.'
            : 'The IGR evidence service is unavailable.',
      }
    }
    return {
      data: publishedIgrRecordSchema.parse(await response.json()),
      error: null,
    }
  } catch {
    return { data: null, error: 'The IGR evidence service is unavailable.' }
  }
}
