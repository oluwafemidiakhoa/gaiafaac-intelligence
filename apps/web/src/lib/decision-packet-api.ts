import { z } from 'zod'

const monthSchema = z.object({
  revenue_month: z.iso.date(),
  reporting_label: z.string(),
  gross_total: z.string().nullable(),
  total_deductions: z.string().nullable(),
  net_allocation: z.string().nullable(),
  reconciliation_status: z.string(),
  proof_id: z.string(),
  proof_path: z.string(),
  source_organization: z.string(),
  source_sha256: z.string(),
  human_verified: z.boolean(),
})

const watchEventSchema = z.object({
  kind: z.string(),
  severity: z.string(),
  headline: z.string(),
  detail: z.string(),
  proof_path: z.string(),
})

const igrRecordSchema = z.object({
  fiscal_year: z.number().int(),
  period_type: z.string(),
  quarter: z.number().int().nullable(),
  period_start: z.iso.date(),
  period_end: z.iso.date(),
  igr_amount: z.string(),
  reported_unit: z.string(),
  source_organization: z.string(),
  source_sha256: z.string().length(64),
  human_verified: z.boolean(),
})

export const decisionPacketSchema = z.object({
  packet_version: z.string(),
  state_name: z.string(),
  state_slug: z.string(),
  state_code: z.string(),
  geopolitical_zone: z.string(),
  year: z.number().int(),
  coverage_label: z.string(),
  months_published: z.number().int(),
  annual_gross: z.string().nullable(),
  annual_deductions: z.string().nullable(),
  annual_net: z.string().nullable(),
  deduction_burden_pct: z.number().nullable(),
  net_retention_pct: z.number().nullable(),
  momentum: z.string(),
  momentum_pct: z.number().nullable(),
  volatility: z.string(),
  volatility_cv_pct: z.number().nullable(),
  evidence_status: z.string(),
  igr_records: z.array(igrRecordSchema),
  igr_note: z.string(),
  watch_events: z.array(watchEventSchema),
  months: z.array(monthSchema),
  disclaimer: z.string(),
})

export type DecisionPacket = z.infer<typeof decisionPacketSchema>

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

export async function getDecisionPacket(
  stateSlug: string,
  year: number,
): Promise<ApiResult<DecisionPacket>> {
  try {
    const response = await fetch(
      `${apiBaseUrl()}/api/v1/published/decision-packet/${encodeURIComponent(stateSlug)}?year=${year}`,
      { next: { revalidate: 300 } },
    )
    if (!response.ok) {
      return { data: null, error: 'Decision Packet is unavailable.' }
    }
    return {
      data: decisionPacketSchema.parse(await response.json()),
      error: null,
    }
  } catch {
    return { data: null, error: 'Decision Packet is unavailable.' }
  }
}
