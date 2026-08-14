import { NextResponse } from 'next/server'

import { getFiscalCertificate } from '@/lib/fiscal-ledger-api'

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ gaiaId: string }> },
) {
  const { gaiaId } = await params
  const result = await getFiscalCertificate(gaiaId)
  if (!result.data) {
    return NextResponse.json(
      { error: 'Fiscal Certificate not found.' },
      { status: 404 },
    )
  }
  return new NextResponse(
    `${JSON.stringify(result.data.evidence.manifest, null, 2)}\n`,
    {
      headers: {
        'Content-Disposition': `attachment; filename="${result.data.data.gaia_id}.json"`,
        'Content-Type': 'application/json; charset=utf-8',
      },
    },
  )
}
