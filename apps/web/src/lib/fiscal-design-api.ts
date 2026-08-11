import { z } from 'zod'

const metricSchema = z.object({
  label: z.string(),
  value: z.string(),
  unit: z.string(),
})

const candidateSchema = z.object({
  key: z.string(),
  title: z.string(),
  purpose: z.string(),
  status: z.enum(['available', 'insufficient_data']),
  metrics: z.array(metricSchema),
  note: z.string(),
})

const evidenceSchema = z.object({
  evidence_domain: z.enum(['faac', 'igr']),
  label: z.string(),
  value: z.string(),
  source_organization: z.string(),
  source_sha256: z.string().length(64),
  reference_path: z.string(),
})

export const fiscalDesignSchema = z.object({
  design_version: z.string(),
  state_name: z.string(),
  state_slug: z.string(),
  state_code: z.string(),
  year: z.number().int(),
  objective: z.string(),
  coverage_label: z.string(),
  faac_months_published: z.number().int(),
  faac_complete_year: z.boolean(),
  annual_igr_available: z.boolean(),
  faac_shock_pct: z.string(),
  igr_shock_pct: z.string(),
  reserve_share_pct: z.string(),
  assumptions: z.array(z.string()),
  evidence: z.array(evidenceSchema),
  candidates: z.array(candidateSchema),
  disclaimer: z.string(),
})

export type FiscalDesign = z.infer<typeof fiscalDesignSchema>

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

export async function getFiscalDesign(
  stateSlug: string,
  year: number,
  faacShock: number,
  igrShock: number,
  reserveShare: number,
): Promise<ApiResult<FiscalDesign>> {
  const params = new URLSearchParams({
    year: String(year),
    faac_shock_pct: String(faacShock),
    igr_shock_pct: String(igrShock),
    reserve_share_pct: String(reserveShare),
  })

  try {
    const response = await fetch(
      `${apiBaseUrl()}/api/v1/published/fiscal-design/${encodeURIComponent(stateSlug)}?${params.toString()}`,
      { next: { revalidate: 300 } },
    )
    if (!response.ok) {
      return { data: null, error: 'Fiscal Design Lab is unavailable for this selection.' }
    }
    return {
      data: fiscalDesignSchema.parse(await response.json()),
      error: null,
    }
  } catch {
    return { data: null, error: 'Fiscal Design Lab is unavailable for this selection.' }
  }
}
