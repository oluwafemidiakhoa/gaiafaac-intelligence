import { z } from 'zod'

const fiscalProofSchema = z.object({
  proof_version: z.literal('1'),
  proof_id: z.string(),
  proof_digest_sha256: z.string().length(64),
  claim: z.string(),
  state_name: z.string(),
  state_slug: z.string(),
  state_code: z.string(),
  geopolitical_zone: z.string(),
  revenue_month: z.iso.date(),
  reporting_label: z.string(),
  financials: z.object({
    gross_total: z.string().nullable(),
    total_deductions: z.string().nullable(),
    net_allocation: z.string().nullable(),
    reported_unit: z.string(),
    reconciliation_status: z.enum(['reconciled', 'not_applicable', 'mismatch']),
    reconciliation_delta: z.string().nullable(),
  }),
  source: z.object({
    source_organization: z.string(),
    source_url: z.string().nullable(),
    original_filename: z.string(),
    sha256: z.string().length(64),
    publication_date: z.iso.date().nullable(),
    document_version: z.string(),
  }),
  verification: z.object({
    allocation_status: z.string(),
    period_status: z.string(),
    source_status: z.string(),
    reviewed_at: z.string().nullable(),
    published_at: z.string().nullable(),
    human_verified: z.boolean(),
  }),
  disclaimer: z.string(),
})

export type FiscalProof = z.infer<typeof fiscalProofSchema>

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

export async function getFiscalProof(stateSlug: string, revenueMonth: string) {
  try {
    const response = await fetch(
      `${apiBaseUrl()}/api/v1/published/fiscal-proof/${encodeURIComponent(stateSlug)}/${revenueMonth}`,
      { next: { revalidate: 300 } },
    )
    if (!response.ok) {
      return { data: null, error: 'Fiscal Proof is unavailable.' }
    }
    return { data: fiscalProofSchema.parse(await response.json()), error: null }
  } catch {
    return { data: null, error: 'Fiscal Proof is unavailable.' }
  }
}
