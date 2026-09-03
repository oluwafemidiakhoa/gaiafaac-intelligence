import { z } from 'zod'

export const pendingIgrReviewSchema = z.object({
  source_document_id: z.string(),
  fiscal_year: z.number().int(),
  source_organization: z.string(),
  processing_status: z.string(),
  covered_states: z.number().int(),
  expected_states: z.number().int(),
  approved: z.boolean(),
  approved_by: z.string().nullable(),
  created_at: z.string().nullable(),
})

const igrReviewSourceSchema = z.object({
  source_organization: z.string(),
  source_url: z.url().nullable(),
  original_filename: z.string(),
  sha256: z.string().length(64),
  document_version: z.string(),
})

const igrReviewRecordSchema = z.object({
  state_name: z.string(),
  state_code: z.string(),
  igr_amount: z.string(),
  reported_unit: z.string(),
  verification_status: z.string(),
  is_published: z.boolean(),
})

const igrApprovalSchema = z
  .object({
    actor_user_id: z.string().nullable(),
    actor_name: z.string().nullable(),
    created_at: z.string(),
  })
  .nullable()

export const igrReviewPacketSchema = z.object({
  source_document_id: z.string(),
  fiscal_year: z.number().int(),
  source: igrReviewSourceSchema,
  covered_states: z.number().int(),
  expected_states: z.number().int(),
  records: z.array(igrReviewRecordSchema),
  approval: igrApprovalSchema,
  published: z.boolean(),
})

const igrReviewActionSchema = z.object({
  source_document_id: z.string(),
  fiscal_year: z.number().int(),
  records_affected: z.number().int(),
  published: z.boolean(),
})

export type PendingIgrReviewItem = z.infer<typeof pendingIgrReviewSchema>
export type IgrReviewPacket = z.infer<typeof igrReviewPacketSchema>
export type IgrReviewAction = z.infer<typeof igrReviewActionSchema>

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
      return {
        data: null,
        error: 'The NBS IGR review service is unavailable.',
      }
    }
    return { data: schema.parse(await response.json()), error: null }
  } catch {
    return { data: null, error: 'The NBS IGR review service is unavailable.' }
  }
}

export function getPendingIgrReviews() {
  return getJson(
    '/api/v1/nbs-igr-review/pending',
    z.array(pendingIgrReviewSchema),
  )
}

export function getIgrReviewPacket(sourceId: string) {
  return getJson(
    `/api/v1/nbs-igr-review/${encodeURIComponent(sourceId)}`,
    igrReviewPacketSchema,
  )
}

async function postAction(
  path: string,
  body: Record<string, unknown>,
): Promise<ApiResult<IgrReviewAction>> {
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
        error: payload?.detail ?? 'NBS IGR review action failed.',
      }
    }
    return {
      data: igrReviewActionSchema.parse(await response.json()),
      error: null,
    }
  } catch {
    return { data: null, error: 'NBS IGR review action failed.' }
  }
}

export function approveIgrReview(sourceId: string, reviewerId: string) {
  return postAction(
    `/api/v1/nbs-igr-review/${encodeURIComponent(sourceId)}/approve`,
    { reviewer_id: reviewerId, attestation: true },
  )
}

export function publishIgrReview(sourceId: string, publisherId: string) {
  return postAction(
    `/api/v1/nbs-igr-review/${encodeURIComponent(sourceId)}/publish`,
    { publisher_id: publisherId, attestation: true },
  )
}
