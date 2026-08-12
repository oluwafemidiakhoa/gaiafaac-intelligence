import { fiscalDesignBriefFingerprint } from '@/lib/fiscal-design-brief-integrity'
import { getFiscalDesign } from '@/lib/fiscal-design-api'
import type { CurrentEvidenceCheckRequest } from '@/lib/fiscal-design-manifest-verifier'

function validRequest(value: unknown): value is CurrentEvidenceCheckRequest {
  if (typeof value !== 'object' || value === null || Array.isArray(value)) {
    return false
  }

  const request = value as Record<string, unknown>
  return (
    typeof request.fingerprint === 'string' &&
    /^[a-f0-9]{64}$/.test(request.fingerprint) &&
    typeof request.stateSlug === 'string' &&
    Boolean(request.stateSlug.trim()) &&
    typeof request.year === 'number' &&
    Number.isInteger(request.year) &&
    request.year >= 2000 &&
    request.year <= 2100 &&
    typeof request.faacShock === 'number' &&
    Number.isFinite(request.faacShock) &&
    request.faacShock >= -100 &&
    request.faacShock <= 100 &&
    typeof request.igrShock === 'number' &&
    Number.isFinite(request.igrShock) &&
    request.igrShock >= -100 &&
    request.igrShock <= 100 &&
    typeof request.reserveShare === 'number' &&
    Number.isFinite(request.reserveShare) &&
    request.reserveShare >= 0 &&
    request.reserveShare <= 100 &&
    typeof request.researchObjective === 'string' &&
    request.researchObjective.length <= 240
  )
}

export async function POST(request: Request) {
  let body: unknown
  try {
    body = await request.json()
  } catch {
    return Response.json({ error: 'A valid JSON request is required.' }, { status: 400 })
  }

  if (!validRequest(body)) {
    return Response.json(
      { error: 'A valid verified-manifest comparison request is required.' },
      { status: 400 },
    )
  }

  const result = await getFiscalDesign(
    body.stateSlug.trim().toLowerCase(),
    body.year,
    body.faacShock,
    body.igrShock,
    body.reserveShare,
  )
  if (!result.data) {
    return Response.json(
      { error: result.error ?? 'Current governed fiscal evidence is unavailable.' },
      { status: 404 },
    )
  }

  const currentFingerprint = fiscalDesignBriefFingerprint(
    result.data,
    body.researchObjective,
  )

  return Response.json({
    status: currentFingerprint === body.fingerprint ? 'current' : 'superseded',
    manifest_fingerprint: body.fingerprint,
    current_fingerprint: currentFingerprint,
    state_name: result.data.state_name,
    year: result.data.year,
    coverage_label: result.data.coverage_label,
  })
}
