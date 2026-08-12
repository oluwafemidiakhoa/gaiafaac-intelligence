import { fiscalDesignEvidenceManifest } from '@/lib/fiscal-design-brief-integrity'
import { getFiscalDesign } from '@/lib/fiscal-design-api'

function bounded(
  value: string | null,
  fallback: number,
  min: number,
  max: number,
) {
  const parsed = Number(value)
  return Number.isFinite(parsed) && parsed >= min && parsed <= max
    ? parsed
    : fallback
}

export async function GET(request: Request) {
  const url = new URL(request.url)
  const state = (url.searchParams.get('state') ?? '').trim().toLowerCase()
  const year = Math.trunc(
    bounded(
      url.searchParams.get('year'),
      new Date().getUTCFullYear(),
      2000,
      2100,
    ),
  )
  const faacShock = bounded(url.searchParams.get('faacShock'), -20, -100, 100)
  const igrShock = bounded(url.searchParams.get('igrShock'), 0, -100, 100)
  const reserveShare = bounded(url.searchParams.get('reserveShare'), 10, 0, 100)
  const researchObjective = (url.searchParams.get('objective') ?? '')
    .trim()
    .slice(0, 240)
  const expectedFingerprint = (
    url.searchParams.get('fingerprint') ?? ''
  ).toLowerCase()

  if (!state || !/^[a-f0-9]{64}$/.test(expectedFingerprint)) {
    return Response.json(
      { error: 'A state and valid brief fingerprint are required.' },
      { status: 400 },
    )
  }

  const result = await getFiscalDesign(
    state,
    year,
    faacShock,
    igrShock,
    reserveShare,
  )
  if (!result.data) {
    return Response.json(
      { error: result.error ?? 'No governed fiscal design is available.' },
      { status: 404 },
    )
  }

  const manifest = fiscalDesignEvidenceManifest(result.data, researchObjective)
  if (manifest.fingerprint !== expectedFingerprint) {
    return Response.json(
      {
        error:
          'The requested brief fingerprint no longer matches the governed scenario response.',
        expected_fingerprint: expectedFingerprint,
        current_fingerprint: manifest.fingerprint,
      },
      { status: 409 },
    )
  }

  const filename = `${result.data.state_slug}-${result.data.year}-fiscal-design-evidence.json`
  return new Response(`${JSON.stringify(manifest, null, 2)}\n`, {
    status: 200,
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
      'Content-Disposition': `attachment; filename="${filename}"`,
      'Cache-Control': 'no-store',
    },
  })
}
