import { z } from 'zod'

const actorSchema = z.object({
  id: z.string(),
  full_name: z.string(),
  email: z.string(),
  role: z.enum(['reviewer', 'administrator']),
})

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
  approved: z.boolean(),
  approved_by: z.string().nullable(),
  created_at: z.string().nullable(),
})

const reviewSourceSchema = z.object({
  source_organization: z.string(),
  source_url: z.url().nullable(),
  original_filename: z.string(),
  sha256: z.string().length(64),
  publication_date: z.iso.date().nullable(),
  document_version: z.string(),
})

const reviewAllocationSchema = z.object({
  state_name: z.string(),
  state_code: z.string(),
  gross_total: z.string().nullable(),
  total_deductions: z.string().nullable(),
  net_allocation: z.string().nullable(),
  reported_unit: z.string(),
  verification_status: z.string(),
  extraction_confidence: z.string().nullable(),
})

const reviewFindingSchema = z.object({
  rule_code: z.string(),
  severity: z.string(),
  message: z.string(),
  details: z.record(z.string(), z.unknown()).nullable(),
  outcome: z.string(),
})

const approvalSchema = z
  .object({
    actor_user_id: z.string().nullable(),
    actor_name: z.string().nullable(),
    created_at: z.string(),
    note: z.string().nullable(),
  })
  .nullable()

export const reviewPacketSchema = z.object({
  run_id: z.string(),
  reporting_label: z.string(),
  revenue_month: z.iso.date(),
  status: z.string(),
  source: reviewSourceSchema,
  covered_states: z.number().int(),
  expected_states: z.number().int(),
  finding_count: z.number().int(),
  blocking_count: z.number().int(),
  allocations: z.array(reviewAllocationSchema),
  findings: z.array(reviewFindingSchema),
  approval: approvalSchema,
})

const reviewActionSchema = z.object({
  run_id: z.string(),
  status: z.string(),
  allocations_affected: z.number().int(),
  published: z.boolean(),
})

export type ReviewActor = z.infer<typeof actorSchema>
export type PendingReviewItem = z.infer<typeof pendingReviewSchema>
export type ReviewPacket = z.infer<typeof reviewPacketSchema>
export type ReviewAction = z.infer<typeof reviewActionSchema>

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

async function getJson<T>(
  path: string,
  schema: z.ZodType<T>,
): Promise<ApiResult<T>> {
  try {
    const response = await fetch(`${apiBaseUrl()}${path}`, {
      cache: 'no-store',
      headers: { 'X-Admin-Key': process.env.ADMIN_KEY ?? '' },
    })
    if (!response.ok) {
      return { data: null, error: 'The review service is unavailable.' }
    }
    return { data: schema.parse(await response.json()), error: null }
  } catch {
    return { data: null, error: 'The review service is unavailable.' }
  }
}

export function getReviewActors() {
  return getJson('/api/v1/review/actors', z.array(actorSchema))
}

export function getPendingReviews() {
  return getJson('/api/v1/review/pending', z.array(pendingReviewSchema))
}

export function getReviewPacket(runId: string) {
  return getJson(
    `/api/v1/review/${encodeURIComponent(runId)}`,
    reviewPacketSchema,
  )
}

async function postAction(
  path: string,
  body: Record<string, unknown>,
): Promise<ApiResult<ReviewAction>> {
  try {
    const response = await fetch(`${apiBaseUrl()}${path}`, {
      method: 'POST',
      headers: adminHeaders(),
      body: JSON.stringify(body),
    })
    if (!response.ok) {
      const payload = (await response.json().catch(() => null)) as {
        detail?: string
      } | null
      return {
        data: null,
        error: payload?.detail ?? 'Review action failed.',
      }
    }
    return {
      data: reviewActionSchema.parse(await response.json()),
      error: null,
    }
  } catch {
    return { data: null, error: 'Review action failed.' }
  }
}

export function approveReview(
  runId: string,
  reviewerId: string,
  note?: string,
) {
  return postAction(`/api/v1/review/${encodeURIComponent(runId)}/approve`, {
    reviewer_id: reviewerId,
    attestation: true,
    note,
  })
}

export function rejectReview(
  runId: string,
  reviewerId: string,
  reason: string,
) {
  return postAction(`/api/v1/review/${encodeURIComponent(runId)}/reject`, {
    reviewer_id: reviewerId,
    reason,
  })
}

export function publishReview(runId: string, publisherId: string) {
  return postAction(`/api/v1/review/${encodeURIComponent(runId)}/publish`, {
    publisher_id: publisherId,
    attestation: true,
  })
}
