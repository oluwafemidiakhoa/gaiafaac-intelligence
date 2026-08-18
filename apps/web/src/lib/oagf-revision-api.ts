import { z } from 'zod'

const revisionCaseSchema = z.object({
  id: z.string(),
  status: z.string(),
  detected_at: z.string(),
  title: z.string(),
  reporting_label: z.string().nullable(),
  revenue_month: z.iso.date().nullable(),
  current_version: z.number().int(),
  previous_version: z.number().int(),
  current_sha256: z.string().length(64),
  previous_sha256: z.string().length(64),
  current_source_url: z.url(),
  previous_source_url: z.url(),
  resolution_code: z.string().nullable(),
  review_note: z.string().nullable(),
  reviewed_by: z.string().nullable(),
  reviewed_at: z.string().nullable(),
})

const resolveSchema = z.object({
  id: z.string(),
  status: z.string(),
  resolution_code: z.string(),
})

export type OagfRevisionCase = z.infer<typeof revisionCaseSchema>

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
    if (!response.ok) return { data: null, error: 'The OAGF revision service is unavailable.' }
    return { data: schema.parse(await response.json()), error: null }
  } catch {
    return { data: null, error: 'The OAGF revision service is unavailable.' }
  }
}

export function getOagfRevisionCases() {
  return getJson('/api/v1/review/oagf-revisions', z.array(revisionCaseSchema))
}

export function getOagfRevisionCase(caseId: string) {
  return getJson(
    `/api/v1/review/oagf-revisions/${encodeURIComponent(caseId)}`,
    revisionCaseSchema,
  )
}

export async function resolveOagfRevision(
  caseId: string,
  reviewerId: string,
  resolutionCode: string,
  note: string,
): Promise<ApiResult<z.infer<typeof resolveSchema>>> {
  try {
    const response = await fetch(
      `${apiBaseUrl()}/api/v1/review/oagf-revisions/${encodeURIComponent(caseId)}/resolve`,
      {
        method: 'POST',
        headers: adminHeaders(),
        body: JSON.stringify({
          reviewer_id: reviewerId,
          resolution_code: resolutionCode,
          attestation: true,
          note,
        }),
      },
    )
    if (!response.ok) {
      const payload = (await response.json().catch(() => null)) as { detail?: string } | null
      return { data: null, error: payload?.detail ?? 'Revision review failed.' }
    }
    return { data: resolveSchema.parse(await response.json()), error: null }
  } catch {
    return { data: null, error: 'Revision review failed.' }
  }
}

export function oagfRevisionSourceApiUrl(caseId: string, version: 'current' | 'previous') {
  return `${apiBaseUrl()}/api/v1/review/oagf-revisions/${encodeURIComponent(caseId)}/source/${version}`
}
