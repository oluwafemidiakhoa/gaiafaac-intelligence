import { NextResponse } from 'next/server'

import { oagfRevisionSourceApiUrl } from '@/lib/oagf-revision-api'

export const dynamic = 'force-dynamic'

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ caseId: string; version: string }> },
) {
  const { caseId, version } = await params
  if (version !== 'current' && version !== 'previous') {
    return NextResponse.json({ detail: 'Invalid revision version.' }, { status: 400 })
  }

  const response = await fetch(oagfRevisionSourceApiUrl(caseId, version), {
    cache: 'no-store',
    headers: { 'X-Admin-Key': process.env.ADMIN_KEY ?? '' },
  })
  if (!response.ok) {
    return NextResponse.json(
      { detail: 'Retained source bytes are unavailable.' },
      { status: response.status },
    )
  }

  const headers = new Headers()
  const contentType = response.headers.get('content-type')
  const disposition = response.headers.get('content-disposition')
  if (contentType) headers.set('content-type', contentType)
  if (disposition) headers.set('content-disposition', disposition)
  headers.set('cache-control', 'private, no-store')
  return new Response(await response.arrayBuffer(), { status: 200, headers })
}
