import { z } from 'zod'

const evidenceStatusSchema = z.enum([
  'unavailable',
  'detected',
  'pending_extraction',
  'extracted',
  'pending_verification',
  'verified',
  'partial',
  'conflicting',
  'superseded',
  'rejected',
])

const manifestSchema = z.object({
  manifest_version: z.string(),
  schema_version: z.string(),
  canonicalization_version: z.string(),
  hash_algorithm: z.literal('sha256'),
  payload_sha256: z.string().length(64),
  payload: z.record(z.string(), z.unknown()),
})

export const fiscalProofEnvelopeSchema = z.object({
  data: z.object({
    gaia_id: z.string(),
    object_type: z.string(),
    jurisdiction: z.object({
      country: z.literal('NG'),
      code: z.string(),
      name: z.string(),
    }),
    fiscal_period: z.string(),
    metric: z.string(),
    value: z.string().nullable(),
    unit: z.string(),
    currency: z.string().nullable(),
    effective_at: z.string(),
    methodology_version: z.string(),
    supersedes_gaia_id: z.string().nullable(),
    superseded_by_gaia_id: z.string().nullable(),
    source: z.object({
      publisher: z.string(),
      document_url: z.string().nullable(),
      document_sha256: z.string().length(64),
      publication_date: z.string().nullable(),
      page: z.number().int().nullable(),
      table: z.string().nullable(),
    }),
    verification: z.object({
      status: evidenceStatusSchema,
      source_verified: z.boolean(),
      reconciled: z.boolean().nullable(),
      human_reviewed: z.boolean(),
      published: z.boolean(),
      verified_at: z.string().nullable(),
      note: z.string(),
    }),
    published_at: z.string(),
  }),
  evidence: z.object({
    manifest: manifestSchema,
    disclaimer: z.string(),
  }),
  meta: z.object({
    schema_version: z.literal('1.0.0'),
    methodology_version: z.string(),
  }),
})

export type LedgerFiscalProof = z.infer<typeof fiscalProofEnvelopeSchema>

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

export async function getLedgerFiscalProof(gaiaId: string) {
  try {
    const response = await fetch(
      `${apiBaseUrl()}/api/v1/proofs/${encodeURIComponent(gaiaId)}`,
      { next: { revalidate: 300 } },
    )
    if (!response.ok) {
      return { data: null, error: 'Fiscal Proof is unavailable.' }
    }
    return {
      data: fiscalProofEnvelopeSchema.parse(await response.json()),
      error: null,
    }
  } catch {
    return { data: null, error: 'Fiscal Proof is unavailable.' }
  }
}
