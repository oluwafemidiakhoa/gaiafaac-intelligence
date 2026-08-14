import { z } from 'zod'

export const evidenceStatusSchema = z.enum([
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

const jurisdictionSchema = z.object({
  country: z.literal('NG'),
  code: z.string(),
  name: z.string(),
})

const manifestSchema = z.object({
  manifest_version: z.string(),
  schema_version: z.string(),
  canonicalization_version: z.string(),
  hash_algorithm: z.literal('sha256'),
  payload_sha256: z.string().length(64),
  payload: z.record(z.string(), z.unknown()),
})

const revisionSchema = z.object({
  previous_claim_gaia_id: z.string(),
  revised_claim_gaia_id: z.string(),
  reason: z.string(),
  value_delta: z.string().nullable(),
  value_change_percent: z.string().nullable(),
  material_change: z.boolean().nullable(),
  source_revision: z.boolean(),
  detected_at: z.string(),
  methodology_version: z.string(),
})

const conflictSchema = z.object({
  conflict_id: z.string(),
  status: z.enum(['unresolved', 'resolved', 'dismissed']),
  object_type: z.string(),
  fiscal_period: z.string(),
  metric: z.string(),
  explanation: z.string(),
  detected_at: z.string(),
  participants: z.array(
    z.object({
      claim_gaia_id: z.string(),
      publisher: z.string(),
      value: z.string().nullable(),
      unit: z.string(),
      currency: z.string().nullable(),
      source_sha256: z.string().length(64),
    }),
  ),
})

const historySchema = z.object({
  entry_type: z.enum([
    'source_detected',
    'human_verified',
    'published',
    'source_revised',
    'claim_superseded',
  ]),
  occurred_at: z.string(),
  label: z.string(),
  evidence_ids: z.array(z.string()),
})

export const fiscalProofEnvelopeSchema = z.object({
  data: z.object({
    gaia_id: z.string(),
    object_type: z.string(),
    jurisdiction: jurisdictionSchema,
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
    revisions: z.array(revisionSchema),
    conflicts: z.array(conflictSchema),
    history: z.array(historySchema),
  }),
  meta: z.object({
    schema_version: z.literal('1.0.0'),
    methodology_version: z.string(),
  }),
})

const domainClaimSchema = z.object({
  gaia_id: z.string(),
  metric: z.string(),
  fiscal_period: z.string(),
  value: z.string().nullable(),
  unit: z.string(),
  currency: z.string().nullable(),
  status: evidenceStatusSchema,
})

const domainSchema = z.object({
  status: evidenceStatusSchema,
  claims: z.array(domainClaimSchema),
})

export const fiscalStateEnvelopeSchema = z.object({
  data: z.object({
    fiscal_state_id: z.string(),
    jurisdiction: jurisdictionSchema,
    effective_at: z.string(),
    fiscal_period: z.string(),
    ledger_status: evidenceStatusSchema,
    evidence_coverage: z.string().nullable(),
    evidence_coverage_status: z.enum(['calculated', 'insufficient_evidence']),
    domains: z.record(z.string(), domainSchema),
    evidence_integrity: z.record(z.string(), z.unknown()),
    events: z.array(z.record(z.string(), z.unknown())),
    sources: z.array(
      z.object({
        publisher: z.string(),
        document_url: z.string().nullable(),
        document_sha256: z.string().length(64),
        publication_date: z.string().nullable(),
      }),
    ),
    previous_state_id: z.string().nullable(),
    published_at: z.string(),
  }),
  evidence: z.object({
    manifest: manifestSchema,
    conflicts: z.array(conflictSchema),
  }),
  meta: z.object({
    schema_version: z.string(),
    methodology_version: z.string(),
  }),
})

const eventSchema = z.object({
  event_id: z.string(),
  jurisdiction: jurisdictionSchema,
  event_type: z.string(),
  severity: z.enum(['informational', 'notable', 'material', 'critical']),
  effective_at: z.string(),
  detected_at: z.string(),
  evidence_status: evidenceStatusSchema,
  evidence_ids: z.array(z.string()),
  calculation: z.record(z.string(), z.unknown()),
  explanation: z.string(),
  fiscal_state_id: z.string().nullable(),
  methodology_version: z.string(),
})

export const fiscalEventStreamEnvelopeSchema = z.object({
  data: z.array(eventSchema),
  evidence: z.object({ record_count: z.number().int(), meaning: z.string() }),
  meta: z.object({
    schema_version: z.string(),
    methodology_version: z.string(),
  }),
})

export const evidenceSourceRegistryEnvelopeSchema = z.object({
  data: z.array(
    z.object({
      source_id: z.string(),
      publisher: z.string(),
      source_type: z.string(),
      jurisdiction: z.string(),
      fiscal_domain: z.string(),
      reporting_cadence: z.string().nullable(),
      canonical_url: z.string().nullable(),
      document_url: z.string().nullable(),
      retrieved_at: z.string().nullable(),
      document_sha256: z.string().length(64),
      source_status: z.string(),
      extraction_status: z.string(),
      verification_status: evidenceStatusSchema,
      last_checked_at: z.string().nullable(),
      revision_detected: z.boolean(),
      supersedes_source_id: z.string().nullable(),
    }),
  ),
  evidence: z.record(z.string(), z.unknown()),
  meta: z.object({
    schema_version: z.string(),
    methodology_version: z.string(),
  }),
})

export const fiscalCertificateEnvelopeSchema = z.object({
  data: z.object({
    gaia_id: z.string(),
    jurisdiction: jurisdictionSchema,
    fiscal_period: z.string(),
    fiscal_state_id: z.string(),
    ledger_status: evidenceStatusSchema,
    evidence_coverage: z.string().nullable(),
    evidence_integrity: z.record(z.string(), z.unknown()),
    verified_domains: z.array(z.string()),
    partial_domains: z.array(z.string()),
    unavailable_domains: z.array(z.string()),
    proof_gaia_ids: z.array(z.string()),
    issued_at: z.string(),
  }),
  evidence: z.object({ manifest: manifestSchema, disclaimer: z.string() }),
  meta: z.object({
    schema_version: z.string(),
    methodology_version: z.string(),
  }),
})

export type LedgerFiscalProof = z.infer<typeof fiscalProofEnvelopeSchema>
export type LedgerFiscalState = z.infer<typeof fiscalStateEnvelopeSchema>
export type LedgerFiscalEvent = z.infer<typeof eventSchema>
export type LedgerFiscalCertificate = z.infer<
  typeof fiscalCertificateEnvelopeSchema
>

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

async function getLedgerObject<T>(path: string, schema: z.ZodType<T>) {
  try {
    const response = await fetch(`${apiBaseUrl()}${path}`, {
      next: { revalidate: 300 },
    })
    if (!response.ok)
      return { data: null, error: 'Ledger record is unavailable.' }
    return { data: schema.parse(await response.json()), error: null }
  } catch {
    return { data: null, error: 'Ledger record is unavailable.' }
  }
}

export function getLedgerFiscalProof(gaiaId: string) {
  return getLedgerObject(
    `/api/v1/proofs/${encodeURIComponent(gaiaId)}`,
    fiscalProofEnvelopeSchema,
  )
}

export function getJurisdictionFiscalState(code: string) {
  return getLedgerObject(
    `/api/v1/jurisdictions/${encodeURIComponent(code)}/state`,
    fiscalStateEnvelopeSchema,
  )
}

export type FiscalEventFilters = {
  jurisdiction?: string
  eventType?: string
  severity?: string
  evidenceStatus?: string
  dateFrom?: string
  dateTo?: string
}

export function getFiscalEvents(filters: FiscalEventFilters = {}) {
  const search = new URLSearchParams()
  if (filters.jurisdiction) search.set('jurisdiction', filters.jurisdiction)
  if (filters.eventType) search.set('event_type', filters.eventType)
  if (filters.severity) search.set('severity', filters.severity)
  if (filters.evidenceStatus)
    search.set('evidence_status', filters.evidenceStatus)
  if (filters.dateFrom) search.set('date_from', filters.dateFrom)
  if (filters.dateTo) search.set('date_to', filters.dateTo)
  const query = search.size ? `?${search.toString()}` : ''
  return getLedgerObject(
    `/api/v1/events${query}`,
    fiscalEventStreamEnvelopeSchema,
  )
}

export function getJurisdictionEvidenceSources(code: string) {
  return getLedgerObject(
    `/api/v1/jurisdictions/${encodeURIComponent(code)}/evidence`,
    evidenceSourceRegistryEnvelopeSchema,
  )
}

export function getFiscalCertificate(gaiaId: string) {
  return getLedgerObject(
    `/api/v1/certificates/${encodeURIComponent(gaiaId)}`,
    fiscalCertificateEnvelopeSchema,
  )
}
