import { z } from 'zod'

export const pendingDmoReviewSchema = z.object({
  source_document_id: z.string(),
  debt_kind: z.string(),
  as_of_date: z.iso.date(),
  source_organization: z.string(),
  processing_status: z.string(),
  covered_states: z.number().int(),
  expected_states: z.number().int(),
  approved: z.boolean(),
  approved_by: z.string().nullable(),
  created_at: z.string().nullable(),
})

const dmoReviewSourceSchema = z.object({
  source_organization: z.string(),
  source_url: z.url().nullable(),
  original_filename: z.string(),
  sha256: z.string().length(64),
  document_version: z.string(),
})

const dmoReviewRecordSchema = z.object({
  state_name: z.string(),
  state_code: z.string(),
  debt_amount: z.string(),
  currency: z.string(),
  verification_status: z.string(),
  is_published: z.boolean(),
})

const dmoApprovalSchema = z
  .object({
    actor_user_id: z.string().nullable(),
    actor_name: z.string().nullable(),
    created_at: z.string(),
  })
  .nullable()

export const dmoReviewPacketSchema = z.object({
  source_document_id: z.string(),
  debt_kind: z.string(),
  as_of_date: z.iso.date(),
  source: dmoReviewSourceSchema,
  covered_states: z.number().int(),
  expected_states: z.number().int(),
  records: z.array(dmoReviewRecordSchema),
  approval: dmoApprovalSchema,
  published: z.boolean(),
})

const dmoReviewActionSchema = z.object({
  source_document_id: z.string(),
  debt_kind: z.string(),
  as_of_date: z.iso.date(),
  records_affected: z.number().int(),
  published: z.boolean(),
})

export type PendingDmoReviewItem = z.infer<typeof pendingDmoReviewSchema>
export type DmoReviewPacket = z.infer<typeof dmoReviewPacketSchema>
export type DmoReviewAction = z.infer<typeof dmoReviewActionSchema>

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
      return { data: null, error: 'The DMO review service is unavailable.' }
    }
    return { data: schema.parse(await response.json()), error: null }
  } catch {
    return { data: null, error: 'The DMO review service is unavailable.' }
  }
}

export function getPendingDmoReviews() {
  return getJson('/api/v1/dmo-review/pending', z.array(pendingDmoReviewSchema))
}

export function getDmoReviewPacket(sourceId: string) {
  return getJson(
    `/api/v1/dmo-review/${encodeURIComponent(sourceId)}`,
    dmoReviewPacketSchema,
  )
}

async function postAction(
  path: string,
  body: Record<string, unknown>,
): Promise<ApiResult<DmoReviewAction>> {
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
        error: payload?.detail ?? 'DMO review action failed.',
      }
    }
    return {
      data: dmoReviewActionSchema.parse(await response.json()),
      error: null,
    }
  } catch {
    return { data: null, error: 'DMO review action failed.' }
  }
}

export function approveDmoReview(sourceId: string, reviewerId: string) {
  return postAction(
    `/api/v1/dmo-review/${encodeURIComponent(sourceId)}/approve`,
    { reviewer_id: reviewerId, attestation: true },
  )
}

export function publishDmoReview(sourceId: string, publisherId: string) {
  return postAction(
    `/api/v1/dmo-review/${encodeURIComponent(sourceId)}/publish`,
    { publisher_id: publisherId, attestation: true },
  )
}
