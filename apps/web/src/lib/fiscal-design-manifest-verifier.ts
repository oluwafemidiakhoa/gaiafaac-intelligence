export interface CurrentEvidenceCheckRequest {
  fingerprint: string
  stateSlug: string
  year: number
  faacShock: number
  igrShock: number
  reserveShare: number
  researchObjective: string
}

export interface EvidenceChangeDetail {
  category:
    | 'coverage'
    | 'evidence'
    | 'assumptions'
    | 'scenario'
    | 'objective'
    | 'other'
  detail: string
}

export type ManifestVerification =
  | {
      status: 'verified'
      fingerprint: string
      stateName: string | null
      year: number | null
      evidenceCount: number | null
      payload: Record<string, unknown>
      currentEvidenceCheck: CurrentEvidenceCheckRequest | null
      artifactKind?: 'fiscal-proof'
      proofVerification?: {
        sourceVerified: boolean
        reconciled: boolean | null
        humanReviewed: boolean
        published: boolean
      }
    }
  | {
      status: 'mismatch'
      fingerprint: string
      computedFingerprint: string
    }
  | {
      status: 'invalid'
      message: string
    }

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function finiteNumber(value: unknown) {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return value
  }
  if (typeof value === 'string' && value.trim()) {
    const parsed = Number(value)
    return Number.isFinite(parsed) ? parsed : null
  }
  return null
}

function displayValue(value: unknown) {
  if (value === null || value === undefined || value === '') {
    return 'not supplied'
  }
  return String(value)
}

function evidenceKey(value: Record<string, unknown>) {
  return [value.evidence_domain, value.label, value.reference_path]
    .map((part) => (typeof part === 'string' ? part : ''))
    .join('\u0000')
}

function evidenceLabel(value: Record<string, unknown>) {
  return typeof value.label === 'string' && value.label.trim()
    ? value.label
    : 'Unnamed evidence record'
}

function evidenceRecords(value: unknown) {
  if (!Array.isArray(value)) {
    return []
  }
  return value.filter(isRecord)
}

function changed(left: unknown, right: unknown) {
  return JSON.stringify(left) !== JSON.stringify(right)
}

export function summarizeFiscalDesignPayloadChanges(
  previous: Record<string, unknown>,
  current: Record<string, unknown>,
): EvidenceChangeDetail[] {
  const changes: EvidenceChangeDetail[] = []

  const coverageFields: Array<[string, string]> = [
    ['coverage_label', 'Coverage label'],
    ['faac_months_published', 'Published FAAC months'],
    ['faac_complete_year', 'Complete FAAC year'],
    ['annual_igr_available', 'Annual IGR availability'],
    ['latest_comparable_year', 'Latest comparable year'],
  ]
  for (const [field, label] of coverageFields) {
    if (changed(previous[field], current[field])) {
      changes.push({
        category: 'coverage',
        detail: `${label} changed from ${displayValue(previous[field])} to ${displayValue(current[field])}.`,
      })
    }
  }

  const previousEvidence = new Map(
    evidenceRecords(previous.evidence).map((record) => [
      evidenceKey(record),
      record,
    ]),
  )
  const currentEvidence = new Map(
    evidenceRecords(current.evidence).map((record) => [
      evidenceKey(record),
      record,
    ]),
  )

  for (const [key, record] of previousEvidence) {
    const currentRecord = currentEvidence.get(key)
    if (!currentRecord) {
      changes.push({
        category: 'evidence',
        detail: `Evidence removed: ${evidenceLabel(record)}.`,
      })
      continue
    }

    const changedParts: string[] = []
    if (record.source_sha256 !== currentRecord.source_sha256) {
      changedParts.push('source hash')
    }
    if (record.value !== currentRecord.value) {
      changedParts.push('value')
    }
    if (record.source_organization !== currentRecord.source_organization) {
      changedParts.push('source organization')
    }
    if (changedParts.length) {
      changes.push({
        category: 'evidence',
        detail: `Evidence changed: ${evidenceLabel(record)} (${changedParts.join(', ')}).`,
      })
    }
  }

  for (const [key, record] of currentEvidence) {
    if (!previousEvidence.has(key)) {
      changes.push({
        category: 'evidence',
        detail: `Evidence added: ${evidenceLabel(record)}.`,
      })
    }
  }

  if (changed(previous.assumptions, current.assumptions)) {
    changes.push({
      category: 'assumptions',
      detail: 'Scenario assumptions changed.',
    })
  }

  if (changed(previous.candidates, current.candidates)) {
    changes.push({
      category: 'scenario',
      detail: 'Scenario outputs or availability changed.',
    })
  }

  if (changed(previous.research_objective, current.research_objective)) {
    changes.push({
      category: 'objective',
      detail: 'Research objective changed.',
    })
  }

  if (changed(previous.design_version, current.design_version)) {
    changes.push({
      category: 'other',
      detail: `Fiscal Design version changed from ${displayValue(previous.design_version)} to ${displayValue(current.design_version)}.`,
    })
  }

  const categorizedFields = new Set([
    'coverage_label',
    'faac_months_published',
    'faac_complete_year',
    'annual_igr_available',
    'latest_comparable_year',
    'evidence',
    'assumptions',
    'candidates',
    'research_objective',
    'design_version',
  ])
  const uncategorizedPrevious = Object.fromEntries(
    Object.entries(previous).filter(([key]) => !categorizedFields.has(key)),
  )
  const uncategorizedCurrent = Object.fromEntries(
    Object.entries(current).filter(([key]) => !categorizedFields.has(key)),
  )
  if (
    changed(uncategorizedPrevious, uncategorizedCurrent) &&
    changes.length === 0
  ) {
    changes.push({
      category: 'other',
      detail: 'Other canonical brief fields changed.',
    })
  }

  return changes
}

async function sha256Hex(value: string) {
  const digest = await globalThis.crypto.subtle.digest(
    'SHA-256',
    new TextEncoder().encode(value),
  )
  return Array.from(new Uint8Array(digest))
    .map((byte) => byte.toString(16).padStart(2, '0'))
    .join('')
}

function canonicalizeProofValue(value: unknown): unknown {
  if (value === null || typeof value === 'boolean') {
    return value
  }
  if (typeof value === 'number') {
    if (!Number.isSafeInteger(value)) {
      throw new TypeError(
        'Canonical proof numbers must be safe JSON integers; exact decimals use strings.',
      )
    }
    return value
  }
  if (typeof value === 'string') {
    return value.normalize('NFC')
  }
  if (Array.isArray(value)) {
    return value.map(canonicalizeProofValue)
  }
  if (isRecord(value)) {
    const entries = Object.entries(value).map(([key, item]) => [
      key.normalize('NFC'),
      item,
    ]) as Array<[string, unknown]>
    entries.sort(([left], [right]) => {
      const leftCodePoints = Array.from(left, (character) =>
        character.codePointAt(0),
      )
      const rightCodePoints = Array.from(right, (character) =>
        character.codePointAt(0),
      )
      const sharedLength = Math.min(
        leftCodePoints.length,
        rightCodePoints.length,
      )
      for (let index = 0; index < sharedLength; index += 1) {
        const difference = leftCodePoints[index]! - rightCodePoints[index]!
        if (difference !== 0) {
          return difference
        }
      }
      return leftCodePoints.length - rightCodePoints.length
    })
    if (entries.some(([key], index) => key === entries[index - 1]?.[0])) {
      throw new TypeError('Duplicate key after Unicode normalization.')
    }
    return Object.fromEntries(
      entries.map(([key, item]) => [key, canonicalizeProofValue(item)]),
    )
  }
  throw new TypeError('Unsupported value in canonical proof payload.')
}

async function verifyFiscalProofManifest(
  parsed: Record<string, unknown>,
): Promise<ManifestVerification> {
  if (parsed.schema_version !== '1.0.0') {
    return {
      status: 'invalid',
      message: 'Unsupported Fiscal Proof schema version.',
    }
  }
  if (parsed.canonicalization_version !== 'gaia-canonical-json-v1') {
    return {
      status: 'invalid',
      message: 'Unsupported Fiscal Proof canonicalization version.',
    }
  }
  if (parsed.hash_algorithm !== 'sha256') {
    return {
      status: 'invalid',
      message: 'Unsupported Fiscal Proof hash algorithm.',
    }
  }
  const fingerprint =
    typeof parsed.payload_sha256 === 'string'
      ? parsed.payload_sha256.toLowerCase()
      : ''
  if (!/^[a-f0-9]{64}$/.test(fingerprint)) {
    return {
      status: 'invalid',
      message: 'The proof payload hash must be a 64-character SHA-256 value.',
    }
  }
  if (!isRecord(parsed.payload)) {
    return {
      status: 'invalid',
      message: 'The Fiscal Proof payload is missing.',
    }
  }

  let canonicalPayload: string
  try {
    canonicalPayload = JSON.stringify(canonicalizeProofValue(parsed.payload))
  } catch {
    return {
      status: 'invalid',
      message: 'The Fiscal Proof payload is not canonicalizable.',
    }
  }
  const computedFingerprint = await sha256Hex(canonicalPayload)
  if (computedFingerprint !== fingerprint) {
    return { status: 'mismatch', fingerprint, computedFingerprint }
  }

  const jurisdiction = isRecord(parsed.payload.jurisdiction)
    ? parsed.payload.jurisdiction
    : null
  const verification = isRecord(parsed.payload.verification)
    ? parsed.payload.verification
    : {}
  const fiscalPeriod =
    typeof parsed.payload.fiscal_period === 'string'
      ? parsed.payload.fiscal_period
      : ''
  const parsedYear = Number(fiscalPeriod.slice(0, 4))

  return {
    status: 'verified',
    fingerprint,
    stateName:
      jurisdiction && typeof jurisdiction.name === 'string'
        ? jurisdiction.name
        : null,
    year: Number.isInteger(parsedYear) ? parsedYear : null,
    evidenceCount: 1,
    payload: parsed.payload,
    currentEvidenceCheck: null,
    artifactKind: 'fiscal-proof',
    proofVerification: {
      sourceVerified: verification.source_verified === true,
      reconciled:
        typeof verification.reconciled === 'boolean'
          ? verification.reconciled
          : null,
      humanReviewed: verification.human_reviewed === true,
      published: verification.published === true,
    },
  }
}

export async function verifyFiscalDesignEvidenceManifestText(
  manifestText: string,
): Promise<ManifestVerification> {
  let parsed: unknown
  try {
    parsed = JSON.parse(manifestText)
  } catch {
    return { status: 'invalid', message: 'The manifest is not valid JSON.' }
  }

  if (!isRecord(parsed)) {
    return { status: 'invalid', message: 'The manifest must be a JSON object.' }
  }

  if (parsed.manifest_version === 'gaia-fiscal-proof-manifest-v1') {
    return verifyFiscalProofManifest(parsed)
  }

  if (parsed.manifest_version !== 'gaia-fiscal-design-evidence-manifest-v1') {
    return {
      status: 'invalid',
      message: 'Unsupported or missing Gaia evidence manifest version.',
    }
  }

  if (parsed.fingerprint_algorithm !== 'sha256') {
    return {
      status: 'invalid',
      message: 'Unsupported or missing manifest fingerprint algorithm.',
    }
  }

  const fingerprint =
    typeof parsed.fingerprint === 'string'
      ? parsed.fingerprint.toLowerCase()
      : ''
  if (!/^[a-f0-9]{64}$/.test(fingerprint)) {
    return {
      status: 'invalid',
      message: 'The manifest fingerprint must be a 64-character SHA-256 value.',
    }
  }

  if (!isRecord(parsed.payload)) {
    return { status: 'invalid', message: 'The manifest payload is missing.' }
  }

  const computedFingerprint = await sha256Hex(JSON.stringify(parsed.payload))
  if (computedFingerprint !== fingerprint) {
    return { status: 'mismatch', fingerprint, computedFingerprint }
  }

  const stateName =
    typeof parsed.payload.state_name === 'string'
      ? parsed.payload.state_name
      : null
  const stateSlug =
    typeof parsed.payload.state_slug === 'string'
      ? parsed.payload.state_slug.trim().toLowerCase()
      : ''
  const year =
    typeof parsed.payload.year === 'number' &&
    Number.isInteger(parsed.payload.year)
      ? parsed.payload.year
      : null
  const evidenceCount = Array.isArray(parsed.payload.evidence)
    ? parsed.payload.evidence.length
    : null
  const faacShock = finiteNumber(parsed.payload.faac_shock_pct)
  const igrShock = finiteNumber(parsed.payload.igr_shock_pct)
  const reserveShare = finiteNumber(parsed.payload.reserve_share_pct)
  const researchObjective =
    typeof parsed.payload.research_objective === 'string'
      ? parsed.payload.research_objective.trim().slice(0, 240)
      : ''
  const currentEvidenceCheck =
    stateSlug &&
    year !== null &&
    faacShock !== null &&
    igrShock !== null &&
    reserveShare !== null
      ? {
          fingerprint,
          stateSlug,
          year,
          faacShock,
          igrShock,
          reserveShare,
          researchObjective,
        }
      : null

  return {
    status: 'verified',
    fingerprint,
    stateName,
    year,
    evidenceCount,
    payload: parsed.payload,
    currentEvidenceCheck,
  }
}
