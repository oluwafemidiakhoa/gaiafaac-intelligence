import { z } from 'zod'

const actorSchema = z.object({
  id: z.string(),
  full_name: z.string(),
  email: z.string(),
  role: z.enum(['reviewer', 'administrator']),
})

const pendingSchema = z.object({
  run_id: z.string(),
  distribution_id: z.string(),
  reporting_label: z.string(),
  disbursement_month: z.iso.date(),
  allocation_period_month: z.iso.date().nullable(),
  source_organization: z.string(),
  verification_status: z.string(),
  pipeline_status: z.string(),
  finding_count: z.number().int(),
  blocking_count: z.number().int(),
  approved: z.boolean(),
  approved_by: z.string().nullable(),
  created_at: z.string().nullable(),
})

const sourceSchema = z.object({
  source_organization: z.string(),
  source_url: z.string().nullable(),
  original_filename: z.string(),
  sha256: z.string().length(64),
  publication_date: z.iso.date().nullable(),
  source_type: z.string().nullable(),
  source_authority: z.string().nullable(),
  canonical_source_status: z.string().nullable(),
})

const amountsSchema = z.object({
  reported_unit: z.string(),
  net_distributable_amount: z.string().nullable(),
  federal_amount: z.string().nullable(),
  states_amount: z.string().nullable(),
  local_governments_amount: z.string().nullable(),
  derivation_amount: z.string().nullable(),
  vat_amount: z.string().nullable(),
  statutory_amount: z.string().nullable(),
  gross_amount: z.string().nullable(),
  deductions_amount: z.string().nullable(),
})

const reconciliationSchema = z.object({
  status: z.string(),
  component_total: z.string().nullable(),
  variance: z.string().nullable(),
  tolerance: z.string().nullable(),
  derivation_treatment: z.string(),
  note: z.string(),
})

const findingSchema = z.object({
  rule_code: z.string(),
  severity: z.string(),
  message: z.string(),
  details: z.record(z.string(), z.unknown()).nullable(),
  tolerance: z.string().nullable(),
})

const approvalSchema = z
  .object({
    actor_user_id: z.string().nullable(),
    actor_name: z.string().nullable(),
    created_at: z.string(),
    note: z.unknown().nullable(),
  })
  .nullable()

const packetSchema = z.object({
  run_id: z.string(),
  distribution_id: z.string(),
  reporting_period_id: z.string(),
  reporting_label: z.string(),
  disbursement_month: z.iso.date(),
  allocation_period_month: z.iso.date().nullable(),
  verification_status: z.string(),
  pipeline_status: z.string(),
  published: z.boolean(),
  source: sourceSchema,
  amounts: amountsSchema,
  reconciliation: reconciliationSchema,
  states_scope: z.string().nullable(),
  findings: z.array(findingSchema),
  blocking_count: z.number().int(),
  approval: approvalSchema,
})

const actionSchema = z.object({
  run_id: z.string(),
  distribution_id: z.string(),
  status: z.string(),
  published: z.boolean(),
})

export type NationalActor = z.infer<typeof actorSchema>
export type PendingNationalReview = z.infer<typeof pendingSchema>
export type NationalReviewPacket = z.infer<typeof packetSchema>

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

function adminHeaders() {
  return {
    'Content-Type': 'application/json',
    'X-Admin-Key': process.env.ADMIN_KEY ?? '',
  }
}

async function getJson<T>(path: string, schema: z.ZodType<T>): Promise<ApiResult<T>> {
  try {
    const response = await fetch(`${apiBaseUrl()}${path}`, {
      cache: 'no-store',
      headers: { 'X-Admin-Key': process.env.ADMIN_KEY ?? '' },
    })
    if (!response.ok) return { data: null, error: 'National review service is unavailable.' }
    return { data: schema.parse(await response.json()), error: null }
  } catch {
    return { data: null, error: 'National review service is unavailable.' }
  }
}

export function getNationalActors() {
  return getJson('/api/v1/review/national/actors', z.array(actorSchema))
}

export function getPendingNationalReviews() {
  return getJson('/api/v1/review/national/pending', z.array(pendingSchema))
}

export function getNationalReviewPacket(runId: string) {
  return getJson(`/api/v1/review/national/${encodeURIComponent(runId)}`, packetSchema)
}

async function postAction(
  path: string,
  body: Record<string, unknown>,
): Promise<ApiResult<z.infer<typeof actionSchema>>> {
  try {
    const response = await fetch(`${apiBaseUrl()}${path}`, {
      method: 'POST',
      headers: adminHeaders(),
      body: JSON.stringify(body),
    })
    if (!response.ok) {
      const payload = (await response.json().catch(() => null)) as { detail?: string } | null
      return { data: null, error: payload?.detail ?? 'National review action failed.' }
    }
    return { data: actionSchema.parse(await response.json()), error: null }
  } catch {
    return { data: null, error: 'National review action failed.' }
  }
}

export function approveNationalReview(runId: string, reviewerId: string, note?: string) {
  return postAction(`/api/v1/review/national/${encodeURIComponent(runId)}/approve`, {
    reviewer_id: reviewerId,
    attestation: true,
    note,
  })
}

export function publishNationalReview(runId: string, publisherId: string) {
  return postAction(`/api/v1/review/national/${encodeURIComponent(runId)}/publish`, {
    publisher_id: publisherId,
    attestation: true,
  })
}
