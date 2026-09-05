import { z } from 'zod'

const fiscalClaimSchema = z.object({
  gaia_id: z.string(),
  object_type: z.string(),
  jurisdiction: z.object({
    code: z.string(),
    name: z.string(),
  }),
  fiscal_period: z.string(),
  metric: z.string(),
  value: z.string().nullable(),
  unit: z.string(),
  currency: z.string().nullable(),
  evidence_status: z.string(),
  effective_at: z.string(),
  published_at: z.string(),
  supersedes_gaia_id: z.string().nullable(),
  superseded_by_gaia_id: z.string().nullable(),
  source: z.object({
    publisher: z.string(),
    document_url: z.string().nullable(),
    document_sha256: z.string().length(64),
    page: z.number().int().nullable(),
    table: z.string().nullable(),
  }),
})

const fiscalClaimEnvelopeSchema = z.object({
  data: z.array(fiscalClaimSchema),
})

const governedIgrStatusSchema = z.object({
  source_scope: z.string().nullable(),
  is_live: z.boolean(),
  published_record_count: z.number().int().nonnegative(),
  jurisdiction_count: z.number().int().nonnegative(),
  latest_period: z.string().nullable(),
  latest_published_at: z.string().nullable(),
  source_organizations: z.array(z.string()),
  note: z.string(),
})

export type EvidenceLaneState =
  | 'Live'
  | 'Pipeline ready'
  | 'Not connected'
  | 'Unavailable'

export interface EvidenceSourceDocument {
  publisher: string
  documentUrl: string | null
  sha256: string
  fiscalPeriod: string
}

export interface EvidenceLane {
  authority: string
  label: string
  state: EvidenceLaneState
  description: string
  publishedRecordCount: number
  jurisdictionCount: number
  latestPeriod: string | null
  sourceOrganizations: string[]
  sourceDocuments: EvidenceSourceDocument[]
}

export interface EvidenceNetworkResult {
  data: EvidenceLane[] | null
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

function newestPeriod(periods: string[]) {
  return periods.length > 0 ? ([...periods].sort().at(-1) ?? null) : null
}

function officialClaims(
  envelope: z.infer<typeof fiscalClaimEnvelopeSchema>,
  publisherFragment: string,
) {
  const needle = publisherFragment.toLocaleLowerCase()
  return envelope.data.filter(
    (claim) =>
      claim.evidence_status === 'verified' &&
      claim.superseded_by_gaia_id === null &&
      claim.source.publisher.toLocaleLowerCase().includes(needle),
  )
}

function sourceDocuments(
  claims: z.infer<typeof fiscalClaimSchema>[],
  latestPeriod: string | null,
): EvidenceSourceDocument[] {
  const seen = new Set<string>()
  return claims
    .filter(
      (claim) => latestPeriod === null || claim.fiscal_period === latestPeriod,
    )
    .flatMap((claim) => {
      if (seen.has(claim.source.document_sha256)) return []
      seen.add(claim.source.document_sha256)
      return [
        {
          publisher: claim.source.publisher,
          documentUrl: claim.source.document_url,
          sha256: claim.source.document_sha256,
          fiscalPeriod: claim.fiscal_period,
        },
      ]
    })
}

async function fetchClaims(domain: string) {
  const response = await fetch(
    `${apiBaseUrl()}/api/v1/claims?fiscal_domain=${encodeURIComponent(domain)}&limit=200`,
    { next: { revalidate: 300 } },
  )
  if (!response.ok) {
    throw new Error(`Unable to load ${domain} claims.`)
  }
  return fiscalClaimEnvelopeSchema.parse(await response.json())
}

async function fetchNbsIgrStatus() {
  const params = new URLSearchParams({
    publisher: 'National Bureau of Statistics',
  })
  const response = await fetch(
    `${apiBaseUrl()}/api/v1/published/igr/status?${params.toString()}`,
    { next: { revalidate: 300 } },
  )
  if (!response.ok) {
    throw new Error('Unable to load canonical NBS IGR status.')
  }
  return governedIgrStatusSchema.parse(await response.json())
}

export async function getEvidenceNetworkStatus({
  oagfLive,
  oagfPeriod,
}: {
  oagfLive: boolean
  oagfPeriod: string | null
}): Promise<EvidenceNetworkResult> {
  try {
    const [nbsIgrStatus, igrEnvelope, debtEnvelope] = await Promise.all([
      fetchNbsIgrStatus(),
      fetchClaims('igr'),
      fetchClaims('debt'),
    ])

    const nbsClaims = officialClaims(
      igrEnvelope,
      'National Bureau of Statistics',
    )
    const dmoClaims = officialClaims(debtEnvelope, 'Debt Management Office')
    const dmoLatestPeriod = newestPeriod(
      dmoClaims.map((claim) => claim.fiscal_period),
    )

    const lanes: EvidenceLane[] = [
      {
        authority: 'OAGF / FAAC',
        label: 'Allocations',
        state: oagfLive ? 'Live' : 'Unavailable',
        description: oagfLive
          ? 'Complete published state and FCT allocation evidence, retained with its official source fingerprint.'
          : 'No complete governed OAGF / FAAC allocation release is currently published.',
        publishedRecordCount: oagfLive ? 37 : 0,
        jurisdictionCount: oagfLive ? 37 : 0,
        latestPeriod: oagfPeriod,
        sourceOrganizations: oagfLive
          ? ['Office of the Accountant-General of the Federation (OAGF)']
          : [],
        sourceDocuments: [],
      },
      {
        authority: 'NBS',
        label: 'State IGR',
        state: nbsIgrStatus.is_live ? 'Live' : 'Pipeline ready',
        description: nbsIgrStatus.is_live
          ? 'Human-verified NBS state IGR claims are published in the canonical governed ledger and source-linked.'
          : 'The governed NBS IGR pipeline is available, but no canonical verified NBS IGR publication is live yet.',
        publishedRecordCount: nbsIgrStatus.published_record_count,
        jurisdictionCount: nbsIgrStatus.jurisdiction_count,
        latestPeriod: nbsIgrStatus.latest_period,
        sourceOrganizations: nbsIgrStatus.source_organizations,
        sourceDocuments: sourceDocuments(nbsClaims, nbsIgrStatus.latest_period),
      },
      {
        authority: 'DMO',
        label: 'Debt pressure',
        state: dmoClaims.length > 0 ? 'Live' : 'Pipeline ready',
        description:
          dmoClaims.length > 0
            ? 'Human-verified DMO debt claims are published and source-linked.'
            : 'The governed DMO debt pipeline is available, but no verified DMO debt claim is published yet.',
        publishedRecordCount: dmoClaims.length,
        jurisdictionCount: new Set(
          dmoClaims.map((claim) => claim.jurisdiction.code),
        ).size,
        latestPeriod: dmoLatestPeriod,
        sourceOrganizations: [
          ...new Set(dmoClaims.map((claim) => claim.source.publisher)),
        ].sort(),
        sourceDocuments: sourceDocuments(dmoClaims, dmoLatestPeriod),
      },
      {
        authority: 'CBN',
        label: 'Macro context',
        state: 'Not connected',
        description:
          'CBN macro series are not yet ingested into governed claims, so Gaia does not use a CBN figure here.',
        publishedRecordCount: 0,
        jurisdictionCount: 0,
        latestPeriod: null,
        sourceOrganizations: [],
        sourceDocuments: [],
      },
      {
        authority: 'NRS',
        label: 'Tax context',
        state: 'Not connected',
        description:
          'Federal tax-authority series are not yet ingested into governed claims, so Gaia does not use a tax figure here.',
        publishedRecordCount: 0,
        jurisdictionCount: 0,
        latestPeriod: null,
        sourceOrganizations: [],
        sourceDocuments: [],
      },
    ]

    return { data: lanes, error: null }
  } catch {
    return {
      data: null,
      error:
        'The evidence-status service is unavailable. Gaia will not guess a source status.',
    }
  }
}
