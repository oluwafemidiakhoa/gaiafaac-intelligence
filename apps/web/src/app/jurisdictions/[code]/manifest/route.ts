import { NextResponse } from 'next/server'

import { getJurisdictionFiscalState } from '@/lib/fiscal-ledger-api'

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ code: string }> },
) {
  const { code } = await params
  const result = await getJurisdictionFiscalState(code)
  if (!result.data) {
    return NextResponse.json(
      { error: 'Fiscal State not found.' },
      { status: 404 },
    )
  }
  return new NextResponse(
    `${JSON.stringify(result.data.evidence.manifest, null, 2)}\n`,
    {
      headers: {
        'Content-Disposition': `attachment; filename="${result.data.data.fiscal_state_id}.json"`,
        'Content-Type': 'application/json; charset=utf-8',
      },
    },
  )
}
