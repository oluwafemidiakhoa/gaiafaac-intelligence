import { z } from 'zod'

const verificationSchema = z.object({
  id: z.string().uuid(),
  receipt_sha256: z.string().length(64),
  methodology_version: z.string(),
  created_at: z.string(),
  evidence_cutoff: z.string().nullable(),
  jurisdictions: z.array(z.string()),
  evidence_domains: z.array(z.string()),
  evidence_count: z.number().int(),
  source_sha256s: z.array(z.string().length(64)),
  evidence_record_sha256s: z.array(z.string().length(64)),
  evidence_kinds: z.array(z.string()),
  predecessor_receipt_id: z.string().uuid().nullable(),
  predecessor_receipt_sha256: z.string().length(64).nullable(),
  triggering_match_id: z.string().uuid().nullable(),
  content_sha256: z.string().length(64).nullable(),
  statement: z.string(),
  limitations: z.array(z.string()),
})

export type FiscalReceiptVerification = z.infer<typeof verificationSchema>

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

export async function verifyFiscalReceipt(receiptId: string) {
  try {
    const response = await fetch(
      `${apiBaseUrl()}/api/v1/fiscal-receipts/${encodeURIComponent(receiptId)}/verify`,
      { cache: 'no-store' },
    )
    if (!response.ok) {
      return {
        data: null,
        error:
          response.status === 404
            ? 'Fiscal Receipt not found.'
            : 'Fiscal Receipt verification is temporarily unavailable.',
      }
    }
    return {
      data: verificationSchema.parse(await response.json()),
      error: null,
    }
  } catch {
    return {
      data: null,
      error: 'Fiscal Receipt verification is temporarily unavailable.',
    }
  }
}
