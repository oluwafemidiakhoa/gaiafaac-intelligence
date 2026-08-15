import { z } from 'zod'

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
})

const reviewActionSchema = z.object({
  run_id: z.string(),
  status: z.string(),
  allocations_affected: z.number().int(),
  published: z.boolean(),
})

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

export async function getPendingReviews(): Promise<
  ApiResult<PendingReviewItem[]>
> {
  try {
    const response = await fetch(`${apiBaseUrl()}/api/v1/review/pending`, {
      next: { revalidate: 120 },
      headers: { 'X-Admin-Key': process.env.ADMIN_KEY ?? '' },
    })
    if (!response.ok) {
      return { data: null, error: 'The review queue is unavailable.' }
    }
    return {
      data: z.array(pendingReviewSchema).parse(await response.json()),
      error: null,
    }
  } catch {
    return { data: null, error: 'The review queue is unavailable.' }
  }
}

export async function getReviewPacket(
  runId: string,
): Promise<ApiResult<ReviewPacket>> {
  try {
    const response = await fetch(`${apiBaseUrl()}/api/v1/review/${runId}`, {
      cache: 'no-store',
      headers: { 'X-Admin-Key': process.env.ADMIN_KEY ?? '' },
    })
    if (!response.ok) {
      return {
        data: null,
        error:
          response.status === 404
            ? 'This review packet is no longer pending.'
            : 'The review packet is unavailable.',
      }
    }
    return {
      data: reviewPacketSchema.parse(await response.json()),
      error: null,
    }
  } catch {
    return { data: null, error: 'The review packet is unavailable.' }
  }
}

export async function approveReview(
  runId: string,
  note?: string,
): Promise<ApiResult<ReviewAction>> {
  const reviewerId = process.env.REVIEWER_ID
  if (!reviewerId) {
    return { data: null, error: 'Reviewer identity is not configured.' }
  }
  try {
    const response = await fetch(
      `${apiBaseUrl()}/api/v1/review/${runId}/approve`,
      {
        method: 'POST',
        headers: adminHeaders(),
        body: JSON.stringify({
          reviewer_id: reviewerId,
          attestation: true,
          note,
        }),
      },
    )
    if (!response.ok) {
      const payload = (await response.json().catch(() => null)) as {
        detail?: string
      } | null
      return {
        data: null,
        error: payload?.detail ?? 'Approval failed.',
      }
    }
    return {
      data: reviewActionSchema.parse(await response.json()),
      error: null,
    }
  } catch {
    return { data: null, error: 'Approval failed.' }
  }
}

export async function rejectReview(
  runId: string,
  reason: string,
): Promise<ApiResult<ReviewAction>> {
  const reviewerId = process.env.REVIEWER_ID
  if (!reviewerId) {
    return { data: null, error: 'Reviewer identity is not configured.' }
  }
  try {
    const response = await fetch(
      `${apiBaseUrl()}/api/v1/review/${runId}/reject`,
      {
        method: 'POST',
        headers: adminHeaders(),
        body: JSON.stringify({ reviewer_id: reviewerId, reason }),
      },
    )
    if (!response.ok) {
      const payload = (await response.json().catch(() => null)) as {
        detail?: string
      } | null
      return { data: null, error: payload?.detail ?? 'Rejection failed.' }
    }
    return {
      data: reviewActionSchema.parse(await response.json()),
      error: null,
    }
  } catch {
    return { data: null, error: 'Rejection failed.' }
  }
}
