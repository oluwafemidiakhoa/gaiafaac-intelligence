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

export type EvidenceLaneState =
  | 'Live'
  | 'Pipeline ready'
  | 'Not connected'
  | 'Unavailable'

export interface EvidenceLane {
  authority: string
  label: string
  state: EvidenceLaneState
  description: string
  publishedRecordCount: number
  latestPeriod: string | null
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
  return periods.length > 0 ? [...periods].sort().at(-1) ?? null : null
}

function officialClaims(
  envelope: z.infer<typeof fiscalClaimEnvelopeSchema>,
  publisherFragment: string,
) {
  const needle = publisherFragment.toLocaleLowerCase()
  return envelope.data.filter(
    (claim) =>
      claim.evidence_status === 'verified' &&
      claim.source.publisher.toLocaleLowerCase().includes(needle),
  )
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

export async function getEvidenceNetworkStatus({
  oagfLive,
  oagfPeriod,
}: {
  oagfLive: boolean
  oagfPeriod: string | null
}): Promise<EvidenceNetworkResult> {
  try {
    const [igrEnvelope, debtEnvelope] = await Promise.all([
      fetchClaims('igr'),
      fetchClaims('debt'),
    ])

    const nbsClaims = officialClaims(igrEnvelope, 'National Bureau of Statistics')
    const dmoClaims = officialClaims(debtEnvelope, 'Debt Management Office')

    const lanes: EvidenceLane[] = [
      {
        authority: 'OAGF / FAAC',
        label: 'Allocations',
        state: oagfLive ? 'Live' : 'Unavailable',
        description: oagfLive
          ? 'Complete published state and FCT allocation evidence, retained with its official source fingerprint.'
          : 'No complete governed OAGF / FAAC allocation release is currently published.',
        publishedRecordCount: oagfLive ? 37 : 0,
        latestPeriod: oagfPeriod,
      },
      {
        authority: 'NBS',
        label: 'State IGR',
        state: nbsClaims.length > 0 ? 'Live' : 'Pipeline ready',
        description:
          nbsClaims.length > 0
            ? 'Human-verified NBS state IGR claims are published and source-linked.'
            : 'The governed NBS IGR pipeline is available, but no verified NBS IGR claim is published yet.',
        publishedRecordCount: nbsClaims.length,
        latestPeriod: newestPeriod(nbsClaims.map((claim) => claim.fiscal_period)),
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
        latestPeriod: newestPeriod(dmoClaims.map((claim) => claim.fiscal_period)),
      },
      {
        authority: 'CBN',
        label: 'Macro context',
        state: 'Not connected',
        description:
          'CBN macro series are not yet ingested into governed claims, so Gaia does not use a CBN figure here.',
        publishedRecordCount: 0,
        latestPeriod: null,
      },
      {
        authority: 'NRS',
        label: 'Tax context',
        state: 'Not connected',
        description:
          'Federal tax-authority series are not yet ingested into governed claims, so Gaia does not use a tax figure here.',
        publishedRecordCount: 0,
        latestPeriod: null,
      },
    ]

    return { data: lanes, error: null }
  } catch {
    return {
      data: null,
      error: 'The evidence-status service is unavailable. Gaia will not guess a source status.',
    }
  }
}
