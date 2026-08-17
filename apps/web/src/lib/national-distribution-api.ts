import { z } from 'zod'

const observedValue = z.object({
  value: z.string().nullable(),
  evidence_class: z.enum(['observed', 'derived', 'conflicted', 'missing']),
})

const reconciliation = z.object({
  status: z.enum(['reconciled', 'conflicted', 'incomplete', 'unavailable']),
  observed_total: z.string().nullable(),
  derived_total: z.string().nullable(),
  variance: z.string().nullable(),
  tolerance: z.string().nullable(),
  evidence_class: z.enum(['observed', 'derived', 'conflicted', 'missing']),
  basis: z.string(),
  note: z.string(),
})

export const nationalDistributionSchema = z.object({
  reporting_period_id: z.string(),
  reporting_label: z.string(),
  revenue_month: z.iso.date(),
  disbursement_month: z.iso.date().nullable().optional(),
  allocation_period_month: z.iso.date().nullable().optional(),
  published_at: z.string().nullable(),
  verification_status: z.string(),
  reported_unit: z.string(),
  derivation_treatment: z.string(),
  states_scope: z.string(),
  canonical_source_status: z
    .enum(['available', 'missing', 'superseded', 'conflicted'])
    .default('available'),
  covered_jurisdictions: z.number().int(),
  expected_jurisdictions: z.number().int(),
  source: z.object({
    source_organization: z.string(),
    source_url: z.string().nullable(),
    original_filename: z.string(),
    sha256: z.string().length(64),
    publication_date: z.iso.date().nullable(),
    document_version: z.string(),
    source_type: z
      .enum([
        'canonical_national_evidence',
        'official_national_summary_evidence',
        'official_government_press_release',
      ])
      .default('canonical_national_evidence'),
    source_authority: z
      .enum(['canonical', 'official_secondary', 'contextual'])
      .default('canonical'),
  }),
  net_distributable_amount: observedValue,
  federal_amount: observedValue,
  states_amount: observedValue,
  local_governments_amount: observedValue,
  derivation_amount: observedValue,
  vat_amount: observedValue,
  statutory_amount: observedValue,
  component_reconciliation: reconciliation,
  jurisdiction_reconciliation: reconciliation,
})

export type NationalDistribution = z.infer<typeof nationalDistributionSchema>

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

export async function getLatestNationalDistribution(): Promise<{
  data: NationalDistribution | null
  error: string | null
}> {
  try {
    const response = await fetch(
      `${apiBaseUrl()}/api/v1/published/national-distribution/latest`,
      { next: { revalidate: 300 } },
    )
    if (response.status === 404) {
      return { data: null, error: null }
    }
    if (!response.ok) {
      return { data: null, error: 'National reconciliation is unavailable.' }
    }
    return {
      data: nationalDistributionSchema.parse(await response.json()),
      error: null,
    }
  } catch {
    return { data: null, error: 'National reconciliation is unavailable.' }
  }
}

export async function getNationalDistributionHistory(limit = 12): Promise<{
  data: NationalDistribution[] | null
  error: string | null
}> {
  try {
    const response = await fetch(
      `${apiBaseUrl()}/api/v1/published/national-distribution/history?limit=${limit}`,
      { next: { revalidate: 300 } },
    )
    if (!response.ok) {
      return {
        data: null,
        error: 'National reconciliation history is unavailable.',
      }
    }
    return {
      data: z.array(nationalDistributionSchema).parse(await response.json()),
      error: null,
    }
  } catch {
    return {
      data: null,
      error: 'National reconciliation history is unavailable.',
    }
  }
}
