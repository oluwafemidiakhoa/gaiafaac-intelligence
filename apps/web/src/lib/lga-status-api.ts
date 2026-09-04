import { z } from 'zod'

const lgaPublicationStatusSchema = z.object({
  state_name: z.string(),
  state_code: z.string(),
  stage: z.enum([
    'not_ingested',
    'investigation_required',
    'awaiting_review',
    'awaiting_publication',
    'published',
  ]),
  reporting_label: z.string().nullable(),
  disbursement_month: z.iso.date().nullable(),
  source_format: z.enum(['excel', 'pdf']).nullable(),
  original_filename: z.string().nullable(),
  source_sha256: z.string().length(64).nullable(),
  record_count: z.number().int(),
  expected_record_count: z.number().int(),
  blocking_count: z.number().int(),
  message: z.string(),
})

export type LgaPublicationStatus = z.infer<typeof lgaPublicationStatusSchema>

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

export async function getLgaPublicationStatus(
  stateCode: string,
): Promise<{ data: LgaPublicationStatus | null; error: string | null }> {
  try {
    const response = await fetch(
      `${apiBaseUrl()}/api/v1/published/local-governments/status/${encodeURIComponent(stateCode)}`,
      { next: { revalidate: 60 } },
    )
    if (!response.ok) {
      return {
        data: null,
        error:
          response.status === 404
            ? 'No LGA publication status is available for this jurisdiction.'
            : 'The LGA publication-status service is unavailable.',
      }
    }
    return {
      data: lgaPublicationStatusSchema.parse(await response.json()),
      error: null,
    }
  } catch {
    return {
      data: null,
      error: 'The LGA publication-status service is unavailable.',
    }
  }
}
