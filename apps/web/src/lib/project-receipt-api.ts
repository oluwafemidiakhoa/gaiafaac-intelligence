import { z } from 'zod'

const projectReceiptSchema = z.object({
  purchase_id: z.string().uuid(),
  document_id: z.string(),
  artifact_sha256: z.string().length(64),
  product_code: z.string(),
  product_label: z.string(),
  artifact_schema: z.string().nullable(),
  evidence_captured_at: z.string().nullable(),
  issued_at: z.string().nullable(),
  jurisdictions: z.array(z.string()),
  source_sha256s: z.array(z.string().length(64)),
  source_count: z.number().int(),
  integrity_status: z.enum(['verified', 'integrity_failure']),
  revision_status: z.enum([
    'no_known_revision',
    'review_recommended',
    'source_registry_partial',
    'integrity_failure',
  ]),
  revised_source_sha256s: z.array(z.string().length(64)),
  unknown_source_sha256s: z.array(z.string().length(64)),
  statement: z.string(),
  limitations: z.array(z.string()),
})

export type ProjectReceiptVerification = z.infer<typeof projectReceiptSchema>

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

export async function verifyProjectReceipt(purchaseId: string) {
  try {
    const response = await fetch(
      `${apiBaseUrl()}/api/v1/project-receipts/${encodeURIComponent(purchaseId)}/verify`,
      { cache: 'no-store' },
    )
    if (!response.ok) {
      return {
        data: null,
        error:
          response.status === 404
            ? 'Project receipt not found.'
            : 'Project receipt verification is temporarily unavailable.',
      }
    }
    return {
      data: projectReceiptSchema.parse(await response.json()),
      error: null,
    }
  } catch {
    return {
      data: null,
      error: 'Project receipt verification is temporarily unavailable.',
    }
  }
}
