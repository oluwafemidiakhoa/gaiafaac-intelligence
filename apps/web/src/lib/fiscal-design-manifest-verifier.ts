export type ManifestVerification =
  | {
      status: 'verified'
      fingerprint: string
      stateName: string | null
      year: number | null
      evidenceCount: number | null
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

async function sha256Hex(value: string) {
  const digest = await globalThis.crypto.subtle.digest(
    'SHA-256',
    new TextEncoder().encode(value),
  )
  return Array.from(new Uint8Array(digest))
    .map((byte) => byte.toString(16).padStart(2, '0'))
    .join('')
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
  const year =
    typeof parsed.payload.year === 'number' &&
    Number.isInteger(parsed.payload.year)
      ? parsed.payload.year
      : null
  const evidenceCount = Array.isArray(parsed.payload.evidence)
    ? parsed.payload.evidence.length
    : null

  return {
    status: 'verified',
    fingerprint,
    stateName,
    year,
    evidenceCount,
  }
}
